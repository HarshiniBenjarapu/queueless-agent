```
 QueueLess Agent 🏥🤖


Demo Video : https://youtu.be/yFDYUXMYVzE

**QueueLess Agent** is a deterministic, production-ready AI healthcare assistant built for the **Devpost Agents for Humans Hackathon** [1]. Powered by the open-source **AWS Strands SDK** [2] and **Groq** (Llama 3 API) for ultra-fast inference [3, 4], QueueLess Agent handles patient scheduling, appointment lookups, and cancellations while strictly enforcing policy verification and privacy controls [5].

---

## 🌟 Key Features &amp; Architecture

QueueLess Agent leverages the core primitives of the AWS Strands SDK to guarantee runtime governance and deterministic behavior [2, 5]:

* **Deterministic Tool Calling:** Uses `@tool` decorators to query patient data and clinic schedules safely without hallucinating or making assumptions [6, 7].
* **Strands Skills Plugin:** Enforces structured Markdown checklists (`skills/appointment_cancellation.md`), guiding the agent through step-by-step verification before executing high-stakes actions [8, 9].
* **Strands Hooks &amp; Guardrails:** Intercepts execution loops to automatically redact sensitive PII (phone numbers, emails) from logs and enforce tool rate-limiting [10-12].
* **Session Persistence:** Retains multi-turn conversation context across CLI restarts so patients don't have to re-verify preferences [13].
* **High-Speed Inference:** Powered by Groq for low-latency multi-turn chat responses.

---

## 🏗️ System Architecture 

```

User Terminal (chat.py) │ ▼ AWS Strands SDK Agent Loop ─────────► Strands Hooks (PII Redaction &amp; Guardrails) │ ─────────► Strands Skills (Cancellation Checklist) ├──► Groq Llama 3 API (Inference Engine) └──► Custom Tools (@tool Decorators)

```

---

## 🛠️ Project Structure

```text
queueless-agent/
├── chat.py                         # Main interactive CLI chat loop
├── queueless_agent.py              # Strands agent initialization &amp; logic
├── tools/                          # Custom tool definitions
├── skills/                         # Strands Skills Markdown checklists
│   └── appointment_cancellation.md
├── queueless-agent-architecture.png # Architecture diagram
├── requirements.txt                # Python dependencies
└── README.md                       # Documentation

```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.10+** (Python 3.14 compatible)
* **Groq API Key**

### 1\. Clone the Repository

```
git clone https://github.com/HarshiniBenjarapu/queueless-agent.git
cd queueless-agent

```

### 2\. Set Up Virtual Environment &amp; Dependencies

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

### 3\. Set API Key

```
export GROQ_API_KEY="your-groq-api-key"

```

### 4\. Launch the Agent

```
python chat.py

```

---

## 💬 Example Terminal Session

```
Session ID [p-1001_session]: p-1001
🏥 QueueLess Healthcare Agent (Groq Powered Chat)

You: hi, im patient p-1001, look up my appointment details

Agent: I’ve retrieved your account details (morning preference)! To pull up your exact slot, please share:
- The doctor’s name you are scheduled with, OR
- Your 6- or 7-digit appointment ID.

You: i need to cancel my appointment

Agent: I’m ready to process your cancellation. To ensure I cancel the right slot, please confirm your doctor’s name or appointment ID.

```

---

## 🏆 Hackathon Submission

* **Event:** Devpost Agents for Humans Hackathon[1]
* **Track:** Professional Agents
* **Harness:** [AWS Strands SDK](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Fgithub.com%2Faws%2Fstrands-agents-sdk)[2]
* **Inference:** Groq Llama 3