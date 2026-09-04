# ReconcileAI — AI Finance Controller

> **An AI-powered finance operations controller for multi-source reconciliation, exception reasoning, safe failure recovery, and audit-ready financial decisions.**

ReconcileAI is a Python-based finance automation project for reconciling **invoices, payments, and settlements** across multiple financial sources.

The project deliberately combines **deterministic financial logic** with **selective AI reasoning**:

- Deterministic Python rules handle routine reconciliation and financial comparisons.
- Exceptions are classified before AI is used.
- Gemini is used only for cases where contextual reasoning can add value.
- AI responses are validated before they are accepted.
- Failed or invalid AI responses are handled through retry/fallback logic.
- Cases that cannot be safely resolved remain **UNRESOLVED** for human review.
- Results can be benchmarked against a controlled ground-truth dataset and reviewed through audit outputs and a Streamlit dashboard.

The core principle is simple:

> **Use AI where reasoning adds value, but keep financial calculations, validation, and reconciliation deterministic and auditable.**

---

## 🚀 Key Features

- Multi-source invoice, payment, and settlement reconciliation
- Synthetic financial dataset generation
- Controlled ground-truth evaluation
- Deterministic financial matching and comparison
- Exception classification
- Selective AI routing
- Gemini-powered exception explanations
- AI response validation
- Retry and failure recovery
- Deterministic fallback handling
- Unresolved / human-review workflow
- Audit logging and audit reporting
- Benchmarking and accuracy evaluation
- Metrics generation
- Streamlit dashboard
- Controlled AI request usage

---

## 🏗️ Architecture

```text
Synthetic Financial Data
          │
          ▼
      Ingestion
          │
          ▼
    Normalization
          │
          ▼
Deterministic Reconciliation
          │
          ▼
Exception Classification
          │
     ┌────┴────┐
     │         │
  Routine   Ambiguous
   Cases      Cases
     │         │
     ▼         ▼
Deterministic AI Router
   Rules        │
                ▼
             Gemini
                │
                ▼
       Response Validation
          │           │
        Valid       Failure
          │           │
          ▼           ▼
     AI Decision   Retry/Fallback
                      │
                      ▼
             UNRESOLVED / HUMAN REVIEW
                      │
                      ▼
                Final Results
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Audit      Benchmark    Dashboard
        Trail    & Ground Truth  Evidence
```

---

## 💡 Why AI Is Used Selectively

Not every financial exception needs an LLM.

For example:

```text
Invoice Amount = ₹10,000
Payment Amount = ₹10,000
Difference     = ₹0
```

A straightforward comparison should be handled by deterministic code rather than consuming an AI request.

The controller therefore separates cases into categories such as:

```text
Transaction
    │
    ▼
Exception Classification
    │
    ├── NO_AI
    │
    ├── RULE_BASED
    │
    └── AI_REQUIRED
             │
             ▼
          Gemini
```

This approach reduces unnecessary AI usage while keeping core financial decisions explainable.

---

## 📊 Synthetic Dataset

The project includes a controlled synthetic dataset generator.

The documented test dataset contains:

- **70 total transactions**
- **58 normal records**
- **12 intentional exception scenarios**

### Exception scenarios

| Exception | Count |
|---|---:|
| Amount mismatch | 3 |
| Missing settlement | 3 |
| Missing payment | 2 |
| Duplicate transaction | 1 |
| Date mismatch | 1 |
| Fee difference | 2 |
| **Total exceptions** | **12** |

The generator uses a fixed random seed for reproducibility:

```python
random.seed(42)
```

The controlled dataset is also designed to limit the number of potential AI-required cases so that Gemini usage stays within the intended request budget.

---

## 🧠 AI Routing

The AI router determines which exceptions should receive AI reasoning.

Conceptually:

```text
Exception
    │
    ▼
Classification
    │
    ├── NO_AI
    │
    ├── RULE_BASED
    │
    └── AI_REQUIRED
             │
             ▼
           Gemini
```

The important design decision is that **the entire dataset is not automatically sent to an LLM**.

AI is reserved for ambiguous cases where contextual interpretation can provide additional value.

---

## 🤖 AI Exception Explanation

For an `AI_REQUIRED` exception, relevant transaction context can be passed to Gemini.

The AI is expected to provide a structured explanation rather than directly modifying financial records.

AI output is then validated by the controller before it is accepted.

> **AI can explain a financial exception, but it should not be trusted blindly.**

---

## 🛡️ Failure Recovery

Failure recovery is part of the controller's core workflow.

For example, if a Gemini request times out:

```text
Transaction
    │
    ▼
Gemini Request
    │
    ▼
API Timeout
    │
    ▼
Retry
    │
    ├── Success ──► Continue
    │
    └── Failed
          │
          ▼
 Deterministic Fallback
          │
          ▼
 Insufficient Evidence?
          │
          ▼
     UNRESOLVED
```

One failed AI request should not terminate processing for the entire batch.

### Invalid AI responses

AI output is validated before acceptance.

For example, a confidence value such as:

```text
confidence = 1.7
```

should be rejected when the expected range does not allow it.

The controller can then fall back to:

```text
Invalid AI Output
        │
        ▼
      Reject
        │
        ▼
     Fallback
        │
        ▼
UNRESOLVED / HUMAN REVIEW
```

For financial automation, an unresolved case is preferable to an unsupported or fabricated financial answer.

---

## 🔐 Data Integrity Principles

### 1. Never invent financial values

If a required financial value is missing or corrupted:

```text
Do NOT calculate
Do NOT guess
Do NOT fabricate
```

Instead:

```text
DATA_ERROR
    │
    ▼
UNRESOLVED
    │
    ▼
HUMAN REVIEW
```

### 2. Preserve exceptions

Failed or invalid records should remain visible in the final exception results.

### 3. Continue the batch

A single problematic transaction should not stop processing of the remaining transactions.

### 4. Validate AI output

LLM responses are treated as untrusted external output and must pass validation before acceptance.

---

## 📁 Project Structure

```text
AI Finance Controller/
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── invoices.csv
│   ├── payments.csv
│   ├── settlements.csv
│   ├── ground_truth.csv
│   ├── reconciliation_results.csv
│   ├── classified_exceptions.csv
│   ├── ai_routing_results.csv
│   ├── final_results.csv
│   ├── metrics.csv
│   ├── audit_log.csv
│   ├── audit_report.csv
│   ├── benchmark.csv
│   └── benchmark_details.csv
│
├── prompts/
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

Generated files such as Python cache files, local databases, and environment secrets should remain outside version control.

---

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| Pandas | Financial data processing |
| SQLite | Local persistence / audit data |
| Google Gemini | AI exception reasoning |
| `google-genai` | Gemini API integration |
| Streamlit | Interactive dashboard |
| `python-dotenv` | Environment configuration |
| CSV | Financial datasets and evaluation outputs |

---

## 🔑 Environment Configuration

The project uses a Gemini API key through an environment variable.

Create a local `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.7-flash
```

The repository includes `.env.example` as a safe template.

**Never commit your real `.env` file or API key to GitHub.**

The `.gitignore` should keep environment secrets and generated local artifacts out of version control.

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ReconcileAI-AI-Finance-Controller.git
cd ReconcileAI-AI-Finance-Controller
```

Replace `YOUR_USERNAME` and the repository name with your actual GitHub repository.

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.7-flash
```

---

## ▶️ Running the Project

### Generate synthetic financial data

From the project root:

```bash
python generate_data.py
```

This generates the synthetic invoice, payment, settlement, and ground-truth datasets under:

```text
data/
```

### Run the reconciliation workflow

The project separates processing into modules for:

1. Ingestion
2. Normalization
3. Reconciliation
4. Exception classification
5. AI routing
6. AI explanation
7. Validation
8. Audit logging
9. Benchmarking

The overall workflow is:

```text
Generate Data
     ↓
Ingestion
     ↓
Normalization
     ↓
Reconciliation
     ↓
Exception Classification
     ↓
AI Routing
     ↓
AI Explanation
     ↓
Validation
     ↓
Audit
     ↓
Benchmark
```

Run the relevant modules according to the workflow implemented in the repository.

---

## 📊 Streamlit Dashboard

The project includes an interactive Streamlit dashboard.

Run:

```bash
streamlit run dashboard/app.py
```

The dashboard provides visibility into the project's operational and evaluation evidence, including:

- Final reconciliation results
- Metrics
- Benchmark results
- Benchmark details
- Audit report
- Deterministic processing
- Rule-based processing
- AI reasoning
- Throughput
- Accuracy
- Pending / unresolved cases

---

## 📈 Benchmarking

The benchmark module evaluates controller results against the ground-truth dataset.

A key design choice is:

> **Benchmarking does not call Gemini.**

This means evaluation can measure already-produced controller results without consuming additional AI requests.

The benchmark can track:

- Ground-truth records
- Controller/database result records
- Evaluated records
- Pending records
- Correct records
- Incorrect records
- Accuracy
- Deterministic processing
- Rule-based processing
- AI reasoning

---

## 🔎 Ground-Truth Evaluation

The project uses a known ground-truth dataset to evaluate whether the controller produced the expected financial outcome.

```text
Ground Truth
     │
     ▼
Expected Financial Outcome
     │
     │ compare
     ▼
Controller Result
     │
     ▼
Correct / Incorrect / Pending
```

This allows the project to measure performance across a batch instead of relying only on individual demonstrations.

The evaluation focuses on:

```text
Total Records
      +
Correct Results
      +
Incorrect Results
      +
Pending / Unresolved
      +
Accuracy
      +
Throughput
```

---

## 🧾 Auditability

Financial automation requires traceability.

The audit layer is designed to make the processing history reviewable:

```text
What happened?
      ↓
Which transaction?
      ↓
What exception occurred?
      ↓
Was AI used?
      ↓
What decision was produced?
      ↓
Was the result validated?
      ↓
Was recovery required?
```

This provides an audit trail instead of treating AI output as a black box.

---

## 🚨 Honest Exception Handling

The controller does not force every transaction into a successful resolution.

A transaction may remain:

```text
UNRESOLVED
```

when there is insufficient evidence or when AI/recovery mechanisms fail.

This is intentional:

```text
Correctly unresolved
        >
Confidently incorrect
```

The unresolved exception list is therefore an important part of both operational review and evaluation.

---

## 🧪 Testing Strategy

The project includes controlled exception scenarios to exercise normal processing and failure handling.

Examples include:

- Amount mismatch
- Missing payment
- Missing settlement
- Duplicate transaction
- Date mismatch
- Fee difference
- Invalid or missing financial values
- AI API failures
- Invalid AI responses

The objective is to demonstrate that exceptional records can be isolated and handled without compromising the entire processing batch.

---

## 🎯 Design Philosophy

ReconcileAI follows four core principles.

### 1. Use deterministic logic for deterministic problems

Financial calculations, matching, comparisons, and validation should use reliable programmatic rules whenever possible.

### 2. Use AI where reasoning adds value

LLMs are useful for interpreting ambiguous exception context and generating human-readable explanations.

### 3. Never blindly trust AI

AI output is treated as untrusted external output and validated before acceptance.

### 4. Fail safely

If the system cannot safely resolve a transaction:

```text
UNRESOLVED
```

is preferable to an unsupported financial decision.

---

## 🔒 Security

Do not commit:

```text
.env
API keys
Passwords
Private credentials
Local secrets
```

Use:

```text
.env.example
```

to document required environment variables without exposing credentials.

Generated local databases and Python cache files should also remain outside version control.

---

## 📌 Project Status

The repository contains the core components for the AI Finance Controller workflow:

- Synthetic data generation
- Financial source datasets
- Normalization
- Deterministic reconciliation
- Exception classification
- AI routing
- Gemini integration
- AI validation
- Agent workflow
- Audit logging
- Benchmarking
- Ground-truth evaluation
- Metrics generation
- Streamlit dashboard

The development focus is to keep the complete workflow reproducible, validate benchmark results, and maintain a clean repository suitable for demonstration and evaluation.

---

## 👤 Project

**Project:** ReconcileAI — AI Finance Controller

**Purpose:** AI-assisted financial reconciliation and exception operations.

**Primary focus:** Multi-source reconciliation with selective AI reasoning, safe failure recovery, measurable performance, and auditability.

---

## ⚠️ Disclaimer

This project uses **synthetic financial data** for demonstration, development, and evaluation purposes.

It is not intended to provide financial advice or replace production financial controls, accounting systems, compliance processes, or human oversight.
