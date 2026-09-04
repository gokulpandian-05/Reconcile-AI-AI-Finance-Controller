import pandas as pd
import os

# -----------------------------
# PATHS
# -----------------------------

DATA_DIR = "./data"

invoice_file = os.path.join(DATA_DIR, "invoices.csv")
payment_file = os.path.join(DATA_DIR, "payments.csv")
settlement_file = os.path.join(DATA_DIR, "settlements.csv")

# -----------------------------
# LOAD DATA
# -----------------------------

invoices = pd.read_csv(invoice_file)
payments = pd.read_csv(payment_file)
settlements = pd.read_csv(settlement_file)

print("CSV files loaded successfully.")

# -----------------------------
# NORMALIZE INVOICE DATA
# -----------------------------

invoices["invoice_id"] = (
    invoices["invoice_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

invoices["customer_id"] = (
    invoices["customer_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

invoices["invoice_amount"] = pd.to_numeric(
    invoices["invoice_amount"],
    errors="coerce"
).round(2)

invoices["invoice_date"] = pd.to_datetime(
    invoices["invoice_date"],
    errors="coerce"
)

invoices["due_date"] = pd.to_datetime(
    invoices["due_date"],
    errors="coerce"
)

invoices["status"] = (
    invoices["status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# -----------------------------
# NORMALIZE PAYMENT DATA
# -----------------------------

payments["transaction_id"] = (
    payments["transaction_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

payments["invoice_id"] = (
    payments["invoice_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

payments["customer_id"] = (
    payments["customer_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

payments["payment_amount"] = pd.to_numeric(
    payments["payment_amount"],
    errors="coerce"
).round(2)

payments["payment_date"] = pd.to_datetime(
    payments["payment_date"],
    errors="coerce"
)

payments["payment_method"] = (
    payments["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)

payments["status"] = (
    payments["status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# -----------------------------
# NORMALIZE SETTLEMENT DATA
# -----------------------------

settlements["settlement_id"] = (
    settlements["settlement_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

settlements["transaction_id"] = (
    settlements["transaction_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Normalize monetary columns
money_columns = [
    "gross_amount",
    "fee",
    "tax",
    "adjustment",
    "net_amount"
]

for column in money_columns:
    settlements[column] = pd.to_numeric(
        settlements[column],
        errors="coerce"
    ).round(2)

settlements["settlement_date"] = pd.to_datetime(
    settlements["settlement_date"],
    errors="coerce"
)

settlements["status"] = (
    settlements["status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# -----------------------------
# SAVE NORMALIZED DATA
# -----------------------------

invoices.to_csv(
    os.path.join(DATA_DIR, "invoices_normalized.csv"),
    index=False
)

payments.to_csv(
    os.path.join(DATA_DIR, "payments_normalized.csv"),
    index=False
)

settlements.to_csv(
    os.path.join(DATA_DIR, "settlements_normalized.csv"),
    index=False
)

# -----------------------------
# DISPLAY RESULTS
# -----------------------------

print("\n===== NORMALIZATION COMPLETE =====")

print("Invoices:", len(invoices))
print("Payments:", len(payments))
print("Settlements:", len(settlements))

print("\nNormalized files created:")
print("✓ invoices_normalized.csv")
print("✓ payments_normalized.csv")
print("✓ settlements_normalized.csv")

print("\n===== SAMPLE INVOICE DATA =====")
print(invoices.head())

print("\n===== SAMPLE PAYMENT DATA =====")
print(payments.head())

print("\n===== SAMPLE SETTLEMENT DATA =====")
print(settlements.head())