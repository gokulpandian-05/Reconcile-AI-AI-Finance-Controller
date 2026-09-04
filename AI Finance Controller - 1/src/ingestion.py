import pandas as pd
import os

# Path to data folder
DATA_DIR = r"C:\Users\pandi\Desktop\AI Finance Controller\data"

# CSV file paths
invoice_file = os.path.join(DATA_DIR, "invoices.csv")
payment_file = os.path.join(DATA_DIR, "payments.csv")
settlement_file = os.path.join(DATA_DIR, "settlements.csv")

# Load CSV files
invoices = pd.read_csv(invoice_file)
payments = pd.read_csv(payment_file)
settlements = pd.read_csv(settlement_file)

# Display basic information
print("\n===== INVOICE DATA =====")
print(invoices.head())

print("\n===== PAYMENT DATA =====")
print(payments.head())

print("\n===== SETTLEMENT DATA =====")
print(settlements.head())

# Display number of records
print("\n===== RECORD COUNTS =====")
print("Invoices:", len(invoices))
print("Payments:", len(payments))
print("Settlements:", len(settlements))