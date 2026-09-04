
import pandas as pd
import os
import sys


# ============================================================
# AI FINANCE CONTROLLER
# STEP 12 — AI ROUTING + AGENT ORCHESTRATION
# ============================================================


# ============================================================
# PATH CONFIGURATION
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

INPUT_FILE = os.path.join(
    DATA_DIR,
    "classified_exceptions.csv"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "final_results.csv"
)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

SRC_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent import process_transaction
from database import save_reconciliation_result


# ============================================================
# LOAD CLASSIFIED EXCEPTIONS
# ============================================================

if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"""
classified_exceptions.csv not found:

{INPUT_FILE}

Run exception_classifier.py before router.py.
"""
    )


df = pd.read_csv(INPUT_FILE)


print("============================================================")
print(" AI FINANCE CONTROLLER")
print(" STEP 12 — AI ROUTING + AGENT ORCHESTRATION")
print("============================================================")

print(
    f"\nClassified records loaded: {len(df)}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "transaction_id",
    "invoice_id",
    "customer_id",
    "invoice_amount",
    "payment_amount",
    "gross_amount",
    "fee",
    "tax",
    "adjustment",
    "net_amount",
    "difference",
    "reason",
    "exception_type",
    "exception_category"
]


missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]


if missing_columns:

    raise ValueError(
        "\nMissing columns in classified_exceptions.csv:\n"
        +
        "\n".join(
            f" - {col}"
            for col in missing_columns
        )
    )


# ============================================================
# NORMALIZE TEXT
# ============================================================

df["exception_category"] = (
    df["exception_category"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

df["exception_type"] = (
    df["exception_type"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# HELPER — MISSING TRANSACTION ID
# ============================================================

def is_missing_transaction_id(value):

    if pd.isna(value):
        return True

    value = str(value).strip().upper()

    return value in {
        "",
        "NAN",
        "NONE",
        "NULL",
        "NA",
        "N/A"
    }


missing_transaction_mask = (
    df["transaction_id"]
    .apply(is_missing_transaction_id)
)


missing_transaction_count = (
    missing_transaction_mask.sum()
)

valid_transaction_count = (
    len(df)
    - missing_transaction_count
)


print("\n============================================================")
print(" TRANSACTION ID VALIDATION")
print("============================================================")

print(
    f"Valid transaction IDs   : "
    f"{valid_transaction_count}"
)

print(
    f"Missing transaction IDs : "
    f"{missing_transaction_count}"
)


# ============================================================
# AI ROUTING POLICY
# ============================================================
#
# NO_AI
#     Already matched records.
#
# HUMAN_REVIEW
#     Data-integrity failures such as missing transaction ID.
#
# AI_REQUIRED
#     Contextual exceptions where LLM reasoning is useful.
#
# RULE_BASED
#     Deterministic exceptions.
#
# ============================================================


AI_REQUIRED = {

    "PAYMENT_MISSING",
    "MISSING_PAYMENT",

    "AMOUNT_DISCREPANCY",
    "AMOUNT_MISMATCH",

    "SETTLEMENT_MISSING",
    "MISSING_SETTLEMENT",

    "SETTLEMENT_AMOUNT_DISCREPANCY",

    "SETTLEMENT_DELAY",
    "DATE_MISMATCH"
}


RULE_BASED = {

    "DUPLICATE_TRANSACTION",

    "FEE_DIFFERENCE",

    "SETTLEMENT_CALCULATION"
}


def decide_ai_requirement(row):

    # --------------------------------------------------------
    # Missing transaction ID
    # --------------------------------------------------------

    if is_missing_transaction_id(
        row["transaction_id"]
    ):

        return pd.Series([
            "HUMAN_REVIEW",
            "MISSING_TRANSACTION_ID"
        ])


    category = row["exception_category"]


    # --------------------------------------------------------
    # No exception
    # --------------------------------------------------------

    if category in {
        "NO_EXCEPTION",
        "NONE",
        "MATCHED"
    }:

        return pd.Series([
            "NO_AI",
            "ALREADY_MATCHED"
        ])


    # --------------------------------------------------------
    # AI required
    # --------------------------------------------------------

    if category in AI_REQUIRED:

        return pd.Series([
            "AI_REQUIRED",
            "CONTEXTUAL_REASONING"
        ])


    # --------------------------------------------------------
    # Rule based
    # --------------------------------------------------------

    if category in RULE_BASED:

        return pd.Series([
            "RULE_BASED",
            "DETERMINISTIC_RULE"
        ])


    # --------------------------------------------------------
    # Unknown exception
    # --------------------------------------------------------

    return pd.Series([
        "HUMAN_REVIEW",
        "UNKNOWN_EXCEPTION_REQUIRES_REVIEW"
    ])


# ============================================================
# APPLY ROUTING
# ============================================================

df[
    [
        "ai_decision",
        "routing_reason"
    ]
] = df.apply(
    decide_ai_requirement,
    axis=1
)


print("\n============================================================")
print(" AI ROUTING")
print("============================================================")

print(
    df["ai_decision"].value_counts()
)


# ============================================================
# INITIALIZE FINAL RESULT COLUMNS
# ============================================================

df["final_status"] = "PENDING"

df["final_action"] = ""

df["ai_explanation"] = ""

df["ai_confidence"] = 0.0

df["ai_override"] = False

df["ai_attempts"] = 0

df["ai_override_reason"] = ""


# ============================================================
# 1. HANDLE NO-AI RECORDS
# ============================================================

no_ai_mask = (
    df["ai_decision"]
    == "NO_AI"
)


df.loc[
    no_ai_mask,
    "final_status"
] = "RESOLVED"


df.loc[
    no_ai_mask,
    "final_action"
] = "NO_ACTION"


df.loc[
    no_ai_mask,
    "ai_explanation"
] = (
    "No exception detected. "
    "No AI reasoning required."
)


df.loc[
    no_ai_mask,
    "ai_confidence"
] = 1.0


# ============================================================
# 2. HANDLE RULE-BASED RECORDS
# ============================================================

rule_mask = (
    df["ai_decision"]
    == "RULE_BASED"
)


df.loc[
    rule_mask,
    "final_status"
] = "RESOLVED"


df.loc[
    rule_mask,
    "final_action"
] = "RULE_BASED_RESOLUTION"


df.loc[
    rule_mask,
    "ai_explanation"
] = (
    "Resolved using deterministic rule-based "
    "logic without requiring AI reasoning."
)


df.loc[
    rule_mask,
    "ai_confidence"
] = 1.0


# ============================================================
# 3. HANDLE INVALID TRANSACTION ID
# ============================================================
#
# IMPORTANT:
#
# These records are NOT deleted.
#
# They are NOT sent to Gemini.
#
# They go directly to HUMAN_REVIEW.
#
# Example:
#
# INV0002 → transaction_id missing
# INV0048 → transaction_id missing
#
# ============================================================

human_review_mask = (
    df["ai_decision"]
    == "HUMAN_REVIEW"
)


df.loc[
    human_review_mask,
    "final_status"
] = "UNRESOLVED"


df.loc[
    human_review_mask,
    "final_action"
] = "HUMAN_REVIEW"


df.loc[
    human_review_mask,
    "ai_explanation"
] = (
    "Record requires human review. "
    "Automated processing cannot safely resolve "
    "the data-integrity issue."
)


df.loc[
    human_review_mask,
    "ai_confidence"
] = 0.0


df.loc[
    human_review_mask,
    "ai_override"
] = True


df.loc[
    human_review_mask,
    "ai_attempts"
] = 0


df.loc[
    human_review_mask,
    "ai_override_reason"
] = (
    df.loc[
        human_review_mask,
        "routing_reason"
    ]
)


# ============================================================
# BUILD TRANSACTION FOR AGENT
# ============================================================

def build_transaction(row):

    transaction_id = row["transaction_id"]


    # --------------------------------------------------------
    # Invoice
    # --------------------------------------------------------

    invoice = {

        "invoice_id":
            row["invoice_id"],

        "customer_id":
            row["customer_id"],

        "invoice_amount":
            row["invoice_amount"]
    }


    # --------------------------------------------------------
    # Payment
    # --------------------------------------------------------

    payment = {}


    if pd.notna(
        row["payment_amount"]
    ):

        payment = {

            "transaction_id":
                transaction_id,

            "payment_amount":
                row["payment_amount"]
        }


    # --------------------------------------------------------
    # Settlement
    # --------------------------------------------------------

    settlement = {}


    if pd.notna(
        row["gross_amount"]
    ):

        settlement = {

            "settlement_id":
                "SET_" + str(
                    transaction_id
                ),

            "gross_amount":
                row["gross_amount"],

            "fee":
                row["fee"],

            "tax":
                row["tax"],

            "adjustment":
                row["adjustment"],

            "net_amount":
                row["net_amount"]
        }


    # --------------------------------------------------------
    # Invoice vs Payment
    # --------------------------------------------------------

    invoice_equals_payment = False


    if (
        pd.notna(row["invoice_amount"])
        and
        pd.notna(row["payment_amount"])
    ):

        invoice_equals_payment = (

            round(
                float(
                    row["invoice_amount"]
                ),
                2
            )

            ==

            round(
                float(
                    row["payment_amount"]
                ),
                2
            )
        )


    # --------------------------------------------------------
    # Settlement calculation
    # --------------------------------------------------------

    settlement_calculation_valid = False


    settlement_columns = [

        "gross_amount",
        "fee",
        "tax",
        "adjustment",
        "net_amount"
    ]


    if all(
        pd.notna(row[col])
        for col in settlement_columns
    ):

        expected_net = round(

            float(row["gross_amount"])
            -
            float(row["fee"])
            -
            float(row["tax"])
            +
            float(row["adjustment"]),

            2
        )


        actual_net = round(

            float(row["net_amount"]),

            2
        )


        settlement_calculation_valid = (
            expected_net
            ==
            actual_net
        )


    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    checks = {

        "invoice_equals_payment":
            invoice_equals_payment,

        "payment_present":
            bool(payment),

        "settlement_present":
            bool(settlement),

        "settlement_calculation_valid":
            settlement_calculation_valid,

        "difference":
            row["difference"],

        "reason":
            row["reason"]
    }


    # --------------------------------------------------------
    # Final transaction object
    # --------------------------------------------------------

    return {

        "transaction_id":
            transaction_id,

        "invoice":
            invoice,

        "payment":
            payment,

        "settlement":
            settlement,

        "exception_type":
            row["exception_category"],

        "checks":
            checks
    }


# ============================================================
# CONTROLLED AI TEST MODE
# ============================================================

TEST_MODE = False

TEST_TRANSACTION_ID = "TX0013"


# ============================================================
# SELECT AI RECORDS
# ============================================================

if TEST_MODE:

    ai_rows = df[
        (df["ai_decision"] == "AI_REQUIRED")
        &
        (
            df["transaction_id"].astype(str)
            == TEST_TRANSACTION_ID
        )
    ].copy()

else:

    ai_rows = df[
        df["ai_decision"]
        == "AI_REQUIRED"
    ].copy()


# ============================================================
# AI PROCESSING SUMMARY
# ============================================================

print("\n============================================================")
print(" AI PROCESSING")
print("============================================================")


if TEST_MODE:

    print(
        "CONTROLLED TEST MODE: ON"
    )

    print(
        "Selected transaction:",
        TEST_TRANSACTION_ID
    )

else:

    print(
        "FULL AI MODE: ON"
    )


print(
    "AI-required records selected:",
    len(ai_rows)
)


print(
    "Maximum Gemini requests for this run:",
    len(ai_rows)
)


# ============================================================
# PROCESS AI RECORDS
# ============================================================

ai_results = []


for _, row in ai_rows.iterrows():

    transaction = build_transaction(
        row
    )


    transaction_id = (
        transaction["transaction_id"]
    )


    print(
        f"\nProcessing {transaction_id}..."
    )


    try:

        result = process_transaction(

            transaction,

            ai_required=True
        )


        if result is None:

            raise RuntimeError(
                "Agent returned None."
            )


        ai_results.append(
            result
        )


        print(
            f"AI processing completed: "
            f"{transaction_id}"
        )


    except Exception as e:

        print(
            "AI processing failed."
        )

        print(
            f"Transaction: {transaction_id}"
        )

        print(
            f"Reason: {str(e)}"
        )


        # ====================================================
        # FAILURE RECOVERY
        # ====================================================
        #
        # AI failure MUST NOT be considered resolved.
        #
        # It becomes HUMAN_REVIEW.
        #
        # ====================================================

        ai_results.append({

            "transaction_id":
                transaction_id,

            "exception_type":
                row["exception_category"],

            "explanation":
                (
                    "AI processing failed. "
                    "Transaction requires human review."
                ),

            "evidence":
                [],

            "calculation":
                "",

            "status":
                "UNRESOLVED",

            "confidence":
                0.0,

            "recommended_action":
                "HUMAN_REVIEW",

            "override":
                True,

            "override_reason":
                str(e),

            "llm_attempt":
                0
        })


# ============================================================
# APPLY AI RESULTS
# ============================================================

for result in ai_results:

    transaction_id = result.get(
        "transaction_id"
    )


    # --------------------------------------------------------
    # Find corresponding row
    # --------------------------------------------------------

    mask = (

        df["transaction_id"].astype(str)
        == str(transaction_id)
    )


    if not mask.any():

        print(
            f"WARNING: AI result could not be "
            f"matched to {transaction_id}"
        )

        continue


    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    result_status = result.get(
        "status",
        "UNRESOLVED"
    )


    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    result_action = result.get(
        "recommended_action",
        "HUMAN_REVIEW"
    )


    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    result_explanation = result.get(
        "explanation",
        ""
    )


    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    result_confidence = result.get(
        "confidence",
        0.0
    )


    # --------------------------------------------------------
    # Override
    # --------------------------------------------------------

    result_override = result.get(
        "override",
        False
    )


    # --------------------------------------------------------
    # Attempts
    # --------------------------------------------------------

    result_attempts = result.get(
        "llm_attempt",
        0
    )


    # --------------------------------------------------------
    # Override reason
    # --------------------------------------------------------

    result_override_reason = result.get(
        "override_reason",
        ""
    )


    # --------------------------------------------------------
    # Apply
    # --------------------------------------------------------

    df.loc[
        mask,
        "final_status"
    ] = result_status


    df.loc[
        mask,
        "final_action"
    ] = result_action


    df.loc[
        mask,
        "ai_explanation"
    ] = result_explanation


    df.loc[
        mask,
        "ai_confidence"
    ] = result_confidence


    df.loc[
        mask,
        "ai_override"
    ] = result_override


    df.loc[
        mask,
        "ai_attempts"
    ] = result_attempts


    df.loc[
        mask,
        "ai_override_reason"
    ] = result_override_reason


# ============================================================
# SAFETY CHECK
# ============================================================
#
# No record should remain PENDING after routing.
#
# A PENDING record means something in the orchestration
# pipeline was not handled.
#
# ============================================================

pending_mask = (
    df["final_status"]
    == "PENDING"
)


pending_count = (
    pending_mask.sum()
)


if pending_count > 0:

    print(
        f"\nWARNING: {pending_count} records "
        "remain PENDING."
    )

    print(
        "Routing them to HUMAN_REVIEW "
        "for safety."
    )


    df.loc[
        pending_mask,
        "final_status"
    ] = "UNRESOLVED"


    df.loc[
        pending_mask,
        "final_action"
    ] = "HUMAN_REVIEW"


    df.loc[
        pending_mask,
        "ai_explanation"
    ] = (
        "Record remained pending after routing. "
        "Human review required."
    )


    df.loc[
        pending_mask,
        "ai_override"
    ] = True


    df.loc[
        pending_mask,
        "ai_override_reason"
    ] = (
        "Unhandled routing state."
    )


# ============================================================
# SAVE FINAL RESULTS CSV
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SAVE RESULTS TO DATABASE
# ============================================================

print("\n============================================================")
print(" SAVING RESULTS TO DATABASE")
print("============================================================")


database_saved = 0

database_failed = 0


for _, row in df.iterrows():

    try:

        # ----------------------------------------------------
        # Database identifier
        # ----------------------------------------------------
        #
        # Normal record:
        #     transaction_id
        #
        # Missing transaction ID:
        #     invoice_id fallback
        #
        # This prevents "nan" from being stored as a fake
        # transaction identifier.
        #
        # ----------------------------------------------------

        if is_missing_transaction_id(
            row["transaction_id"]
        ):

            database_transaction_id = (
                "INVOICE:"
                +
                str(
                    row["invoice_id"]
                )
            )

        else:

            database_transaction_id = str(
                row["transaction_id"]
            )


        save_reconciliation_result(

            transaction_id=
                database_transaction_id,

            exception_type=
                str(
                    row["exception_category"]
                ),

            final_status=
                str(
                    row["final_status"]
                ),

            final_action=
                str(
                    row["final_action"]
                ),

            ai_confidence=
                float(
                    row["ai_confidence"]
                ),

            ai_override=
                bool(
                    row["ai_override"]
                ),

            ai_attempts=
                int(
                    row["ai_attempts"]
                ),

            ai_explanation=
                str(
                    row["ai_explanation"]
                )
        )


        database_saved += 1


    except Exception as e:

        database_failed += 1


        identifier = (

            row["transaction_id"]

            if not is_missing_transaction_id(
                row["transaction_id"]
            )

            else row["invoice_id"]
        )


        print(
            f"Database save failed for "
            f"{identifier}: {e}"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n============================================================")
print(" FINAL AI FINANCE CONTROLLER RESULTS")
print("============================================================")


print(
    f"\nTotal records: {len(df)}"
)


print("\nAI routing:")

print(
    df["ai_decision"].value_counts()
)


print("\nFinal status:")

print(
    df["final_status"].value_counts()
)


print("\nFinal actions:")

print(
    df["final_action"].value_counts()
)


print(
    "\nAI / Gemini requests attempted:",
    len(ai_results)
)


print(
    "Human review required:",
    (
        df["final_action"]
        == "HUMAN_REVIEW"
    ).sum()
)


print(
    "Missing transaction IDs:",
    missing_transaction_count
)


print(
    "\nDatabase records saved:",
    database_saved
)


print(
    "Database failures:",
    database_failed
)


print(
    "\nOutput saved to:"
)


print(
    OUTPUT_FILE
)


# ============================================================
# HUMAN REVIEW RECORDS
# ============================================================

human_review_df = df[
    df["final_action"]
    == "HUMAN_REVIEW"
]


print("\n============================================================")
print(" HUMAN REVIEW QUEUE")
print("============================================================")


if human_review_df.empty:

    print(
        "No records require human review."
    )

else:

    review_columns = [

        "invoice_id",
        "transaction_id",
        "exception_type",
        "exception_category",
        "priority",
        "routing_reason",
        "final_status",
        "final_action"
    ]


    available_review_columns = [

        col
        for col in review_columns
        if col in df.columns
    ]


    print(
        human_review_df[
            available_review_columns
        ].to_string(index=False)
    )


# ============================================================
# FINAL COMPLETION
# ============================================================

print("\n============================================================")
print(" STEP 12 COMPLETED")
print("============================================================")