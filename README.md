# Reconcile AI — AI Finance Controller

> **AI-assisted financial reconciliation with deterministic controls, selective AI reasoning, validation, auditability, and measurable performance.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-150458?logo=pandas)](https://pandas.pydata.org/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Reasoning-4285F4?logo=google)](https://ai.google.dev/)

---

## 📌 Overview

**Reconcile AI** is an AI-assisted finance reconciliation controller designed to process financial transactions across multiple source systems such as:

* Invoices
* Payments
* Settlements

The system combines **deterministic financial rules** with **selective AI reasoning**.

It does not send every transaction to an LLM.

Instead, the controller first performs reliable programmatic checks and only routes ambiguous financial exceptions to AI when contextual reasoning is useful.

The system also validates AI responses and safely routes unresolved cases to human review.

---

# 🎯 What the System Does

```text
Financial Sources
       │
       ▼
┌──────────────────┐
│ Data Ingestion   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Normalization    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Reconciliation   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Exception        │
│ Classification   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ AI Router        │
└───────┬──────────┘
        │
   ┌────┴───────────────┐
   │                    │
   ▼                    ▼
Deterministic        AI Required
Rules                Exceptions
   │                    │
   │                    ▼
   │              Gemini / Agent
   │                    │
   │                    ▼
   │              AI Validation
   │                    │
   └──────────┬─────────┘
              ▼
       Final Decision
              │
       ┌──────┴───────┐
       ▼              ▼
     Audit        Benchmark
       │              │
       └──────┬───────┘
              ▼
        Streamlit Dashboard
```

---

# ✨ Key Features

### 1. Multi-source reconciliation

Combines financial information from:

* Invoice data
* Payment data
* Settlement data

### 2. Deterministic financial controls

Reliable calculations and matching are performed using programmatic rules rather than AI.

Examples:

* Invoice vs payment comparison
* Settlement calculation validation
* Duplicate detection
* Fee difference detection
* Missing transaction detection
* Date mismatch detection

### 3. Selective AI routing

AI is used only when contextual reasoning can add value.

Typical AI-routed exceptions include:

* Payment missing
* Amount discrepancy
* Settlement missing
* Settlement discrepancy
* Settlement delay
* Date mismatch

Deterministic exceptions do not unnecessarily consume Gemini requests.

### 4. AI validation

LLM responses are treated as **untrusted external output**.

The system validates AI responses before accepting them.

Invalid or unsafe responses can be rejected and routed to recovery or human review.

### 5. Failure recovery

AI failure does not stop the entire financial batch.

The controller can handle:

* API failures
* Timeouts
* Invalid AI responses
* Missing evidence
* Data errors

When a transaction cannot be safely resolved:

```text
UNRESOLVED
     ↓
HUMAN_REVIEW
```

### 6. Auditability

The system produces audit-related outputs so decisions can be reviewed after processing.

The audit layer captures information such as:

```text
Transaction
    ↓
Exception
    ↓
AI Used?
    ↓
Decision
    ↓
Validation
    ↓
Recovery
```

### 7. Ground-truth evaluation

The controller can compare its results against a known ground-truth dataset.

```text
Ground Truth
      │
      ▼
Expected Outcome
      │
      │ compare
      ▼
Controller Result
      │
      ▼
Correct / Incorrect / Pending
```

### 8. Benchmarking

Benchmarking measures system performance without making additional Gemini requests.

Metrics include:

* Total records
* Evaluated records
* Correct results
* Incorrect results
* Pending results
* Accuracy
* Deterministic processing
* Rule-based processing
* AI processing
* Throughput

### 9. Interactive dashboard

A Streamlit dashboard provides visibility into:

* Reconciliation results
* Exception classifications
* AI routing
* Final decisions
* Metrics
* Benchmark results
* Audit reports
* Accuracy
* Throughput
* Human-review cases
* Unresolved transactions

---

# 🧠 AI Decision Strategy

The system follows a simple principle:

> **Use deterministic logic for deterministic problems. Use AI only where reasoning adds value.**

### Processing strategy

| Transaction type       | Processing              |
| ---------------------- | ----------------------- |
| Normal match           | Deterministic           |
| Duplicate              | Rule-based              |
| Fee difference         | Rule-based              |
| Settlement calculation | Rule-based              |
| Contextual exception   | AI                      |
| Missing critical data  | Human review            |
| AI failure             | Human review            |
| Invalid AI response    | Recovery / Human review |

This reduces unnecessary AI usage while keeping financial calculations deterministic.

---

# 🔐 Data Integrity

The controller follows four important principles.

### Never invent financial values

If financial evidence is missing or corrupted:

```text
DO NOT GUESS
DO NOT FABRICATE
DO NOT FORCE A RESULT
```

Instead:

```text
DATA_ERROR
    ↓
UNRESOLVED
    ↓
HUMAN_REVIEW
```

### Preserve exceptions

Failed transactions remain visible instead of silently disappearing.

### Continue processing

One bad transaction should not stop the remaining batch.

### Validate AI output

AI responses must pass validation before they can influence the final decision.

---

# 📁 Project Structure

```text
Reconcile-AI-AI-Finance-Controller/
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── invoices.csv
│   ├── payments.csv
│   ├── settlements.csv
│   ├── ground_truth.csv
│   │
│   ├── normalized_invoices.csv
│   ├── normalized_payments.csv
│   ├── normalized_settlements.csv
│   │
│   ├── reconciliation_results.csv
│   ├── classified_exceptions.csv
│   ├── ai_routing_results.csv
│   ├── final_results.csv
│   │
│   ├── metrics.csv
│   ├── audit_log.csv
│   ├── audit_report.csv
│   │
│   ├── benchmark.csv
│   └── benchmark_details.csv
│
├── prompts/
│   └── AI prompt templates
│
├── src/
│   ├── agent.py
│   ├── audit.py
│   ├── audit_report.py
│   ├── benchmark.py
│   ├── database.py
│   ├── decision_valider.py
│   ├── exception_classifier.py
│   ├── ingestion.py
│   ├── llm.py
│   ├── metrics.py
│   ├── normalize.py
│   ├── reconciliation.py
│   ├── router.py
│   └── validate.py
│
├── tests/
│
├── generate_data.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 🧩 Module Responsibilities

| Module                    | Responsibility                                |
| ------------------------- | --------------------------------------------- |
| `generate_data.py`        | Generates controlled synthetic financial data |
| `ingestion.py`            | Loads financial source data                   |
| `normalize.py`            | Standardizes source data                      |
| `reconciliation.py`       | Performs deterministic reconciliation         |
| `exception_classifier.py` | Categorizes reconciliation exceptions         |
| `router.py`               | Decides deterministic vs AI vs human review   |
| `agent.py`                | Coordinates AI transaction processing         |
| `llm.py`                  | Handles Gemini interaction                    |
| `decision_valider.py`     | Validates AI decisions                        |
| `validate.py`             | Performs validation checks                    |
| `database.py`             | Stores reconciliation results                 |
| `audit.py`                | Creates audit records                         |
| `audit_report.py`         | Produces audit reporting                      |
| `metrics.py`              | Calculates performance metrics                |
| `benchmark.py`            | Compares results against ground truth         |
| `dashboard/app.py`        | Streamlit visualization                       |

---

# ⚙️ Technology Stack

| Technology      | Purpose                                   |
| --------------- | ----------------------------------------- |
| Python          | Core application                          |
| Pandas          | Financial data processing                 |
| SQLite          | Local persistence                         |
| Google Gemini   | AI exception reasoning                    |
| `google-genai`  | Gemini API integration                    |
| Streamlit       | Interactive dashboard                     |
| `python-dotenv` | Environment configuration                 |
| CSV             | Financial datasets and evaluation outputs |

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/gokulpandian-05/Reconcile-AI-AI-Finance-Controller.git
cd Reconcile-AI-AI-Finance-Controller
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Gemini

Create a local `.env` file in the project root.

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.7-flash
```

Never commit `.env`.

The repository intentionally contains:

```text
.env.example
```

instead of real credentials.

---

# ▶️ Running the Project

Always run commands from the **project root**.

```text
Reconcile-AI-AI-Finance-Controller/
```

## Generate synthetic data

```bash
python generate_data.py
```

This creates the controlled financial datasets used by the reconciliation workflow.

---

# 🔄 Processing Workflow

The complete controller workflow is:

```text
1. Generate Data
       ↓
2. Ingestion
       ↓
3. Normalization
       ↓
4. Reconciliation
       ↓
5. Exception Classification
       ↓
6. AI Routing
       ↓
7. AI Agent / Gemini
       ↓
8. Decision Validation
       ↓
9. Database / Audit
       ↓
10. Benchmark
       ↓
11. Dashboard
```

Each stage produces structured outputs that are consumed by the next stage.

---

# 🤖 AI Processing

AI is not used for basic arithmetic or straightforward matching.

For AI-required transactions:

```text
Transaction
    ↓
Router
    ↓
Agent
    ↓
Gemini
    ↓
Structured AI Response
    ↓
Validation
    ↓
Accepted / Rejected
```

The AI is primarily responsible for **interpreting contextual exceptions and generating explanations**.

It does not directly modify the underlying financial source records.

---

# 🛡️ Failure Recovery

A failed AI request must not become a successful financial decision.

Example:

```text
Transaction
     ↓
Gemini Request
     ↓
API Failure / Timeout
     ↓
Recovery
     ↓
Insufficient Evidence
     ↓
UNRESOLVED
     ↓
HUMAN_REVIEW
```

Invalid AI responses are also rejected.

For example:

```text
confidence = 1.7
```

is invalid when confidence must remain within the expected range.

The transaction can therefore be routed to:

```text
UNRESOLVED / HUMAN_REVIEW
```

---

# 📊 Dashboard

Start the Streamlit dashboard:

```bash
streamlit run dashboard/app.py
```

Then open:

```text
http://localhost:8501
```

The dashboard provides operational and evaluation visibility across the processed batch.

---

# 📈 Benchmarking

Benchmarking compares controller results against the project's ground-truth dataset.

```text
Ground Truth
     │
     ▼
Controller Results
     │
     ▼
Evaluation
     │
 ┌───┼───────────────┐
 ▼   ▼               ▼
Correct  Incorrect  Pending
     │
     ▼
 Accuracy
     +
 Throughput
```

An important design decision is that benchmarking **does not call Gemini**.

This keeps evaluation independent from additional AI requests.

---

# 🧪 Testing

The project is designed around controlled financial exceptions.

Example scenarios include:

* Amount mismatch
* Missing payment
* Missing settlement
* Duplicate transaction
* Date mismatch
* Fee difference
* Invalid financial values
* Missing transaction IDs
* AI API failure
* Invalid AI response

The objective is not simply to demonstrate a successful transaction.

The objective is to demonstrate that the controller can process **normal, exceptional, invalid, and failed cases without collapsing the entire batch**.

---

# 🏆 Evaluation Philosophy

Reconcile AI focuses on four dimensions:

```text
                 Reconcile AI
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Financial      AI Judgment    Reliability
    Accuracy
        │             │             │
        └─────────────┼─────────────┘
                      ▼
               Measured Results
                      │
             ┌────────┴────────┐
             ▼                 ▼
          Accuracy         Throughput
             │                 │
             └────────┬────────┘
                      ▼
              Honest Exceptions
```

The system therefore evaluates:

* Why AI was used
* When AI was not used
* AI decision quality
* Failure behavior
* Accuracy
* Throughput
* Unresolved cases
* Auditability

---

# 💡 Design Principles

### 1. Deterministic first

Use reliable programmatic rules wherever possible.

### 2. AI only when useful

Use LLM reasoning for contextual exceptions rather than routine calculations.

### 3. Never blindly trust AI

AI output must be validated.

### 4. Fail safely

An unresolved financial transaction is preferable to an unsupported financial decision.

```text
Correctly unresolved
        >
Confidently incorrect
```

---

# 🔒 Security

Never commit:

```text
.env
API keys
Passwords
Private credentials
Local secrets
```

The repository uses:

```text
.env.example
```

for environment configuration.

Generated Python cache files and local databases should also remain outside version control.

---

# 📦 Repository Outputs

The project generates several categories of outputs.

### Source data

```text
invoices.csv
payments.csv
settlements.csv
ground_truth.csv
```

### Reconciliation

```text
reconciliation_results.csv
classified_exceptions.csv
```

### AI processing

```text
ai_routing_results.csv
final_results.csv
```

### Metrics

```text
metrics.csv
benchmark.csv
benchmark_details.csv
```

### Audit

```text
audit_log.csv
audit_report.csv
```

---

# 📋 Example Exception Categories

The controller can distinguish between different classes of financial exceptions, including:

```text
PAYMENT_MISSING
AMOUNT_DISCREPANCY
SETTLEMENT_MISSING
SETTLEMENT_AMOUNT_DISCREPANCY
SETTLEMENT_DELAY
DATE_MISMATCH
DUPLICATE_TRANSACTION
FEE_DIFFERENCE
SETTLEMENT_CALCULATION
```

The routing decision determines whether each case should be processed deterministically, with AI reasoning, or through human review.

---

# 🌟 Why This Project Is Different

Traditional reconciliation automation often focuses only on producing a final result.

Reconcile AI focuses on **how the result was produced and whether that result can be trusted**.

The system therefore makes the following distinctions explicit:

```text
Deterministic decision
        vs
Rule-based decision
        vs
AI-assisted decision
        vs
Human review
```

This makes the controller easier to evaluate, audit, and improve.

---

# ⚠️ Disclaimer

This project uses **synthetic financial data** for demonstration, development, and evaluation.

It is not intended to provide financial advice or replace:

* Production accounting systems
* Financial controls
* Compliance processes
* Professional accounting review
* Human oversight

---

# 👤 Project

**Reconcile AI — AI Finance Controller**

**Purpose:** AI-assisted financial reconciliation and exception operations.

**Primary focus:** Multi-source reconciliation with selective AI reasoning, safe failure recovery, measurable performance, and auditability.

---

## 📌 Project Status

The repository currently contains the core components required for:

* Synthetic data generation
* Financial source processing
* Normalization
* Deterministic reconciliation
* Exception classification
* AI routing
* Gemini integration
* AI validation
* Agent workflow
* Audit logging
* Benchmarking
* Ground-truth evaluation
* Metrics generation
* Streamlit dashboard

---

## 📄 License

Add an appropriate open-source license to the repository before distributing the project publicly.
