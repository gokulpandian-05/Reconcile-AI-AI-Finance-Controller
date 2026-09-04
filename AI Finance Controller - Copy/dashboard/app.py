
import os
import pandas as pd
import streamlit as st


# ============================================================
# AI FINANCE CONTROLLER
# STEP 22 - FINAL DASHBOARD / PRESENTATION EVIDENCE
# ============================================================

st.set_page_config(
    page_title="AI Finance Controller",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("💰 AI Finance Controller")

st.subheader(
    "ReconcileAI — Autonomous Finance Operations"
)

st.caption(
    "Multi-source reconciliation • Exception classification • "
    "AI reasoning • Failure recovery • Human escalation • "
    "Audit evidence"
)

st.divider()


# ============================================================
# LOAD CSV
# ============================================================

@st.cache_data
def load_csv(filename):

    path = os.path.join(
        DATA_DIR,
        filename
    )

    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)

    except Exception as error:

        st.warning(
            f"Could not load {filename}: {error}"
        )

        return pd.DataFrame()


# ============================================================
# LOAD PROJECT OUTPUTS
# ============================================================

final_results = load_csv(
    "final_results.csv"
)

metrics = load_csv(
    "metrics.csv"
)

benchmark = load_csv(
    "benchmark.csv"
)

benchmark_details = load_csv(
    "benchmark_details.csv"
)

audit_report = load_csv(
    "audit_report.csv"
)


# ============================================================
# HELPER
# ============================================================

def safe_int(value, default=0):

    try:

        if pd.isna(value):
            return default

        return int(float(value))

    except Exception:

        return default


def safe_float(value, default=0.0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


def get_metric(column, default=0):

    if metrics.empty:
        return default

    if column not in metrics.columns:
        return default

    return metrics.iloc[0].get(
        column,
        default
    )


# ============================================================
# BENCHMARK METRICS
# ============================================================

total_ground_truth = 0
database_results = len(final_results)

evaluated = 0
pending = 0
correct = 0
incorrect = 0
accuracy = 0.0

deterministic = 0
rule_based = 0
ai_reasoning = 0

throughput = 0.0


if not benchmark.empty:

    row = benchmark.iloc[0]

    total_ground_truth = safe_int(
        row.get(
            "ground_truth_records",
            database_results
        )
    )

    database_results = safe_int(
        row.get(
            "database_result_records",
            database_results
        )
    )

    evaluated = safe_int(
        row.get(
            "evaluated_records",
            0
        )
    )

    pending = safe_int(
        row.get(
            "pending_records",
            0
        )
    )

    correct = safe_int(
        row.get(
            "correct_records",
            0
        )
    )

    incorrect = safe_int(
        row.get(
            "incorrect_records",
            0
        )
    )

    accuracy = safe_float(
        row.get(
            "accuracy_percent",
            0
        )
    )

    deterministic = safe_int(
        row.get(
            "deterministic_total",
            0
        )
    )

    rule_based = safe_int(
        row.get(
            "rule_based_total",
            0
        )
    )

    ai_reasoning = safe_int(
        row.get(
            "ai_total",
            0
        )
    )

    throughput = safe_float(
        row.get(
            "throughput_records_per_second",
            0
        )
    )


# ============================================================
# METRICS OUTPUT
# ============================================================

resolved = 0
unresolved = 0
human_review = 0
ai_records = 0
ai_attempts = 0
failure_recovery = 0


if not metrics.empty:

    row = metrics.iloc[0]

    resolved = safe_int(
        row.get(
            "resolved",
            row.get(
                "resolved_records",
                0
            )
        )
    )

    unresolved = safe_int(
        row.get(
            "unresolved",
            row.get(
                "unresolved_records",
                0
            )
        )
    )

    human_review = safe_int(
        row.get(
            "human_review",
            0
        )
    )

    ai_records = safe_int(
        row.get(
            "ai_records",
            0
        )
    )

    ai_attempts = safe_int(
        row.get(
            "ai_attempts",
            0
        )
    )

    failure_recovery = safe_int(
        row.get(
            "failure_recovery_events",
            row.get(
                "failure_recovery",
                0
            )
        )
    )


# ============================================================
# FALLBACK CALCULATIONS
# ============================================================

if not final_results.empty:

    if "final_status" in final_results.columns:

        status_series = (
            final_results["final_status"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

        if resolved == 0:

            resolved = int(
                (
                    status_series
                    == "RESOLVED"
                ).sum()
            )

        if unresolved == 0:

            unresolved = int(
                (
                    status_series
                    == "UNRESOLVED"
                ).sum()
            )


# ============================================================
# HERO METRICS
# ============================================================

st.header("📊 Executive Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Ground Truth Records",
        total_ground_truth
    )

with c2:

    st.metric(
        "Accuracy",
        f"{accuracy:.2f}%"
    )

with c3:

    st.metric(
        "Resolved",
        resolved
    )

with c4:

    st.metric(
        "Human Review",
        human_review
    )


# ============================================================
# DATASET STATUS
# ============================================================

if total_ground_truth != database_results:

    st.warning(
        f"Dataset status: {total_ground_truth} ground-truth "
        f"records vs {database_results} database results. "
        f"{total_ground_truth - database_results} record(s) "
        f"are currently pending because they are not present "
        f"in the database results."
    )


st.divider()


# ============================================================
# CONTROLLED EVALUATION
# ============================================================

st.header("🎯 Controlled Evaluation")

evaluation_data = pd.DataFrame(
    {
        "Result": [
            "Correct",
            "Incorrect",
            "Pending"
        ],
        "Records": [
            correct,
            incorrect,
            pending
        ]
    }
)

col1, col2 = st.columns(2)

with col1:

    st.subheader(
        "Ground-Truth Results"
    )

    st.bar_chart(
        evaluation_data.set_index(
            "Result"
        )
    )


with col2:

    st.subheader(
        "Evaluation Summary"
    )

    st.metric(
        "Evaluated",
        evaluated
    )

    st.metric(
        "Correct",
        correct
    )

    st.metric(
        "Incorrect",
        incorrect
    )

    st.metric(
        "Pending",
        pending
    )


# ============================================================
# ACCURACY EXPLANATION
# ============================================================

st.info(
    f"Ground-truth accuracy = {correct} correct / "
    f"{evaluated} evaluated = {accuracy:.2f}%."
)


st.divider()


# ============================================================
# FINAL STATUS
# ============================================================

st.header("✅ Final Reconciliation Status")

if not final_results.empty:

    if "final_status" in final_results.columns:

        status_counts = (
            final_results[
                "final_status"
            ]
            .fillna("UNKNOWN")
            .astype(str)
            .str.upper()
            .str.strip()
            .value_counts()
            .rename_axis("Status")
            .reset_index(
                name="Records"
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            st.bar_chart(
                status_counts.set_index(
                    "Status"
                )
            )

        with col2:

            st.dataframe(
                status_counts,
                use_container_width=True,
                hide_index=True
            )

    else:

        st.warning(
            "final_status column not found."
        )

else:

    st.warning(
        "final_results.csv is empty."
    )


# ============================================================
# FINAL ACTION
# ============================================================

st.subheader(
    "Final Actions"
)

if not final_results.empty:

    if "final_action" in final_results.columns:

        action_counts = (
            final_results[
                "final_action"
            ]
            .fillna("UNKNOWN")
            .astype(str)
            .str.upper()
            .str.strip()
            .value_counts()
            .rename_axis("Final Action")
            .reset_index(
                name="Records"
            )
        )

        st.bar_chart(
            action_counts.set_index(
                "Final Action"
            )
        )

        st.dataframe(
            action_counts,
            use_container_width=True,
            hide_index=True
        )


st.divider()


# ============================================================
# AI DECISION PIPELINE
# ============================================================

st.header("🤖 AI Decision Pipeline")

ai1, ai2, ai3, ai4 = st.columns(4)

with ai1:

    st.metric(
        "Deterministic",
        deterministic
    )

with ai2:

    st.metric(
        "Rule Based",
        rule_based
    )

with ai3:

    st.metric(
        "AI Reasoning",
        ai_reasoning
    )

with ai4:

    st.metric(
        "AI Records",
        ai_records
    )


pipeline_data = pd.DataFrame(
    {
        "Decision Type": [
            "Deterministic",
            "Rule Based",
            "AI Reasoning"
        ],
        "Records": [
            deterministic,
            rule_based,
            ai_reasoning
        ]
    }
)

st.bar_chart(
    pipeline_data.set_index(
        "Decision Type"
    )
)


# ============================================================
# FAILURE RECOVERY
# ============================================================

st.header("🛡️ Failure Recovery")

fr1, fr2, fr3 = st.columns(3)

with fr1:

    st.metric(
        "AI Attempts",
        ai_attempts
    )

with fr2:

    st.metric(
        "Failure Recoveries",
        failure_recovery
    )

with fr3:

    st.metric(
        "Human Review",
        human_review
    )


if not benchmark_details.empty:

    if "decision_type" in benchmark_details.columns:

        recovery_counts = (
            benchmark_details[
                "decision_type"
            ]
            .fillna("OTHER")
            .astype(str)
            .str.upper()
            .str.strip()
            .value_counts()
            .rename_axis(
                "Decision Type"
            )
            .reset_index(
                name="Records"
            )
        )

        st.subheader(
            "Decision / Recovery Breakdown"
        )

        st.bar_chart(
            recovery_counts.set_index(
                "Decision Type"
            )
        )


# ============================================================
# EXCEPTION ANALYSIS
# ============================================================

st.header("⚠️ Exception Analysis")

exception_data = pd.DataFrame()

if not final_results.empty:

    exception_column = None

    if "exception_type" in final_results.columns:

        exception_column = "exception_type"

    elif "exception_category" in final_results.columns:

        exception_column = "exception_category"

    if exception_column:

        exception_data = (
            final_results[
                exception_column
            ]
            .fillna("NONE")
            .astype(str)
            .str.upper()
            .str.strip()
            .value_counts()
            .rename_axis(
                "Exception Type"
            )
            .reset_index(
                name="Records"
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            st.bar_chart(
                exception_data.set_index(
                    "Exception Type"
                )
            )

        with col2:

            st.dataframe(
                exception_data,
                use_container_width=True,
                hide_index=True
            )

    else:

        st.info(
            "No exception type column found."
        )


# ============================================================
# FAILURE RECOVERY TRANSACTIONS
# ============================================================

if not benchmark_details.empty:

    if "ai_override" in benchmark_details.columns:

        recovery_records = benchmark_details[
            pd.to_numeric(
                benchmark_details[
                    "ai_override"
                ],
                errors="coerce"
            )
            .fillna(0)
            == 1
        ].copy()

        if not recovery_records.empty:

            st.subheader(
                "Failure Recovery Transactions"
            )

            recovery_columns = [

                "transaction_id",

                "final_status",

                "final_action",

                "decision_type",

                "ai_attempts",

                "ai_override"
            ]

            available_columns = [
                column
                for column in recovery_columns
                if column in recovery_records.columns
            ]

            st.dataframe(
                recovery_records[
                    available_columns
                ],
                use_container_width=True,
                hide_index=True
            )


st.divider()


# ============================================================
# TRANSACTION-LEVEL AUDIT
# ============================================================

st.header("🔍 Transaction-Level Audit Evidence")

if not benchmark_details.empty:

    display_columns = [

        "transaction_id",

        "expected_status",

        "exception_type_gt",

        "final_status",

        "final_action",

        "decision_type",

        "evaluation_state",

        "result_category",

        "correct",

        "ai_attempts",

        "ai_override"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in benchmark_details.columns
    ]

    st.dataframe(
        benchmark_details[
            available_columns
        ],
        use_container_width=True,
        hide_index=True,
        height=500
    )

else:

    st.warning(
        "benchmark_details.csv is empty."
    )


# ============================================================
# SEARCH TRANSACTION
# ============================================================

st.subheader(
    "🔎 Transaction Lookup"
)

transaction_id = st.text_input(
    "Enter Transaction ID",
    placeholder="Example: TX0024"
)

if transaction_id:

    transaction_id = (
        transaction_id
        .strip()
        .upper()
    )

    if not benchmark_details.empty:

        if "transaction_id" in benchmark_details.columns:

            match = benchmark_details[
                benchmark_details[
                    "transaction_id"
                ]
                .astype(str)
                .str.upper()
                .str.strip()
                == transaction_id
            ]

            if not match.empty:

                st.success(
                    f"Transaction {transaction_id} found."
                )

                st.dataframe(
                    match,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.error(
                    f"Transaction {transaction_id} "
                    "not found in benchmark results."
                )


# ============================================================
# BUILDATHON EVIDENCE
# ============================================================

st.divider()

st.header("🏆 Buildathon Evidence")

e1, e2, e3, e4 = st.columns(4)

with e1:

    st.metric(
        "Accuracy",
        f"{accuracy:.2f}%"
    )

with e2:

    st.metric(
        "Correct",
        correct
    )

with e3:

    st.metric(
        "Failure Recoveries",
        failure_recovery
    )

with e4:

    st.metric(
        "Throughput",
        f"{throughput:.2f}/sec"
    )


# ============================================================
# ARCHITECTURE SUMMARY
# ============================================================

st.divider()

st.header("🧠 System Architecture")

st.markdown(
    """
### Finance Reconciliation Flow

**Invoice Data**
→ **Payment Data**
→ **Settlement Data**
→ **Normalization**
→ **Deterministic Reconciliation**
→ **Exception Classification**
→ **AI Routing**
→ **Bounded AI Reasoning**
→ **Decision Validation**
→ **Failure Recovery**
→ **Final Resolution**
→ **SQLite Storage**
→ **Audit Trail**
→ **Ground-Truth Evaluation**
→ **Benchmark**
→ **Dashboard**

### Decision Safety

- Deterministic matches are resolved without unnecessary AI calls.
- AI is used only for routed exceptions.
- AI outputs are validated before final decisions.
- Failed AI calls are not treated as successful resolutions.
- Failed AI reasoning can trigger **HUMAN_REVIEW**.
- Every transaction produces auditable decision evidence.
"""
)


# ============================================================
# PROJECT OUTPUT FILES
# ============================================================

st.divider()

st.header("📁 Generated Evidence")

files = [

    "final_results.csv",

    "metrics.csv",

    "benchmark.csv",

    "benchmark_details.csv",

    "benchmark_summary.txt",

    "audit_log.csv",

    "audit_report.csv",

    "audit_summary.txt",

    "finance_controller.db"
]

file_status = []

for filename in files:

    path = os.path.join(
        DATA_DIR,
        filename
    )

    file_status.append(
        {
            "File": filename,
            "Status": (
                "Available"
                if os.path.exists(path)
                else "Missing"
            )
        }
    )

st.dataframe(
    pd.DataFrame(file_status),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Finance Controller | ReconcileAI | "
    "Controlled financial reconciliation with "
    "bounded AI decisions, failure recovery, "
    "human escalation and auditability."
)

st.caption(
    "Step 22 — Final Dashboard / Presentation Evidence"
)