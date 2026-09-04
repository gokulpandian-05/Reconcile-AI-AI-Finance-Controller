import os
import sqlite3
import pandas as pd
from datetime import datetime


# ============================================================
# AI FINANCE CONTROLLER
# STEP 20 - AUDIT & DECISION EVIDENCE
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

DB_PATH = os.path.join(
    DATA_DIR,
    "finance_controller.db"
)

AUDIT_REPORT_PATH = os.path.join(
    DATA_DIR,
    "audit_report.csv"
)

AUDIT_SUMMARY_PATH = os.path.join(
    DATA_DIR,
    "audit_summary.txt"
)


# ============================================================
# LOAD DATABASE
# ============================================================

def load_database_results():

    if not os.path.exists(DB_PATH):

        print("ERROR: Database not found:")
        print(DB_PATH)

        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    try:

        df = pd.read_sql_query(
            """
            SELECT
                result_id,
                transaction_id,
                exception_type,
                final_status,
                final_action,
                ai_confidence,
                ai_override,
                ai_attempts,
                ai_explanation,
                created_at,
                updated_at
            FROM reconciliation_results
            ORDER BY result_id
            """,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value):

    if pd.isna(value):

        return ""

    return (
        str(value)
        .strip()
        .upper()
    )


# ============================================================
# DETERMINE DECISION TYPE
# ============================================================

def determine_decision_type(row):

    final_status = normalize_text(
        row["final_status"]
    )

    final_action = normalize_text(
        row["final_action"]
    )

    ai_attempts = int(
        row["ai_attempts"]
        if pd.notna(row["ai_attempts"])
        else 0
    )

    ai_override = int(
        row["ai_override"]
        if pd.notna(row["ai_override"])
        else 0
    )

    # --------------------------------------------------------
    # Deterministic match
    # --------------------------------------------------------

    if (
        final_status == "RESOLVED"
        and
        final_action == "NO_ACTION"
    ):

        return "DETERMINISTIC_MATCH"

    # --------------------------------------------------------
    # Rule-based resolution
    # --------------------------------------------------------

    if final_action == "RULE_BASED_RESOLUTION":

        return "RULE_BASED_RESOLUTION"

    # --------------------------------------------------------
    # AI resolution
    # --------------------------------------------------------

    if final_status == "AI_RESOLVED":

        return "AI_RESOLUTION"

    if (
        final_status == "RESOLVED"
        and
        ai_attempts > 0
    ):

        return "AI_RESOLUTION"

    # --------------------------------------------------------
    # AI failure / recovery
    # --------------------------------------------------------

    if (
        ai_override == 1
        and
        final_action == "HUMAN_REVIEW"
    ):

        return "AI_FAILURE_RECOVERY"

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    if final_action == "HUMAN_REVIEW":

        return "HUMAN_REVIEW"

    # --------------------------------------------------------
    # Pending AI
    # --------------------------------------------------------

    if final_action == "NOT_SENT_TO_GEMINI":

        return "PENDING_AI"

    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    return "OTHER"


# ============================================================
# GENERATE DECISION REASON
# ============================================================

def generate_decision_reason(row):

    decision_type = row["decision_type"]

    exception_type = normalize_text(
        row["exception_type"]
    )

    ai_attempts = int(
        row["ai_attempts"]
        if pd.notna(row["ai_attempts"])
        else 0
    )

    ai_override = int(
        row["ai_override"]
        if pd.notna(row["ai_override"])
        else 0
    )

    # --------------------------------------------------------
    # Deterministic
    # --------------------------------------------------------

    if decision_type == "DETERMINISTIC_MATCH":

        return (
            "Transaction matched deterministically "
            "and required no further action."
        )

    # --------------------------------------------------------
    # Rule based
    # --------------------------------------------------------

    if decision_type == "RULE_BASED_RESOLUTION":

        if exception_type:

            return (
                f"Exception {exception_type} was resolved "
                "using a deterministic business rule."
            )

        return (
            "Transaction was resolved using "
            "a deterministic business rule."
        )

    # --------------------------------------------------------
    # AI resolution
    # --------------------------------------------------------

    if decision_type == "AI_RESOLUTION":

        return (
            "Transaction was routed to AI reasoning "
            "and received a successful AI resolution."
        )

    # --------------------------------------------------------
    # AI failure recovery
    # --------------------------------------------------------

    if decision_type == "AI_FAILURE_RECOVERY":

        return (
            "AI reasoning was attempted, but the AI path "
            "was unavailable or exhausted. The controller "
            "stopped further retries and escalated the "
            "transaction to human review."
        )

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    if decision_type == "HUMAN_REVIEW":

        return (
            "Transaction requires human review because "
            "the automated controller could not safely "
            "resolve the exception."
        )

    # --------------------------------------------------------
    # Pending
    # --------------------------------------------------------

    if decision_type == "PENDING_AI":

        return (
            "Transaction requires AI reasoning but was "
            "not sent to Gemini during this processing run."
        )

    # --------------------------------------------------------
    # Other
    # --------------------------------------------------------

    return (
        "Decision was recorded by the controller. "
        "Additional review may be required."
    )


# ============================================================
# GENERATE AUDIT REPORT
# ============================================================

def generate_audit_report():

    print()
    print("=" * 60)
    print(" AI FINANCE CONTROLLER - STEP 20")
    print(" AUDIT & DECISION EVIDENCE")
    print("=" * 60)

    # --------------------------------------------------------
    # Load database
    # --------------------------------------------------------

    results = load_database_results()

    if results.empty:

        print()
        print(
            "No database records available for audit."
        )

        return

    # --------------------------------------------------------
    # Normalize database fields
    # --------------------------------------------------------

    results["final_status"] = (
        results["final_status"]
        .apply(normalize_text)
    )

    results["final_action"] = (
        results["final_action"]
        .apply(normalize_text)
    )

    results["exception_type"] = (
        results["exception_type"]
        .apply(normalize_text)
    )

    results["ai_attempts"] = pd.to_numeric(
        results["ai_attempts"],
        errors="coerce"
    ).fillna(0).astype(int)

    results["ai_override"] = pd.to_numeric(
        results["ai_override"],
        errors="coerce"
    ).fillna(0).astype(int)

    results["ai_confidence"] = pd.to_numeric(
        results["ai_confidence"],
        errors="coerce"
    ).fillna(0.0)

    results["ai_explanation"] = (
        results["ai_explanation"]
        .fillna("")
        .astype(str)
    )

    # ========================================================
    # DECISION TYPE
    # ========================================================

    results["decision_type"] = (
        results.apply(
            determine_decision_type,
            axis=1
        )
    )

    # ========================================================
    # DECISION REASON
    # ========================================================

    results["decision_reason"] = (
        results.apply(
            generate_decision_reason,
            axis=1
        )
    )

    # ========================================================
    # FAILURE RECOVERY FLAG
    # ========================================================

    results["failure_recovery"] = (
        results["ai_override"] == 1
    ).map({
        True: "YES",
        False: "NO"
    })

    # ========================================================
    # AI USED FLAG
    # ========================================================

    results["ai_used"] = (
        results["ai_attempts"] > 0
    ).map({
        True: "YES",
        False: "NO"
    })

    # ========================================================
    # HUMAN REVIEW FLAG
    # ========================================================

    results["human_review_required"] = (
        results["final_action"] == "HUMAN_REVIEW"
    ).map({
        True: "YES",
        False: "NO"
    })

    # ========================================================
    # AUDIT TIMESTAMP
    # ========================================================

    audit_timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    results["audit_generated_at"] = (
        audit_timestamp
    )

    # ========================================================
    # REORDER COLUMNS
    # ========================================================

    audit_columns = [

        "result_id",

        "transaction_id",

        "exception_type",

        "decision_type",

        "final_status",

        "final_action",

        "decision_reason",

        "ai_used",

        "ai_attempts",

        "ai_confidence",

        "failure_recovery",

        "human_review_required",

        "ai_override",

        "ai_explanation",

        "created_at",

        "updated_at",

        "audit_generated_at"
    ]

    audit_df = results[
        audit_columns
    ].copy()

    # ========================================================
    # SAVE AUDIT CSV
    # ========================================================

    audit_df.to_csv(
        AUDIT_REPORT_PATH,
        index=False
    )

    # ========================================================
    # SUMMARY COUNTS
    # ========================================================

    total = len(
        audit_df
    )

    deterministic = int(
        (
            audit_df["decision_type"]
            == "DETERMINISTIC_MATCH"
        ).sum()
    )

    rule_based = int(
        (
            audit_df["decision_type"]
            == "RULE_BASED_RESOLUTION"
        ).sum()
    )

    ai_resolved = int(
        (
            audit_df["decision_type"]
            == "AI_RESOLUTION"
        ).sum()
    )

    ai_failure_recovery = int(
        (
            audit_df["decision_type"]
            == "AI_FAILURE_RECOVERY"
        ).sum()
    )

    human_review = int(
        (
            audit_df["human_review_required"]
            == "YES"
        ).sum()
    )

    ai_records = int(
        (
            audit_df["ai_used"]
            == "YES"
        ).sum()
    )

    ai_attempts = int(
        audit_df["ai_attempts"].sum()
    )

    resolved = int(
        audit_df["final_status"]
        .isin(
            [
                "RESOLVED",
                "AI_RESOLVED"
            ]
        )
        .sum()
    )

    unresolved = int(
        (
            audit_df["final_status"]
            == "UNRESOLVED"
        ).sum()
    )

    # ========================================================
    # EXCEPTION BREAKDOWN
    # ========================================================

    exception_counts = (
        audit_df["exception_type"]
        .replace("", "NONE")
        .value_counts()
    )

    # ========================================================
    # DECISION BREAKDOWN
    # ========================================================

    decision_counts = (
        audit_df["decision_type"]
        .value_counts()
    )

    # ========================================================
    # STATUS BREAKDOWN
    # ========================================================

    status_counts = (
        audit_df["final_status"]
        .value_counts()
    )

    # ========================================================
    # ACTION BREAKDOWN
    # ========================================================

    action_counts = (
        audit_df["final_action"]
        .value_counts()
    )

    # ========================================================
    # CREATE SUMMARY TEXT
    # ========================================================

    summary_lines = [

        "============================================================",

        "AI FINANCE CONTROLLER",

        "STEP 20 - AUDIT & DECISION EVIDENCE REPORT",

        "============================================================",

        "",

        f"Audit generated at : {audit_timestamp}",

        f"Database path      : {DB_PATH}",

        "",

        "------------------------------------------------------------",

        "PROCESSING SUMMARY",

        "------------------------------------------------------------",

        f"Total transactions : {total}",

        f"Resolved           : {resolved}",

        f"Unresolved         : {unresolved}",

        f"Human review       : {human_review}",

        "",

        "------------------------------------------------------------",

        "DECISION PATH SUMMARY",

        "------------------------------------------------------------",

        f"Deterministic matches : {deterministic}",

        f"Rule-based resolutions: {rule_based}",

        f"AI resolutions        : {ai_resolved}",

        f"AI failure recoveries : {ai_failure_recovery}",

        "",

        "------------------------------------------------------------",

        "AI USAGE",

        "------------------------------------------------------------",

        f"Records involving AI : {ai_records}",

        f"AI attempts          : {ai_attempts}",

        f"Failure recoveries   : {ai_failure_recovery}",

        "",

        "------------------------------------------------------------",

        "FINAL STATUS BREAKDOWN",

        "------------------------------------------------------------"
    ]

    for status, count in status_counts.items():

        summary_lines.append(
            f"{status}: {count}"
        )

    summary_lines.extend([

        "",

        "------------------------------------------------------------",

        "FINAL ACTION BREAKDOWN",

        "------------------------------------------------------------"
    ])

    for action, count in action_counts.items():

        summary_lines.append(
            f"{action}: {count}"
        )

    summary_lines.extend([

        "",

        "------------------------------------------------------------",

        "DECISION TYPE BREAKDOWN",

        "------------------------------------------------------------"
    ])

    for decision, count in decision_counts.items():

        summary_lines.append(
            f"{decision}: {count}"
        )

    summary_lines.extend([

        "",

        "------------------------------------------------------------",

        "EXCEPTION BREAKDOWN",

        "------------------------------------------------------------"
    ])

    for exception, count in exception_counts.items():

        summary_lines.append(
            f"{exception}: {count}"
        )

    summary_lines.extend([

        "",

        "------------------------------------------------------------",

        "FAILURE RECOVERY EVIDENCE",

        "------------------------------------------------------------"
    ])

    recovery_records = audit_df[
        audit_df["failure_recovery"]
        == "YES"
    ]

    if recovery_records.empty:

        summary_lines.append(
            "No failure recovery events recorded."
        )

    else:

        for _, row in recovery_records.iterrows():

            summary_lines.append(

                f"{row['transaction_id']} | "
                f"Exception={row['exception_type']} | "
                f"AI Attempts={row['ai_attempts']} | "
                f"Action={row['final_action']} | "
                f"Status={row['final_status']}"
            )

    summary_lines.extend([

        "",

        "------------------------------------------------------------",

        "AUDIT INTERPRETATION",

        "------------------------------------------------------------",

        "Every transaction stored in the SQLite database",

        "has been assigned an auditable decision type and",

        "decision reason.",

        "",

        "AI failures are preserved as evidence rather than",

        "being hidden. When an AI path fails, the controller",

        "can escalate the transaction to HUMAN_REVIEW.",

        "",

        "This provides transaction-level traceability for",

        "automated decisions, AI usage, exceptions, and",

        "failure recovery.",

        "",

        "============================================================",

        "END OF AUDIT REPORT",

        "============================================================"
    ])

    summary_text = "\n".join(
        summary_lines
    )

    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    with open(
        AUDIT_SUMMARY_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            summary_text
        )

    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    print()

    print(
        "AUDIT REPORT GENERATED SUCCESSFULLY"
    )

    print()

    print(
        f"Total transactions : {total}"
    )

    print(
        f"Resolved           : {resolved}"
    )

    print(
        f"Unresolved         : {unresolved}"
    )

    print(
        f"Human review       : {human_review}"
    )

    print(
        f"AI records         : {ai_records}"
    )

    print(
        f"AI attempts        : {ai_attempts}"
    )

    print(
        f"Failure recoveries : {ai_failure_recovery}"
    )

    print()

    print(
        "Decision types:"
    )

    print(
        decision_counts.to_string()
    )

    print()

    print(
        "Audit report saved to:"
    )

    print(
        AUDIT_REPORT_PATH
    )

    print()

    print(
        "Audit summary saved to:"
    )

    print(
        AUDIT_SUMMARY_PATH
    )

    print()

    print(
        "=" * 60
    )

    print(
        "STEP 20 COMPLETED"
    )

    print(
        "=" * 60
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_audit_report()