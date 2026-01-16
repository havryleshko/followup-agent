# System Design Document

## Project: Context-Aware Follow-Up Recommendations for Overdue Invoices

## Document Format & Rationale

## 1. Purpose

Problem: **Inconsistent Follow-Ups on Overdue Customer Payments**
MVP: **A tool that takes a list of overdue invoices and outputs context-aware, correctly timed follow-up messages with escalation logic — delivered manually or semi-manually.**
Explanation: **Businesses lose liquidity when they fail to systematically remind clients of late payments, leading to prolonged cash gaps.**

The system is designed as a **human-in-the-loop AI tool** that produces judgment, not autonomous actions.

---

## 2. Goals and Non-Goals

### Goals
- Generate correct follow-up timing recommendations
- Select appropriate tone based on customer context
- Produce business-safe follow-up drafts
- Run locally with minimal cost
- Be auditable and explainable

### Non-Goals
- Automatic email sending
- End-to-end invoicing or accounting
- Real-time processing
- High-availability or production-scale infrastructure
- Legal or compliance enforcement

---

## 3. High-Level Architecture

### Conceptual Flow

```
Invoice Data → Context Extraction → Decision Logic → Message Generation → Control Agent → Output Artifact
```

### Execution Characteristics
- Stateless execution
- One-off runs
- Local CLI execution
- Human review required before use

---

## 4. Input Data Design

### Supported Inputs (v0)
- CSV or Excel files

### Required Fields
- Client name
- Invoice amount
- Invoice issue date
- Days overdue
- Last follow-up date
- Relationship tag (new / recurring / VIP / risky)
- Notes

### Assumptions
- Input data is accurate
- User is responsible for data legality and consent

---

## 5. Agent Architecture

The system is implemented using a **multi-agent LangGraph orchestration**.

### Agent 1: Invoice Context Agent

**Responsibility:**
- Normalize invoice data
- Infer payment risk level
- Summarize invoice state

**Inputs:**
- Raw invoice row

**Outputs:**
- Structured context object

---

### Agent 2: Follow-Up Decision Agent

**Responsibility:**
- Decide whether a follow-up is required
- Determine urgency and tone

**Decision Factors:**
- Days overdue
- Invoice amount
- Relationship context
- Prior follow-ups

**Constraints:**
- No threatening language
- No legal claims

---

### Agent 3: Message Generation Agent

**Responsibility:**
- Generate concise, professional follow-up drafts
- Maintain business-appropriate tone

**Outputs:**
- Email body
- Optional subject line
- Short explanation of reasoning

---

## 6. Prompt & Context Engineering Strategy

- Agents operate on structured inputs and outputs
- Prompts are scoped to a single responsibility
- Conservative defaults are applied
- Explanations are generated alongside outputs

**Rationale:**
Separating reasoning, decision-making, and generation improves reliability and debuggability.

---

## 7. Execution Model (CLI-First)

### Execution
- System is run via CLI by the operator
- Example:

```
python run_followups.py invoices.csv
```

### Output
- Markdown or text report
- One recommendation per invoice

### Rationale
- Zero infrastructure cost
- High trust through manual review
- Fast iteration and validation

---

## 8. Failure Modes & Mitigations

### Potential Failures
- Incorrect tone recommendation
- Missing invoice context
- LLM hallucination

### Mitigations
- Human review before use
- Conservative language defaults
- Explanatory outputs

---

## 9. Security & Privacy Considerations

- No data persistence
- No third-party data sharing
- Local execution only
- Users control all data inputs

---

## 10. Evolution Path (Conditional)

### If Validated
- Lightweight UI wrapper
- Scheduling support
- Read-only accounting integrations

### If Not Validated
- Archive repository as reference implementation

---

## 11. Summary

This system is intentionally small, auditable, and human-centered.

Its primary purpose is to validate whether **AI-assisted judgment** can meaningfully improve follow-up behavior in small businesses.

Complete visual architecture (single-run, human-in-the-loop)

┌──────────────────────────────────────────────┐
│                  OPERATOR                    │
│        (You / CLI Invocation / Script)       │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│               INPUT INTERFACE                 │
│  - CSV / Excel / JSON                         │
│  - Overdue invoices                           │
│  - No LLM here                                │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│              SHARED STATE OBJECT              │
│  (Immutable per step, append-only)            │
│                                              │
│  state = {                                    │
│    invoice_data                               │
│    context                                    │
│    decision                                   │
│    message                                    │
│  }                                           │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│               CONTEXT AGENT                   │
│                                              │
│  Code + Prompt + (Optional) LLM               │
│                                              │
│  Responsibilities:                            │
│  - Normalize invoice data                     │
│  - Infer payment risk                         │
│  - Summarize relationship context             │
│                                              │
│  Writes → state.context                       │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│               DECISION AGENT                  │
│                                              │
│  Rules + Prompt + LLM                         │
│                                              │
│  Responsibilities:                            │
│  - Follow-up required?                        │
│  - Timing (now / wait)                        │
│  - Tone (soft / neutral / firm)               │
│                                              │
│  Writes → state.decision                      │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│               MESSAGE AGENT                   │
│                                              │
│  Prompt + LLM                                 │
│                                              │
│  Responsibilities:                            │
│  - Draft follow-up message                    │
│  - Generate subject line                      │
│  - Explain reasoning                          │
│                                              │
│  Writes → state.message                       │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│              OUTPUT ARTIFACT                  │
│                                              │
│  - Markdown / Text / PDF                      │
│  - One recommendation per invoice             │
│  - Human-readable                             │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│              HUMAN REVIEW                     │
│                                              │
│  - Read output                                │
│  - Decide to send or not                      │
│  - Manual follow-up                           │
└──────────────────────────────────────────────┘

Where LLM is:
Context Agent   → optional LLM
Decision Agent  → LLM (plus rules)
Message Agent   → LLM (primary)

## Repo structure:

followup-judgment-agent/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── data/
│   ├── samples/
│   │   └── invoices_sample.csv
│   └── schemas/
│       └── invoice_schema.json
│
├── src/
│   ├── main.py                # CLI entrypoint
│   │
│   ├── config/
│   │   ├── settings.py        # model choice, thresholds
│   │   └── prompts.py         # all prompts live here
│   │
│   ├── state/
│   │   └── state.py           # Typed LangGraph state
│   │
│   ├── agents/
│   │   ├── context_agent.py
│   │   ├── decision_agent.py
│   │   └── message_agent.py
│   │
│   ├── graph/
│   │   └── workflow.py        # LangGraph definition
│   │
│   ├── io/
│   │   ├── loader.py          # CSV / Excel
│   │   └── writer.py          # Markdown / Text output
│   │
│   └── utils/
│       └── validation.py
│
├── outputs/
│   └── example_output.md
│
└── tests/
    └── test_decision_logic.py

