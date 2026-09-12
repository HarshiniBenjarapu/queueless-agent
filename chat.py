
import sys
import warnings
import logging

warnings.filterwarnings("ignore")

# Drop the provider-side logger warning that is emitted when
# persisted reasoningContent / reasoningText content blocks are inspected
# by the installed strands.models.openai formatter during multi-turn
# request assembly. This lives above the Strands/OpenAI import path.
logging.getLogger("strands.models.openai").setLevel(logging.CRITICAL + 10)
logging.getLogger("strands.models.openai").propagate = False
logging.getLogger("strands.models.openai").disabled = True


def _suppress_httpcore2_async_cleanup(unraisable):
    """Drop Python 3.14 httpcore2 async-generator shutdown noise.

    A known Python 3.14 + httpcore2 cleanup pattern emits a
    RuntimeError: generator didn't stop after athrow() and GeneratorExit
    traces through sys.unraisablehook while an async generator is being
    closed during response streaming. These reports are cosmetic, so we
    silence specifically that async cleanup signature and hand off any
    other unraisable object through the normal interpreter hook.
    """
    exc_type = getattr(unraisable, "exc_type", None)
    exc_value = getattr(unraisable, "exc_value", None)
    err_msg = getattr(unraisable, "err_msg", "") or ""

    message = ""
    if exc_type is not None:
        message += f"{exc_type.__name__}: "
    if exc_value is not None:
        message += str(exc_value)
    if err_msg:
        message += f" {err_msg}"

    lowered = message.lower()
    if (
        "generator didn't stop after athrow" in lowered
        or "generatorexit" in lowered
        or "asyncgen" in lowered
        or "httpcore2" in lowered
    ):
        return

    sys.__unraisablehook__(unraisable)


sys.unraisablehook = _suppress_httpcore2_async_cleanup

import json
import os
import re
from pathlib import Path

"""Interactive multi-turn terminal chat for QueueLess Healthcare Agent using Groq."""

from strands import Agent
from strands.models import OpenAIModel
from strands.session import FileSessionManager

from queueless_tools import (
    get_patient_details,
    check_clinic_calendar,
    reschedule_appointment,
    cancel_appointment,
    send_patient_notification,
)


def _strip_reasoning_keys(payload):
    """Recursively remove persisted reasoning keys from a nested payload structure."""
    if isinstance(payload, dict):
        cleaned = {}
        for key, value in payload.items():
            if key in {"reasoningContent", "reasoning_content", "reasoningText"}:
                continue
            cleaned[key] = _strip_reasoning_keys(value)
        return cleaned

    if isinstance(payload, list):
        return [_strip_reasoning_keys(item) for item in payload]

    return payload


def _sanitize_content_list(blocks):
    """Return a block list where empty or unsupported reasoning wrappers are dropped."""
    safe_blocks = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        if not block:
            continue

        plain = _strip_reasoning_keys(block)
        if not plain:
            continue

        known_keys = {
            "text",
            "image",
            "document",
            "toolResult",
            "toolUse",
            "cachePoint",
            "guardContent",
            "citationsContent",
        }
        if not any(key in plain for key in known_keys):
            continue

        if isinstance(plain.get("text"), str) and plain.get("text") == "":
            continue

        safe_blocks.append(plain)

    return safe_blocks


def _sanitize_session_history(session_id):
    """Rewrite stored agent message files so legacy reasoning blocks never hydrate again."""
    base = Path(".sessions") / f"session_{session_id}"
    agent_dir = base / "agents" / "agent_queue_less_agent" / "messages"
    if not agent_dir.exists():
        return

    for file_path in agent_dir.glob("message_*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        msg = data.get("message", {})
        content = msg.get("content")
        if isinstance(content, list):
            clean_content = _sanitize_content_list(content)
            msg["content"] = clean_content
            data["message"] = msg
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class CleanStreamCallbackHandler:
    """Print only final user-visible text and suppress model reasoning traces."""

    def __call__(self, **kwargs):
        reasoning_text = kwargs.get("reasoningText", False)
        if reasoning_text:
            return

        data = kwargs.get("data", "")
        if not isinstance(data, str):
            data = str(data)

        if not data:
            return

        complete = kwargs.get("complete", False)
        print(data, end="" if not complete else "\n")

SYSTEM_PROMPT = """You are an intelligent Healthcare Coordination Agent for QueueLess.
Be empathetic, professional, and efficient. Use available tools to manage clinic 
schedules, assist patients with appointment updates, and optimize doctor availability."""

def main():
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY environment variable is not set!")
        print("Run: export GROQ_API_KEY='your_actual_groq_api_key'")
        return

    # Session persistence for Module 4: accept a session id from the user
    # or default to the patient example-style suffix.
    default_session_id = os.getenv("QUEUELESS_SESSION_ID", "p-1001_session")
    requested_session_id = input(f"Session ID [{default_session_id}]: ").strip()
    raw_session_id = requested_session_id or default_session_id

    # Normalize the raw user input to a repository-safe, case-insensitive,
    # equivalent session identifier so the same patient is resumed from the
    # same .sessions/session_* folder across process restarts.
    normalized = raw_session_id.strip().lower()
    normalized = normalized.replace("_session", "")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    session_id = normalized

    # Clean any stale multi-turn reasoning blocks out of the stored session files.
    _sanitize_session_history(session_id)

    # Verified Strands API: FileSessionManager(session_id, storage_dir=".sessions")
    session_manager = FileSessionManager(session_id=session_id, storage_dir=".sessions")

    # Keep the same agent identity across process restarts so a FileSessionManager can
    # restore the same agent from the same session directory.
    agent_id = os.getenv("QUEUELESS_AGENT_ID", "queue_less_agent")

    # Use a currently visible Groq default model string while still allowing GROQ_MODEL_ID override.
    model_id = os.getenv("GROQ_MODEL_ID", "openai/gpt-oss-20b")

    model = OpenAIModel(
        client_args={
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": groq_api_key,
        },
        model_id=model_id,
        stream=False,
    )

    agent = Agent(
        model=model,
        tools=[
            get_patient_details,
            check_clinic_calendar,
            reschedule_appointment,
            cancel_appointment,
            send_patient_notification,
        ],
        system_prompt=SYSTEM_PROMPT,
        session_manager=session_manager,
        agent_id=agent_id,
        callback_handler=CleanStreamCallbackHandler(),
    )

    print("🏥 QueueLess Healthcare Agent (Groq Powered Chat)")
    print("Type 'quit', 'exit', or 'q' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break
        if not user_input:
            continue

        print("\nAgent: ", end="")
        agent(user_input)
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()

