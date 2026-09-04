import pandas as pd
import os

# ==========================================
# STEP 6 - DETERMINISTIC RECONCILIATION
# ==========================================

DATA_DIR = r"C:\Users\pandi\Desktop\AI Finance Controller\data"

# ------------------------------------------
# LOAD NORMALIZED DATA
# ------------------------------------------

invoices = pd.read_csv(
    os.path.join(DATA_DIR, "invoices_normalized.csv")
)

payments = pd.read_csv(
    os.path.join(DATA_DIR, "payments_normalized.csv")
)

settlements = pd.read_csv(
    os.path.join(DATA_DIR, "settlements_normalized.csv")
)

# Convert dates
invoices["invoice_date"] = pd.to_datetime(
    invoices["invoice_date"],
    errors="coerce"
)

payments["payment_date"] = pd.to_datetime(
    payments["payment_date"],
    errors="coerce"
)

settlements["settlement_date"] = pd.to_datetime(
    settlements["settlement_date"],
    errors="coerce"
)

# ==========================================
# RECONCILIATION
# ==========================================

results = []

for _, invoice in invoices.iterrows():

    invoice_id = invoice["invoice_id"]
    customer_id = invoice["customer_id"]
    invoice_amount = invoice["invoice_amount"]

    # --------------------------------------
    # 1. FIND PAYMENT
    # --------------------------------------

    payment_rows = payments[
        payments["invoice_id"] == invoice_id
    ]

    if payment_rows.empty:

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": None,
            "status": "EXCEPTION",
            "exception_type": "MISSING_PAYMENT",
            "invoice_amount": invoice_amount,
            "payment_amount": None,
            "gross_amount": None,
            "fee": None,
            "tax": None,
            "adjustment": None,
            "net_amount": None,
            "difference": None,
            "reason": "No payment found for invoice."
        })

        continue

    # --------------------------------------
    # 2. CHECK DUPLICATE PAYMENTS
    # --------------------------------------

    if len(payment_rows) > 1:

        transaction_id = payment_rows.iloc[0]["transaction_id"]

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "DUPLICATE_PAYMENT",
            "invoice_amount": invoice_amount,
            "payment_amount": payment_rows["payment_amount"].sum(),
            "gross_amount": None,
            "fee": None,
            "tax": None,
            "adjustment": None,
            "net_amount": None,
            "difference": None,
            "reason": "Multiple payments found for the same invoice."
        })

        continue

    payment = payment_rows.iloc[0]

    transaction_id = payment["transaction_id"]
    payment_amount = payment["payment_amount"]

    # --------------------------------------
    # 3. CHECK PAYMENT AMOUNT
    # --------------------------------------

    if pd.isna(payment_amount):

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "INVALID_PAYMENT_AMOUNT",
            "invoice_amount": invoice_amount,
            "payment_amount": None,
            "gross_amount": None,
            "fee": None,
            "tax": None,
            "adjustment": None,
            "net_amount": None,
            "difference": None,
            "reason": "Payment amount is missing."
        })

        continue

    # --------------------------------------
    # 4. INVOICE VS PAYMENT
    # --------------------------------------

    invoice_payment_difference = round(
        invoice_amount - payment_amount,
        2
    )

    if invoice_payment_difference != 0:

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "AMOUNT_MISMATCH",
            "invoice_amount": invoice_amount,
            "payment_amount": payment_amount,
            "gross_amount": None,
            "fee": None,
            "tax": None,
            "adjustment": None,
            "net_amount": None,
            "difference": invoice_payment_difference,
            "reason": (
                f"Invoice amount ₹{invoice_amount:.2f} "
                f"does not match payment amount "
                f"₹{payment_amount:.2f}."
            )
        })

        continue

    # --------------------------------------
    # 5. FIND SETTLEMENT
    # --------------------------------------

    settlement_rows = settlements[
        settlements["transaction_id"] == transaction_id
    ]

    if settlement_rows.empty:

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "MISSING_SETTLEMENT",
            "invoice_amount": invoice_amount,
            "payment_amount": payment_amount,
            "gross_amount": None,
            "fee": None,
            "tax": None,
            "adjustment": None,
            "net_amount": None,
            "difference": None,
            "reason": "No settlement found for payment."
        })

        continue

    settlement = settlement_rows.iloc[0]

    gross_amount = settlement["gross_amount"]
    fee = settlement["fee"]
    tax = settlement["tax"]
    adjustment = settlement["adjustment"]
    net_amount = settlement["net_amount"]

    # --------------------------------------
    # 6. PAYMENT VS GROSS AMOUNT
    # --------------------------------------

    gross_difference = round(
        payment_amount - gross_amount,
        2
    )

    if gross_difference != 0:

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "GROSS_AMOUNT_MISMATCH",
            "invoice_amount": invoice_amount,
            "payment_amount": payment_amount,
            "gross_amount": gross_amount,
            "fee": fee,
            "tax": tax,
            "adjustment": adjustment,
            "net_amount": net_amount,
            "difference": gross_difference,
            "reason": (
                f"Payment amount ₹{payment_amount:.2f} "
                f"does not match settlement gross amount "
                f"₹{gross_amount:.2f}."
            )
        })

        continue

    # --------------------------------------
    # 7. VERIFY SETTLEMENT CALCULATION
    # --------------------------------------

    expected_net_amount = round(
        gross_amount - fee - tax + adjustment,
        2
    )

    settlement_difference = round(
        expected_net_amount - net_amount,
        2
    )

    if settlement_difference != 0:

        results.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "status": "EXCEPTION",
            "exception_type": "SETTLEMENT_CALCULATION_ERROR",
            "invoice_amount": invoice_amount,
            "payment_amount": payment_amount,
            "gross_amount": gross_amount,
            "fee": fee,
            "tax": tax,
            "adjustment": adjustment,
            "net_amount": net_amount,
            "difference": settlement_difference,
            "reason": (
                f"Expected net settlement ₹{expected_net_amount:.2f}, "
                f"but recorded net settlement is "
                f"₹{net_amount:.2f}."
            )
        })

        continue

    # --------------------------------------
    # 8. CHECK SETTLEMENT DATE
    # --------------------------------------

    payment_date = payment["payment_date"]
    settlement_date = settlement["settlement_date"]

    if pd.notna(payment_date) and pd.notna(settlement_date):

        days_difference = (
            settlement_date - payment_date
        ).days

        if days_difference > 7:

            results.append({
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "transaction_id": transaction_id,
                "status": "EXCEPTION",
                "exception_type": "DATE_MISMATCH",
                "invoice_amount": invoice_amount,
                "payment_amount": payment_amount,
                "gross_amount": gross_amount,
                "fee": fee,
                "tax": tax,
                "adjustment": adjustment,
                "net_amount": net_amount,
                "difference": None,
                "reason": (
                    f"Settlement occurred {days_difference} "
                    f"days after payment."
                )
            })

            continue

    # --------------------------------------
    # 9. EVERYTHING MATCHES
    # --------------------------------------

    results.append({
        "invoice_id": invoice_id,
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "status": "MATCHED",
        "exception_type": "NONE",
        "invoice_amount": invoice_amount,
        "payment_amount": payment_amount,
        "gross_amount": gross_amount,
        "fee": fee,
        "tax": tax,
        "adjustment": adjustment,
        "net_amount": net_amount,
        "difference": 0,
        "reason": (
            "Invoice, payment and settlement "
            "records are consistent."
        )
    })


# ==========================================
# CREATE RESULT DATAFRAME
# ==========================================

results_df = pd.DataFrame(results)

# ==========================================
# SAVE RESULTS
# ==========================================

output_file = os.path.join(
    DATA_DIR,
    "reconciliation_results.csv"
)

results_df.to_csv(
    output_file,
    index=False
)

# ==========================================
# DISPLAY SUMMARY
# ==========================================

print("\n==========================================")
print(" DETERMINISTIC RECONCILIATION COMPLETE")
print("==========================================")

print("\nTotal records:", len(results_df))

print("\nStatus:")
print(
    results_df["status"].value_counts()
)

print("\nException types:")
print(
    results_df["exception_type"].value_counts()
)

print("\nOutput file:")
print(output_file)

print("\nSample results:")
print(
    results_df.head(10).to_string(index=False)
)