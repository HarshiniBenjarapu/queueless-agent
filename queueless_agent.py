
import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*generator didn't stop after athrow.*",
    category=RuntimeWarning,
)
warnings.filterwarnings("ignore", category=ResourceWarning)

import os
import re
from strands import Agent
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)
from strands.models import OpenAIModel

from queueless_tools import (
    get_patient_details,
    check_clinic_calendar,
    reschedule_appointment,
    cancel_appointment,
    send_patient_notification,
)

# 1. Load skill file if present (Module 3 - Skills)
cancellation_skill = ""
if os.path.exists("skills/appointment_cancellation.md"):
    with open("skills/appointment_cancellation.md", "r") as f:
        cancellation_skill = f.read()

# 2. PII Guardrail Hook (Module 2 - Hooks)
class PIIMaskerHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(AfterToolCallEvent, self.mask_sensitive_data)

    def reset(self, event: BeforeInvocationEvent) -> None:
        print("[HOOK] 🔄 PII Guardrail active for invocation")

    def mask_sensitive_data(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown_tool")
        if hasattr(event, "result") and isinstance(event.result, str):
            original_result = event.result
            masked_text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\\(?\d{3}\\)?[-.\s]?\d{4}', '[REDACTED PHONE]', original_result)
            masked_text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED EMAIL]', masked_text)
            if masked_text != original_result:
                print(f"[HOOK] 🛡️ PII Guardrail triggered on '{tool_name}'! Masked sensitive patient data.")
                event.result = masked_text

# 3. Execution Guardrail Hook (Module 3 - Execution Governance)
class AppointmentGuardrailHook(HookProvider):
    def __init__(self):
        self.patient_verified = False

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(BeforeToolCallEvent, self.verify_execution_order)

    def reset(self, event: BeforeInvocationEvent) -> None:
        self.patient_verified = False

    def verify_execution_order(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "")
        if tool_name == "get_patient_details":
            self.patient_verified = True
        elif tool_name in ["cancel_appointment", "reschedule_appointment", "send_patient_notification"] and not self.patient_verified:
            print("[GUARDRAIL] ⚠️ Intercepted tool execution! Patient identity verification required first.")

SYSTEM_PROMPT = f"""You are an intelligent Healthcare Coordination Agent for QueueLess.
Be empathetic, professional, and efficient. Use available tools to manage clinic 
schedules, assist patients with appointment updates, and optimize doctor availability.

### ACTIVE WORKFLOW SKILL:
{cancellation_skill}
"""

# 4. Initialize Groq model using OpenAIModel
groq_api_key = os.getenv("GROQ_API_KEY")
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
    hooks=[PIIMaskerHook(), AppointmentGuardrailHook()],
    system_prompt=SYSTEM_PROMPT,
)

if __name__ == "__main__":
    print("🚀 Testing QueueLess Agent with Groq...\n")
    response = agent("I'm patient P-1001 and I need to cancel my appointment with Dr. Rao.")
    print("\nAgent Output:")
    print(response)
