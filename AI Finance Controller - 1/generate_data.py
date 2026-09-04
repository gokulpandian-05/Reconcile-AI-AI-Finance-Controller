
import pandas as pd
import random
import os
from datetime import datetime, timedelta

# ============================================================
# AI FINANCE CONTROLLER
# SYNTHETIC DATA GENERATOR
# STEP 21 - 70 RECORD QUOTA-SAFE DATASET
# ============================================================

# -----------------------------
# SETTINGS
# -----------------------------

NUM_RECORDS = 70
EXCEPTION_COUNT = 12

random.seed(42)

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# VALIDATION
# -----------------------------

if EXCEPTION_COUNT >= NUM_RECORDS:
    raise ValueError(
        "EXCEPTION_COUNT must be smaller than NUM_RECORDS."
    )

# -----------------------------
# HELPER DATA
# -----------------------------

payment_methods = [
    "UPI",
    "Card",
    "NetBanking",
    "Wallet"
]

start_date = datetime(2026, 8, 1)

# -----------------------------
# DATA CONTAINERS
# -----------------------------

invoices = []
payments = []
settlements = []
ground_truth = []

# ============================================================
# FIXED EXCEPTION PLAN
# ============================================================
#
# Total transactions = 70
#
# Normal records            = 58
# Amount mismatch            = 3
# Missing settlement         = 3
# Missing payment            = 2
# Duplicate transaction      = 1
# Date mismatch              = 1
# Fee difference             = 2
#
# Total exceptions = 12
#
# Maximum possible AI-required records = 12
# Maximum possible Gemini requests     = 12
#
# This keeps the run below the 20-request
# Gemini free-tier request limit.
# ============================================================

exception_plan = (
    ["amount_mismatch"] * 3
    + ["missing_settlement"] * 3
    + ["missing_payment"] * 2
    + ["duplicate_transaction"] * 1
    + ["date_mismatch"] * 1
    + ["fee_difference"] * 2
)

if len(exception_plan) != EXCEPTION_COUNT:
    raise ValueError(
        "Exception plan count does not match EXCEPTION_COUNT."
    )

# Shuffle the exception locations so the exceptions
# are distributed throughout the dataset.

random.shuffle(exception_plan)

scenario_plan = (
    ["normal"] * (NUM_RECORDS - EXCEPTION_COUNT)
    + exception_plan
)

random.shuffle(scenario_plan)

# ============================================================
# GENERATE DATA
# ============================================================

for i in range(1, NUM_RECORDS + 1):

    invoice_id = f"INV{i:04d}"
    transaction_id = f"TX{i:04d}"
    settlement_id = f"SET{i:04d}"
    customer_id = f"C{i:04d}"

    # -----------------------------
    # INVOICE
    # -----------------------------

    invoice_amount = random.choice([
        1200,
        1500,
        2000,
        2500,
        3000,
        4500,
        5000,
        7500,
        10000,
        15000,
        20000,
        25000
    ])

    invoice_date = (
        start_date
        + timedelta(days=random.randint(0, 20))
    )

    payment_date = (
        invoice_date
        + timedelta(days=random.randint(0, 3))
    )

    settlement_date = (
        payment_date
        + timedelta(days=random.randint(1, 3))
    )

    payment_amount = invoice_amount

    # -----------------------------
    # NORMAL GATEWAY FEE
    # -----------------------------

    fee = round(
        payment_amount * 0.02,
        2
    )

    tax = round(
        fee * 0.18,
        2
    )

    adjustment = 0

    net_amount = round(
        payment_amount
        - fee
        - tax
        + adjustment,
        2
    )

    # -----------------------------
    # DEFAULT STATUS
    # -----------------------------

    status = "MATCHED"
    exception_type = "NONE"

    scenario = scenario_plan[i - 1]

    # ========================================================
    # INTENTIONAL EXCEPTIONS
    # ========================================================

    # -----------------------------
    # AMOUNT MISMATCH
    # -----------------------------

    if scenario == "amount_mismatch":

        payment_amount = (
            invoice_amount
            - random.choice([
                100,
                250,
                500,
                750
            ])
        )

        # Recalculate settlement values
        fee = round(
            payment_amount * 0.02,
            2
        )

        tax = round(
            fee * 0.18,
            2
        )

        net_amount = round(
            payment_amount
            - fee
            - tax
            + adjustment,
            2
        )

        status = "EXCEPTION"
        exception_type = "AMOUNT_MISMATCH"

    # -----------------------------
    # MISSING SETTLEMENT
    # -----------------------------

    elif scenario == "missing_settlement":

        status = "EXCEPTION"
        exception_type = "MISSING_SETTLEMENT"

    # -----------------------------
    # MISSING PAYMENT
    # -----------------------------

    elif scenario == "missing_payment":

        payment_amount = None

        status = "EXCEPTION"
        exception_type = "MISSING_PAYMENT"

    # -----------------------------
    # DUPLICATE TRANSACTION
    # -----------------------------

    elif scenario == "duplicate_transaction":

        status = "EXCEPTION"
        exception_type = "DUPLICATE_TRANSACTION"

    # -----------------------------
    # DATE MISMATCH
    # -----------------------------

    elif scenario == "date_mismatch":

        settlement_date = (
            payment_date
            + timedelta(days=15)
        )

        status = "EXCEPTION"
        exception_type = "DATE_MISMATCH"

    # -----------------------------
    # FEE DIFFERENCE
    # -----------------------------

    elif scenario == "fee_difference":

        fee = round(
            payment_amount * 0.04,
            2
        )

        tax = round(
            fee * 0.18,
            2
        )

        net_amount = round(
            payment_amount
            - fee
            - tax
            + adjustment,
            2
        )

        status = "EXCEPTION"
        exception_type = "FEE_DIFFERENCE"

    # ========================================================
    # INVOICE DATA
    # ========================================================

    invoices.append({

        "invoice_id":
            invoice_id,

        "customer_id":
            customer_id,

        "invoice_amount":
            invoice_amount,

        "invoice_date":
            invoice_date.strftime("%Y-%m-%d"),

        "due_date":
            (
                invoice_date
                + timedelta(days=7)
            ).strftime("%Y-%m-%d"),

        "status":
            "ISSUED"
    })

    # ========================================================
    # PAYMENT DATA
    # ========================================================

    if scenario != "missing_payment":

        payments.append({

            "transaction_id":
                transaction_id,

            "invoice_id":
                invoice_id,

            "customer_id":
                customer_id,

            "payment_amount":
                payment_amount,

            "payment_date":
                payment_date.strftime("%Y-%m-%d"),

            "payment_method":
                random.choice(payment_methods),

            "status":
                "SUCCESS"
        })

    # ========================================================
    # SETTLEMENT DATA
    # ========================================================

    if scenario != "missing_settlement":

        settlements.append({

            "settlement_id":
                settlement_id,

            "transaction_id":
                transaction_id,

            "gross_amount":
                payment_amount,

            "fee":
                fee,

            "tax":
                tax,

            "adjustment":
                adjustment,

            "net_amount":
                net_amount,

            "settlement_date":
                settlement_date.strftime("%Y-%m-%d"),

            "status":
                "SETTLED"
        })

    # ========================================================
    # DUPLICATE TRANSACTION
    # ========================================================

    if scenario == "duplicate_transaction":

        payments.append({

            "transaction_id":
                transaction_id,

            "invoice_id":
                invoice_id,

            "customer_id":
                customer_id,

            "payment_amount":
                payment_amount,

            "payment_date":
                payment_date.strftime("%Y-%m-%d"),

            "payment_method":
                random.choice(payment_methods),

            "status":
                "SUCCESS"
        })

    # ========================================================
    # GROUND TRUTH
    # ========================================================

    ground_truth.append({

        "transaction_id":
            transaction_id,

        "invoice_id":
            invoice_id,

        "expected_status":
            status,

        "exception_type":
            exception_type
    })


# ============================================================
# CREATE DATAFRAMES
# ============================================================

invoice_df = pd.DataFrame(
    invoices
)

payment_df = pd.DataFrame(
    payments
)

settlement_df = pd.DataFrame(
    settlements
)

ground_truth_df = pd.DataFrame(
    ground_truth
)


# ============================================================
# FINAL VALIDATION
# ============================================================

actual_total = len(ground_truth_df)

actual_exceptions = len(
    ground_truth_df[
        ground_truth_df["exception_type"] != "NONE"
    ]
)

actual_normal = len(
    ground_truth_df[
        ground_truth_df["exception_type"] == "NONE"
    ]
)

if actual_total != NUM_RECORDS:

    raise RuntimeError(
        f"Expected {NUM_RECORDS} records, "
        f"but generated {actual_total}."
    )

if actual_exceptions != EXCEPTION_COUNT:

    raise RuntimeError(
        f"Expected {EXCEPTION_COUNT} exceptions, "
        f"but generated {actual_exceptions}."
    )

if actual_normal != (
    NUM_RECORDS - EXCEPTION_COUNT
):

    raise RuntimeError(
        "Normal record count is incorrect."
    )


# ============================================================
# SAVE CSV FILES
# ============================================================

invoice_df.to_csv(
    f"{OUTPUT_DIR}/invoices.csv",
    index=False
)

payment_df.to_csv(
    f"{OUTPUT_DIR}/payments.csv",
    index=False
)

settlement_df.to_csv(
    f"{OUTPUT_DIR}/settlements.csv",
    index=False
)

ground_truth_df.to_csv(
    f"{OUTPUT_DIR}/ground_truth.csv",
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 55)
print(" SYNTHETIC DATA GENERATION COMPLETE")
print("=" * 55)

print()

print(
    f"Invoice records      : "
    f"{len(invoice_df)}"
)

print(
    f"Payment records      : "
    f"{len(payment_df)}"
)

print(
    f"Settlement records   : "
    f"{len(settlement_df)}"
)

print(
    f"Ground truth records : "
    f"{len(ground_truth_df)}"
)

print()
print("Dataset composition:")

print(
    f"Total transactions   : "
    f"{actual_total}"
)

print(
    f"Normal records       : "
    f"{actual_normal}"
)

print(
    f"Exception records    : "
    f"{actual_exceptions}"
)

print()
print("Exception distribution:")

print(
    ground_truth_df[
        ground_truth_df["exception_type"] != "NONE"
    ]["exception_type"]
    .value_counts()
    .to_string()
)

print()
print("Ground-truth status distribution:")

print(
    ground_truth_df[
        "expected_status"
    ]
    .value_counts()
    .to_string()
)

print()
print("Files created:")

print("✓ data/invoices.csv")
print("✓ data/payments.csv")
print("✓ data/settlements.csv")
print("✓ data/ground_truth.csv")

print()
print("=" * 55)
print(" GEMINI QUOTA SAFETY")
print("=" * 55)

print(
    f"Maximum AI-required records : "
    f"{actual_exceptions}"
)

print(
    f"Maximum Gemini requests     : "
    f"{actual_exceptions}"
)

print(
    "Gemini free-tier target     : "
    "20 requests"
)

print(
    "Remaining request headroom  : "
    f"{20 - actual_exceptions}"
)

print("=" * 55)

print()
print("Ready for Phase 2: Data Ingestion.")