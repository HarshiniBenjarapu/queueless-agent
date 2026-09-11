
import warnings

warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=r".*generator didn't stop after athrow.*",
)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=r".*reasoningContent.*")

import os
import re

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

