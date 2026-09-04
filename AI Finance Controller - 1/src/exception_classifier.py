
import pandas as pd
import os


# ============================================================
# AI FINANCE CONTROLLER
# STEP 7 — EXCEPTION CLASSIFICATION
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
    "reconciliation_results.csv"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "classified_exceptions.csv"
)


# ============================================================
# LOAD RECONCILIATION RESULTS
# ============================================================

if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"\nReconciliation results not found:\n"
        f"{INPUT_FILE}\n"
        "\nRun reconcile.py before exception_classifier.py."
    )


df = pd.read_csv(INPUT_FILE)


print("============================================================")
print(" AI FINANCE CONTROLLER")
print(" STEP 7 — EXCEPTION CLASSIFICATION")
print("============================================================")

print(
    f"\nReconciliation records loaded: {len(df)}"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "invoice_id",
    "customer_id",
    "transaction_id",
    "status",
    "exception_type",
    "invoice_amount",
    "payment_amount",
    "gross_amount",
    "fee",
    "tax",
    "adjustment",
    "net_amount",
    "difference",
    "reason"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:

    raise ValueError(
        "\nMissing columns in reconciliation_results.csv:\n"
        + "\n".join(
            f" - {col}"
            for col in missing_columns
        )
    )


# ============================================================
# NORMALIZE TEXT FIELDS
# ============================================================

df["exception_type"] = (
    df["exception_type"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

df["status"] = (
    df["status"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# HELPER — CHECK MISSING TRANSACTION ID
# ============================================================

def transaction_id_missing(value):

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


# ============================================================
# EXCEPTION CLASSIFICATION FUNCTION
# ============================================================

def classify_exception(row):

    exception_type = row["exception_type"]

    transaction_missing = transaction_id_missing(
        row["transaction_id"]
    )


    # ========================================================
    # 1. MISSING TRANSACTION ID
    # ========================================================
    #
    # IMPORTANT:
    # Do NOT remove this record.
    #
    # The invoice may still be valid while the payment
    # transaction identifier is unavailable.
    #
    # Such a record cannot safely enter the normal AI
    # transaction-processing flow.
    #
    # Therefore:
    #
    # INVALID_TRANSACTION_ID
    #       ↓
    # CRITICAL
    #       ↓
    # HUMAN_REVIEW
    #
    # ========================================================

    if transaction_missing:

        return pd.Series([
            "INVALID_TRANSACTION_ID",
            "CRITICAL",
            "Human review required because transaction ID is missing."
        ])


    # ========================================================
    # 2. NO EXCEPTION
    # ========================================================

    if exception_type in {
        "",
        "NONE"
    }:

        return pd.Series([
            "NO_EXCEPTION",
            "LOW",
            "No action required."
        ])


    # ========================================================
    # 3. MISSING PAYMENT
    # ========================================================

    if exception_type == "MISSING_PAYMENT":

        return pd.Series([
            "PAYMENT_MISSING",
            "HIGH",
            "Investigate payment source."
        ])


    # ========================================================
    # 4. AMOUNT MISMATCH
    # ========================================================

    if exception_type == "AMOUNT_MISMATCH":

        return pd.Series([
            "AMOUNT_DISCREPANCY",
            "HIGH",
            "Verify invoice and payment amounts."
        ])


    # ========================================================
    # 5. MISSING SETTLEMENT
    # ========================================================

    if exception_type == "MISSING_SETTLEMENT":

        return pd.Series([
            "SETTLEMENT_MISSING",
            "HIGH",
            "Check payment gateway settlement."
        ])


    # ========================================================
    # 6. DUPLICATE PAYMENT
    # ========================================================

    if exception_type == "DUPLICATE_PAYMENT":

        return pd.Series([
            "DUPLICATE_TRANSACTION",
            "CRITICAL",
            "Investigate possible duplicate payment."
        ])


    # ========================================================
    # 7. GROSS AMOUNT MISMATCH
    # ========================================================

    if exception_type == "GROSS_AMOUNT_MISMATCH":

        return pd.Series([
            "SETTLEMENT_AMOUNT_DISCREPANCY",
            "HIGH",
            "Compare payment and gateway gross amount."
        ])


    # ========================================================
    # 8. SETTLEMENT CALCULATION ERROR
    # ========================================================

    if exception_type == "SETTLEMENT_CALCULATION_ERROR":

        return pd.Series([
            "SETTLEMENT_CALCULATION",
            "HIGH",
            "Verify fee, tax and adjustment calculation."
        ])


    # ========================================================
    # 9. DATE MISMATCH
    # ========================================================

    if exception_type == "DATE_MISMATCH":

        return pd.Series([
            "SETTLEMENT_DELAY",
            "MEDIUM",
            "Investigate settlement processing delay."
        ])


    # ========================================================
    # 10. INVALID PAYMENT AMOUNT
    # ========================================================

    if exception_type == "INVALID_PAYMENT_AMOUNT":

        return pd.Series([
            "INVALID_PAYMENT_DATA",
            "HIGH",
            "Verify payment record."
        ])


    # ========================================================
    # 11. UNKNOWN EXCEPTION
    # ========================================================

    return pd.Series([
        "UNKNOWN_EXCEPTION",
        "MEDIUM",
        "Manual investigation required."
    ])


# ============================================================
# APPLY CLASSIFICATION
# ============================================================

df[
    [
        "exception_category",
        "priority",
        "recommended_action"
    ]
] = df.apply(
    classify_exception,
    axis=1
)


# ============================================================
# ADD ROUTING HINT
# ============================================================
#
# This is NOT the final router decision.
# It simply gives the next stage useful information.
#
# INVALID_TRANSACTION_ID → HUMAN_REVIEW
# Other exceptions       → router decides
#
# ============================================================

df["routing_hint"] = "ROUTER_DECISION"

df.loc[
    df["exception_category"]
    == "INVALID_TRANSACTION_ID",
    "routing_hint"
] = "HUMAN_REVIEW"


# ============================================================
# ADD DATA INTEGRITY FLAG
# ============================================================

df["data_integrity_status"] = "VALID"

df.loc[
    df["exception_category"]
    == "INVALID_TRANSACTION_ID",
    "data_integrity_status"
] = "INVALID_TRANSACTION_ID"


# ============================================================
# SAVE CLASSIFIED RESULTS
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("\n============================================================")
print(" EXCEPTION CLASSIFICATION COMPLETE")
print("============================================================")


print(
    f"\nTotal records: {len(df)}"
)


# ============================================================
# TRANSACTION ID STATUS
# ============================================================

missing_transaction_count = df[
    "transaction_id"
].apply(
    transaction_id_missing
).sum()

valid_transaction_count = (
    len(df)
    - missing_transaction_count
)


print("\nTransaction ID status:")

print(
    f"Valid transaction IDs   : "
    f"{valid_transaction_count}"
)

print(
    f"Missing transaction IDs : "
    f"{missing_transaction_count}"
)


# ============================================================
# EXCEPTION CATEGORIES
# ============================================================

print("\nException Categories:")

print(
    df[
        "exception_category"
    ].value_counts()
)


# ============================================================
# PRIORITY DISTRIBUTION
# ============================================================

print("\nPriority Distribution:")

print(
    df[
        "priority"
    ].value_counts()
)


# ============================================================
# ROUTING HINT DISTRIBUTION
# ============================================================

print("\nRouting Hints:")

print(
    df[
        "routing_hint"
    ].value_counts()
)


# ============================================================
# SHOW INVALID TRANSACTION RECORDS
# ============================================================

invalid_records = df[
    df["exception_category"]
    == "INVALID_TRANSACTION_ID"
]

print(
    "\n============================================================"
)

print(
    " RECORDS WITH MISSING TRANSACTION ID"
)

print(
    "============================================================"
)

if invalid_records.empty:

    print(
        "No missing transaction IDs detected."
    )

else:

    display_columns = [
        "invoice_id",
        "customer_id",
        "transaction_id",
        "status",
        "exception_type",
        "exception_category",
        "priority",
        "recommended_action",
        "routing_hint"
    ]

    print(
        invalid_records[
            display_columns
        ].to_string(index=False)
    )


# ============================================================
# SAMPLE CLASSIFIED RECORDS
# ============================================================

print(
    "\n============================================================"
)

print(
    " SAMPLE CLASSIFIED RECORDS"
)

print(
    "============================================================"
)

sample_columns = [
    "invoice_id",
    "customer_id",
    "transaction_id",
    "status",
    "exception_type",
    "exception_category",
    "priority",
    "recommended_action",
    "routing_hint"
]

print(
    df[
        sample_columns
    ].head(10).to_string(index=False)
)


# ============================================================
# OUTPUT
# ============================================================

print(
    "\nOutput saved to:"
)

print(
    OUTPUT_FILE
)


print(
    "\n============================================================"
)

print(
    " STEP 7 COMPLETED"
)

print(
    "============================================================"
)
