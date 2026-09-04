
import sqlite3
import os
from datetime import datetime


# ============================================================
# AI FINANCE CONTROLLER
# DATABASE MODULE
# STEP 17 - RESULT STORAGE
# ============================================================


# ============================================================
# PATH CONFIGURATION
# ============================================================

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "data"
)

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(
    DATA_DIR,
    "finance_controller.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Create the reconciliation_results table if it does not exist.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_results (

                result_id INTEGER PRIMARY KEY AUTOINCREMENT,

                transaction_id TEXT NOT NULL UNIQUE,

                exception_type TEXT,

                final_status TEXT,

                final_action TEXT,

                ai_confidence REAL DEFAULT 0.0,

                ai_override INTEGER DEFAULT 0,

                ai_attempts INTEGER DEFAULT 0,

                ai_explanation TEXT,

                created_at TEXT,

                updated_at TEXT

            )
        """)

        conn.commit()

    finally:

        conn.close()

    print("SQLite database initialized:")
    print(DB_PATH)


# ============================================================
# SAVE / UPDATE RECONCILIATION RESULT
# ============================================================

def save_reconciliation_result(
    transaction_id,
    exception_type=None,
    final_status="UNRESOLVED",
    final_action="HUMAN_REVIEW",
    ai_confidence=0.0,
    ai_override=False,
    ai_attempts=0,
    ai_explanation=""
):
    """
    Save a reconciliation result.

    Existing transaction_id:
        UPDATE

    New transaction_id:
        INSERT

    IMPORTANT:
    The transaction_id supplied by the reconciliation pipeline
    must be the original benchmark transaction ID.

    Do NOT pass values such as:

        INVOICE:INV0002
        INVOICE:INV0048

    as replacement transaction IDs.
    """

    if transaction_id is None:
        raise ValueError(
            "transaction_id cannot be None."
        )

    transaction_id = str(
        transaction_id
    ).strip()

    if not transaction_id:
        raise ValueError(
            "transaction_id cannot be empty."
        )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Check existing transaction
        # ----------------------------------------------------

        cursor.execute("""
            SELECT result_id
            FROM reconciliation_results
            WHERE transaction_id = ?
        """, (
            transaction_id,
        ))

        existing = cursor.fetchone()

        confidence = float(
            ai_confidence
            if ai_confidence is not None
            else 0.0
        )

        override = int(
            bool(ai_override)
        )

        attempts = int(
            ai_attempts
            if ai_attempts is not None
            else 0
        )

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        if existing:

            cursor.execute("""
                UPDATE reconciliation_results

                SET
                    exception_type = ?,
                    final_status = ?,
                    final_action = ?,
                    ai_confidence = ?,
                    ai_override = ?,
                    ai_attempts = ?,
                    ai_explanation = ?,
                    updated_at = ?

                WHERE transaction_id = ?
            """, (

                exception_type,

                final_status,

                final_action,

                confidence,

                override,

                attempts,

                ai_explanation,

                now,

                transaction_id
            ))

            print(
                f"Database result updated: "
                f"{transaction_id}"
            )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        else:

            cursor.execute("""
                INSERT INTO reconciliation_results (

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

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                transaction_id,

                exception_type,

                final_status,

                final_action,

                confidence,

                override,

                attempts,

                ai_explanation,

                now,

                now
            ))

            print(
                f"Database result saved: "
                f"{transaction_id}"
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# GET ONE RESULT
# ============================================================

def get_reconciliation_result(
    transaction_id
):
    """
    Retrieve one transaction result.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
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

            WHERE transaction_id = ?
        """, (
            transaction_id,
        ))

        row = cursor.fetchone()

    finally:

        conn.close()

    if row is None:
        return None

    return dict(row)


# ============================================================
# SHOW ALL RESULTS
# ============================================================

def show_reconciliation_results():
    """
    Display all stored reconciliation results.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
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
        """)

        rows = cursor.fetchall()

    finally:

        conn.close()

    print()
    print("=" * 42)
    print(" STORED RECONCILIATION RESULTS")
    print("=" * 42)

    if not rows:

        print("No reconciliation results found.")

        return

    for row in rows:

        print()
        print(
            f"Result ID       : "
            f"{row['result_id']}"
        )

        print(
            f"Transaction ID  : "
            f"{row['transaction_id']}"
        )

        print(
            f"Exception       : "
            f"{row['exception_type']}"
        )

        print(
            f"Final Status    : "
            f"{row['final_status']}"
        )

        print(
            f"Final Action    : "
            f"{row['final_action']}"
        )

        print(
            f"AI Confidence   : "
            f"{row['ai_confidence']}"
        )

        print(
            f"AI Override     : "
            f"{row['ai_override']}"
        )

        print(
            f"AI Attempts     : "
            f"{row['ai_attempts']}"
        )

        print(
            f"Explanation     : "
            f"{row['ai_explanation']}"
        )

        print(
            f"Created         : "
            f"{row['created_at']}"
        )

        print(
            f"Updated         : "
            f"{row['updated_at']}"
        )

        print("-" * 42)


# ============================================================
# DATABASE SUMMARY
# ============================================================

def show_database_summary():
    """
    Display useful database-level metrics.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Total records
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM reconciliation_results
        """)

        total = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Status counts
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                final_status,
                COUNT(*) AS count

            FROM reconciliation_results

            GROUP BY final_status
        """)

        status_rows = cursor.fetchall()

        # ----------------------------------------------------
        # AI attempts
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM reconciliation_results
            WHERE ai_attempts > 0
        """)

        ai_requests = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Human review
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM reconciliation_results
            WHERE final_action = 'HUMAN_REVIEW'
        """)

        human_review = cursor.fetchone()[0]

    finally:

        conn.close()

    print()
    print("=" * 42)
    print(" DATABASE SUMMARY")
    print("=" * 42)

    print(
        f"Total stored results : {total}"
    )

    print(
        f"Gemini/AI attempts   : {ai_requests}"
    )

    print(
        f"Human review         : {human_review}"
    )

    print()
    print("Final status:")

    if status_rows:

        for row in status_rows:

            print(
                f"{row['final_status']}: "
                f"{row['count']}"
            )

    else:

        print("No status records.")


# ============================================================
# DELETE ONE TRANSACTION
# ============================================================

def delete_transaction(
    transaction_id
):
    """
    Delete one transaction.

    Development/testing utility only.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM reconciliation_results
            WHERE transaction_id = ?
        """, (
            transaction_id,
        ))

        deleted = cursor.rowcount

        conn.commit()

    finally:

        conn.close()

    if deleted:

        print(
            f"Deleted database record: "
            f"{transaction_id}"
        )

    else:

        print(
            f"No database record found: "
            f"{transaction_id}"
        )


# ============================================================
# CLEAR ALL RESULTS
# ============================================================

def clear_results():
    """
    Delete ALL reconciliation results.

    Use this before running a fresh 70-record benchmark.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM reconciliation_results
        """)

        deleted = cursor.rowcount

        conn.commit()

    finally:

        conn.close()

    print(
        f"Cleared {deleted} database records."
    )


# ============================================================
# DATABASE VALIDATION
# ============================================================

def validate_database_count(
    expected_count=70
):
    """
    Validate that the database contains exactly the
    expected number of benchmark results.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM reconciliation_results
        """)

        count = cursor.fetchone()[0]

    finally:

        conn.close()

    print()
    print("=" * 42)
    print(" DATABASE VALIDATION")
    print("=" * 42)

    print(
        f"Expected records : {expected_count}"
    )

    print(
        f"Actual records   : {count}"
    )

    if count == expected_count:

        print(
            "STATUS           : PASS"
        )

        return True

    print(
        "STATUS           : FAIL"
    )

    print(
        f"Difference       : "
        f"{count - expected_count}"
    )

    return False


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 42)
    print(" AI FINANCE CONTROLLER DATABASE")
    print("=" * 42)

    initialize_database()

    print()
    print(
        "Database module initialized successfully."
    )

    print(
        "No test transaction was inserted."
    )

    print(
        "Run clear_results() before a fresh benchmark."
    )

    show_database_summary()