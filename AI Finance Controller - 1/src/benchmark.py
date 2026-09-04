
import os
import sqlite3
import time
import pandas as pd


# ============================================================
# AI FINANCE CONTROLLER
# STEP 21 - CONTROLLED EVALUATION / BENCHMARK
# ============================================================

print()
print("=" * 70)
print(" AI FINANCE CONTROLLER - STEP 21")
print(" CONTROLLED EVALUATION / BENCHMARK")
print("=" * 70)

print()
print("This benchmark evaluates existing database results")
print("against the ground-truth dataset.")
print()
print("Gemini is NOT called during benchmarking.")
print()


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

DB_PATH = os.path.join(
    DATA_DIR,
    "finance_controller.db"
)

GROUND_TRUTH_PATH = os.path.join(
    DATA_DIR,
    "ground_truth.csv"
)

RECONCILIATION_PATH = os.path.join(
    DATA_DIR,
    "reconciliation_results.csv"
)

FINAL_RESULTS_PATH = os.path.join(
    DATA_DIR,
    "final_results.csv"
)

BENCHMARK_PATH = os.path.join(
    DATA_DIR,
    "benchmark.csv"
)

BENCHMARK_DETAILS_PATH = os.path.join(
    DATA_DIR,
    "benchmark_details.csv"
)

BENCHMARK_SUMMARY_PATH = os.path.join(
    DATA_DIR,
    "benchmark_summary.txt"
)


# ============================================================
# STRING CLEANING
# ============================================================

def clean_string(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


# ============================================================
# NORMALIZE EXCEPTION TYPE
# ============================================================

def normalize_exception_type(value):

    value = clean_string(value).upper()

    aliases = {

        "MISSING_PAYMENT":
            "PAYMENT_MISSING",

        "PAYMENT_MISSING":
            "PAYMENT_MISSING",

        "MISSING_SETTLEMENT":
            "SETTLEMENT_MISSING",

        "SETTLEMENT_MISSING":
            "SETTLEMENT_MISSING",

        "AMOUNT_MISMATCH":
            "AMOUNT_DISCREPANCY",

        "AMOUNT_DISCREPANCY":
            "AMOUNT_DISCREPANCY",

        "DATE_MISMATCH":
            "SETTLEMENT_DELAY",

        "SETTLEMENT_DELAY":
            "SETTLEMENT_DELAY",

        "SETTLEMENT_AMOUNT_DISCREPANCY":
            "SETTLEMENT_AMOUNT_DISCREPANCY",

        "FEE_DIFFERENCE":
            "FEE_DIFFERENCE",

        "DUPLICATE_TRANSACTION":
            "DUPLICATE_TRANSACTION",

        "NO_EXCEPTION":
            "NO_EXCEPTION",

        "NONE":
            "NO_EXCEPTION",

        "MATCHED":
            "NO_EXCEPTION"
    }

    return aliases.get(
        value,
        value
    )


# ============================================================
# NORMALIZE FINAL DATABASE STATUS
#
# IMPORTANT:
#
# Ground truth uses business outcome:
#
# MATCHED
# EXCEPTION
#
# Database uses workflow status:
#
# RESOLVED
# UNRESOLVED
#
# Therefore we convert BOTH into one canonical benchmark
# vocabulary:
#
# MATCHED
# EXCEPTION
#
# ============================================================

def normalize_expected_status(value):

    value = clean_string(value).upper()

    aliases = {

        # Ground truth normal match
        "MATCHED":
            "MATCHED",

        "MATCH":
            "MATCHED",

        "RESOLVED":
            "MATCHED",

        "AI_RESOLVED":
            "MATCHED",

        # Ground truth exception
        "EXCEPTION":
            "EXCEPTION",

        "UNRESOLVED":
            "EXCEPTION",

        "HUMAN_REVIEW":
            "EXCEPTION",

        "PENDING":
            "EXCEPTION",

        "PENDING_AI_TEST":
            "EXCEPTION"
    }

    return aliases.get(
        value,
        value
    )


def normalize_result_status(
    final_status,
    final_action=""
):

    status = clean_string(
        final_status
    ).upper()

    action = clean_string(
        final_action
    ).upper()

    # --------------------------------------------------------
    # Database resolved result
    # --------------------------------------------------------

    if status in {
        "RESOLVED",
        "AI_RESOLVED",
        "MATCHED",
        "MATCH"
    }:

        return "MATCHED"

    # --------------------------------------------------------
    # Database unresolved / human review
    # --------------------------------------------------------

    if status in {
        "UNRESOLVED",
        "EXCEPTION",
        "PENDING",
        "PENDING_AI_TEST"
    }:

        return "EXCEPTION"

    # --------------------------------------------------------
    # Human review is always an exception outcome
    # --------------------------------------------------------

    if action == "HUMAN_REVIEW":

        return "EXCEPTION"

    return status


# ============================================================
# LOAD DATABASE RESULTS
# ============================================================

def load_database_results():

    if not os.path.exists(DB_PATH):

        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    conn = sqlite3.connect(
        DB_PATH
    )

    try:

        query = """
            SELECT
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
        """

        df = pd.read_sql_query(
            query,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

def load_ground_truth():

    if not os.path.exists(
        GROUND_TRUTH_PATH
    ):

        raise FileNotFoundError(
            f"Ground truth file not found:\n"
            f"{GROUND_TRUTH_PATH}"
        )

    df = pd.read_csv(
        GROUND_TRUTH_PATH
    )

    required_columns = [
        "transaction_id",
        "invoice_id",
        "expected_status",
        "exception_type"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Ground truth is missing columns:\n"
            + "\n".join(
                f" - {column}"
                for column in missing
            )
        )

    return df


# ============================================================
# LOAD RECONCILIATION RESULTS
# ============================================================

def load_reconciliation_results():

    if not os.path.exists(
        RECONCILIATION_PATH
    ):

        return pd.DataFrame()

    try:

        return pd.read_csv(
            RECONCILIATION_PATH
        )

    except Exception as error:

        print(
            "WARNING: Could not load "
            "reconciliation_results.csv"
        )

        print(error)

        return pd.DataFrame()


# ============================================================
# LOAD FINAL RESULTS
# ============================================================

def load_final_results():

    if not os.path.exists(
        FINAL_RESULTS_PATH
    ):

        return pd.DataFrame()

    try:

        return pd.read_csv(
            FINAL_RESULTS_PATH
        )

    except Exception as error:

        print(
            "WARNING: Could not load "
            "final_results.csv"
        )

        print(error)

        return pd.DataFrame()


# ============================================================
# BUILD TRANSACTION RESULT MAP
# ============================================================

def build_transaction_result_map(
    results
):

    result_map = {}

    if results is None:
        return result_map

    if results.empty:
        return result_map

    if "transaction_id" not in results.columns:
        return result_map

    for _, row in results.iterrows():

        transaction_id = clean_string(
            row.get(
                "transaction_id",
                ""
            )
        )

        if not transaction_id:
            continue

        result_map[
            transaction_id
        ] = row

    return result_map


# ============================================================
# BUILD INVOICE RESULT MAP
# ============================================================

def build_invoice_result_map(
    results
):

    result_map = {}

    if results is None:
        return result_map

    if results.empty:
        return result_map

    if "invoice_id" not in results.columns:
        return result_map

    for _, row in results.iterrows():

        invoice_id = clean_string(
            row.get(
                "invoice_id",
                ""
            )
        )

        if not invoice_id:
            continue

        result_map[
            invoice_id
        ] = row

    return result_map


# ============================================================
# FIND RESULT
#
# Priority:
#
# 1. transaction_id
# 2. invoice_id
#
# This specifically handles:
#
# TX0002 -> INV0002
# TX0048 -> INV0048
#
# where the database stores:
#
# INVOICE:INV0002
# INVOICE:INV0048
#
# ============================================================

def find_result(
    gt_transaction_id,
    gt_invoice_id,
    transaction_map,
    invoice_map
):

    gt_transaction_id = clean_string(
        gt_transaction_id
    )

    gt_invoice_id = clean_string(
        gt_invoice_id
    )

    # --------------------------------------------------------
    # 1. TRANSACTION ID
    # --------------------------------------------------------

    if gt_transaction_id:

        if gt_transaction_id in transaction_map:

            return (
                transaction_map[
                    gt_transaction_id
                ],
                "TRANSACTION_ID"
            )

    # --------------------------------------------------------
    # 2. INVOICE ID
    # --------------------------------------------------------

    if gt_invoice_id:

        if gt_invoice_id in invoice_map:

            return (
                invoice_map[
                    gt_invoice_id
                ],
                "INVOICE_ID"
            )

    # --------------------------------------------------------
    # 3. DATABASE SPECIAL FORMAT
    #
    # INVOICE:INV0002
    #
    # --------------------------------------------------------

    invoice_transaction_key = (
        "INVOICE:"
        + gt_invoice_id
    )

    if gt_invoice_id:

        if invoice_transaction_key in transaction_map:

            return (
                transaction_map[
                    invoice_transaction_key
                ],
                "INVOICE_TRANSACTION_ID"
            )

    return (
        None,
        "NO_MATCH"
    )


# ============================================================
# GET SAFE RESULT VALUE
# ============================================================

def get_result_value(
    result_row,
    column,
    default=""
):

    if result_row is None:

        return default

    if column not in result_row.index:

        return default

    value = result_row[column]

    try:

        if pd.isna(value):

            return default

    except Exception:

        pass

    return value


# ============================================================
# CLASSIFY DECISION TYPE
# ============================================================

def classify_decision(
    row
):

    final_action = clean_string(
        row.get(
            "final_action",
            ""
        )
    ).upper()

    final_status = normalize_result_status(
        row.get(
            "final_status",
            ""
        ),
        final_action
    )

    ai_attempts = pd.to_numeric(
        row.get(
            "ai_attempts",
            0
        ),
        errors="coerce"
    )

    if pd.isna(ai_attempts):

        ai_attempts = 0

    ai_override = pd.to_numeric(
        row.get(
            "ai_override",
            0
        ),
        errors="coerce"
    )

    if pd.isna(ai_override):

        ai_override = 0

    # --------------------------------------------------------
    # HUMAN REVIEW / FAILURE RECOVERY
    # --------------------------------------------------------

    if final_action == "HUMAN_REVIEW":

        if ai_override == 1:

            return "AI_FAILURE_RECOVERY"

        return "HUMAN_REVIEW"

    # --------------------------------------------------------
    # RULE BASED
    # --------------------------------------------------------

    if final_action == "RULE_BASED_RESOLUTION":

        return "RULE_BASED_RESOLUTION"

    # --------------------------------------------------------
    # AI RESOLVED
    # --------------------------------------------------------

    if (
        ai_attempts > 0
        and final_status == "MATCHED"
    ):

        return "AI_REASONING"

    # --------------------------------------------------------
    # AI UNRESOLVED
    # --------------------------------------------------------

    if ai_attempts > 0:

        return "AI_REASONING"

    # --------------------------------------------------------
    # DETERMINISTIC MATCH
    # --------------------------------------------------------

    if (
        final_status == "MATCHED"
        and
        final_action == "NO_ACTION"
        and
        ai_attempts == 0
    ):

        return "DETERMINISTIC_MATCH"

    return "OTHER"


# ============================================================
# DETERMINE WHETHER RESULT IS EVALUATED
# ============================================================

def is_evaluated(
    result_row
):

    if result_row is None:

        return False

    final_status = clean_string(
        result_row.get(
            "final_status",
            ""
        )
    ).upper()

    final_action = clean_string(
        result_row.get(
            "final_action",
            ""
        )
    ).upper()

    if final_status in {
        "RESOLVED",
        "UNRESOLVED",
        "MATCHED",
        "EXCEPTION",
        "AI_RESOLVED"
    }:

        return True

    if final_action == "HUMAN_REVIEW":

        return True

    return False


# ============================================================
# CALCULATE BENCHMARK
# ============================================================

def calculate_benchmark():

    start_time = time.perf_counter()

    # ========================================================
    # LOAD DATA
    # ========================================================

    database_results = (
        load_database_results()
    )

    ground_truth = (
        load_ground_truth()
    )

    reconciliation_results = (
        load_reconciliation_results()
    )

    final_results = (
        load_final_results()
    )

    # ========================================================
    # VALIDATE
    # ========================================================

    if database_results.empty:

        raise RuntimeError(
            "No database reconciliation results found."
        )

    if ground_truth.empty:

        raise RuntimeError(
            "Ground truth dataset is empty."
        )

    # ========================================================
    # NORMALIZE DATABASE
    # ========================================================

    database_results = (
        database_results.copy()
    )

    database_results[
        "transaction_id"
    ] = (
        database_results[
            "transaction_id"
        ]
        .apply(clean_string)
    )

    database_results[
        "exception_type"
    ] = (
        database_results[
            "exception_type"
        ]
        .apply(normalize_exception_type)
    )

    database_results[
        "final_status"
    ] = (
        database_results[
            "final_status"
        ]
        .apply(clean_string)
        .str.upper()
    )

    database_results[
        "final_action"
    ] = (
        database_results[
            "final_action"
        ]
        .apply(clean_string)
        .str.upper()
    )

    database_results[
        "ai_attempts"
    ] = pd.to_numeric(
        database_results[
            "ai_attempts"
        ],
        errors="coerce"
    ).fillna(0)

    database_results[
        "ai_override"
    ] = pd.to_numeric(
        database_results[
            "ai_override"
        ],
        errors="coerce"
    ).fillna(0)

    # ========================================================
    # NORMALIZE GROUND TRUTH
    # ========================================================

    ground_truth = (
        ground_truth.copy()
    )

    ground_truth[
        "transaction_id"
    ] = (
        ground_truth[
            "transaction_id"
        ]
        .apply(clean_string)
    )

    ground_truth[
        "invoice_id"
    ] = (
        ground_truth[
            "invoice_id"
        ]
        .apply(clean_string)
    )

    ground_truth[
        "expected_status"
    ] = (
        ground_truth[
            "expected_status"
        ]
        .apply(normalize_expected_status)
    )

    ground_truth[
        "exception_type"
    ] = (
        ground_truth[
            "exception_type"
        ]
        .apply(normalize_exception_type)
    )

    # ========================================================
    # REMOVE DUPLICATE GROUND TRUTH TRANSACTIONS
    # ========================================================

    ground_truth = (
        ground_truth
        .drop_duplicates(
            subset=[
                "transaction_id"
            ],
            keep="last"
        )
        .copy()
    )

    # ========================================================
    # BUILD MAPS
    # ========================================================

    transaction_map = (
        build_transaction_result_map(
            database_results
        )
    )

    # --------------------------------------------------------
    # Invoice map:
    #
    # final_results.csv is preferred because it contains
    # invoice_id in the normal pipeline.
    # --------------------------------------------------------

    invoice_source = pd.DataFrame()

    if (
        not final_results.empty
        and
        "invoice_id"
        in final_results.columns
    ):

        invoice_source = (
            final_results.copy()
        )

    elif (
        not reconciliation_results.empty
        and
        "invoice_id"
        in reconciliation_results.columns
    ):

        invoice_source = (
            reconciliation_results.copy()
        )

    invoice_map = (
        build_invoice_result_map(
            invoice_source
        )
    )

    # ========================================================
    # COMPARISON
    # ========================================================

    comparison_rows = []

    transaction_matches = 0
    invoice_matches = 0
    invoice_transaction_matches = 0
    no_matches = 0

    # ========================================================
    # PROCESS GROUND TRUTH
    # ========================================================

    for _, gt_row in ground_truth.iterrows():

        gt_transaction_id = clean_string(
            gt_row[
                "transaction_id"
            ]
        )

        gt_invoice_id = clean_string(
            gt_row[
                "invoice_id"
            ]
        )

        expected_status = (
            normalize_expected_status(
                gt_row[
                    "expected_status"
                ]
            )
        )

        expected_exception_type = (
            normalize_exception_type(
                gt_row[
                    "exception_type"
                ]
            )
        )

        # ----------------------------------------------------
        # FIND RESULT
        # ----------------------------------------------------

        result_row, match_method = find_result(
            gt_transaction_id,
            gt_invoice_id,
            transaction_map,
            invoice_map
        )

        if match_method == "TRANSACTION_ID":

            transaction_matches += 1

        elif match_method == "INVOICE_ID":

            invoice_matches += 1

        elif match_method == "INVOICE_TRANSACTION_ID":

            invoice_transaction_matches += 1

        else:

            no_matches += 1

        # ----------------------------------------------------
        # RESULT VALUES
        # ----------------------------------------------------

        if result_row is None:

            result_exists = False

            raw_final_status = ""

            benchmark_status = ""

            final_action = ""

            result_exception_type = ""

            ai_attempts = 0

            ai_override = 0

            ai_confidence = ""

            ai_explanation = ""

            decision_type = "OTHER"

            evaluation_state = "PENDING"

            status_correct = False

            exception_type_correct = False

            overall_correct = False

            result_category = "PENDING"

        else:

            result_exists = True

            raw_final_status = clean_string(
                get_result_value(
                    result_row,
                    "final_status",
                    ""
                )
            ).upper()

            final_action = clean_string(
                get_result_value(
                    result_row,
                    "final_action",
                    ""
                )
            ).upper()

            benchmark_status = (
                normalize_result_status(
                    raw_final_status,
                    final_action
                )
            )

            result_exception_type = (
                normalize_exception_type(
                    get_result_value(
                        result_row,
                        "exception_type",
                        ""
                    )
                )
            )

            ai_attempts = pd.to_numeric(
                get_result_value(
                    result_row,
                    "ai_attempts",
                    0
                ),
                errors="coerce"
            )

            if pd.isna(ai_attempts):

                ai_attempts = 0

            ai_override = pd.to_numeric(
                get_result_value(
                    result_row,
                    "ai_override",
                    0
                ),
                errors="coerce"
            )

            if pd.isna(ai_override):

                ai_override = 0

            ai_confidence = (
                get_result_value(
                    result_row,
                    "ai_confidence",
                    ""
                )
            )

            ai_explanation = (
                get_result_value(
                    result_row,
                    "ai_explanation",
                    ""
                )
            )

            decision_type = (
                classify_decision(
                    result_row
                )
            )

            evaluation_state = (
                "EVALUATED"
                if is_evaluated(
                    result_row
                )
                else "PENDING"
            )

            # ------------------------------------------------
            # STATUS CORRECTNESS
            # ------------------------------------------------

            status_correct = (
                evaluation_state == "EVALUATED"
                and
                benchmark_status
                ==
                expected_status
            )

            # ------------------------------------------------
            # EXCEPTION TYPE CORRECTNESS
            #
            # Only exception ground truth requires exception
            # type validation.
            # ------------------------------------------------

            if expected_status == "EXCEPTION":

                exception_type_correct = (
                    result_exception_type
                    ==
                    expected_exception_type
                )

            else:

                exception_type_correct = True

            # ------------------------------------------------
            # OVERALL CORRECTNESS
            #
            # For an expected exception:
            #
            # 1. Exception outcome must be correct
            # 2. Exception type must be correct
            #
            # For MATCHED:
            #
            # Status must be correct.
            # ------------------------------------------------

            if expected_status == "EXCEPTION":

                overall_correct = (
                    status_correct
                    and
                    exception_type_correct
                )

            else:

                overall_correct = (
                    status_correct
                )

            # ------------------------------------------------
            # CATEGORY
            # ------------------------------------------------

            if evaluation_state == "PENDING":

                result_category = "PENDING"

            elif overall_correct:

                result_category = "CORRECT"

            else:

                result_category = "INCORRECT"

        # ====================================================
        # STORE COMPARISON
        # ====================================================

        comparison_rows.append({

            "transaction_id":
                gt_transaction_id,

            "invoice_id":
                gt_invoice_id,

            "expected_status":
                expected_status,

            "expected_exception_type":
                expected_exception_type,

            "result_exists":
                result_exists,

            "match_method":
                match_method,

            "result_transaction_id":
                (
                    get_result_value(
                        result_row,
                        "transaction_id",
                        ""
                    )
                    if result_row is not None
                    else ""
                ),

            "raw_final_status":
                raw_final_status,

            "benchmark_status":
                benchmark_status,

            "final_action":
                final_action,

            "result_exception_type":
                result_exception_type,

            "status_correct":
                status_correct,

            "exception_type_correct":
                exception_type_correct,

            "overall_correct":
                overall_correct,

            "decision_type":
                decision_type,

            "evaluation_state":
                evaluation_state,

            "result_category":
                result_category,

            "ai_attempts":
                ai_attempts,

            "ai_override":
                ai_override,

            "ai_confidence":
                ai_confidence,

            "ai_explanation":
                ai_explanation
        })

    # ========================================================
    # DATAFRAME
    # ========================================================

    comparison = pd.DataFrame(
        comparison_rows
    )

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    total_ground_truth = len(
        ground_truth
    )

    total_database_results = len(
        database_results
    )

    evaluated = int(
        (
            comparison[
                "evaluation_state"
            ]
            ==
            "EVALUATED"
        ).sum()
    )

    pending = int(
        (
            comparison[
                "evaluation_state"
            ]
            ==
            "PENDING"
        ).sum()
    )

    correct = int(
        (
            comparison[
                "result_category"
            ]
            ==
            "CORRECT"
        ).sum()
    )

    incorrect = int(
        (
            comparison[
                "result_category"
            ]
            ==
            "INCORRECT"
        ).sum()
    )

    # ========================================================
    # ACCURACY
    # ========================================================

    if evaluated > 0:

        accuracy = round(
            correct
            /
            evaluated
            *
            100,
            2
        )

    else:

        accuracy = 0.0

    # ========================================================
    # GROUND TRUTH COMPOSITION
    # ========================================================

    matched_ground_truth = int(
        (
            ground_truth[
                "expected_status"
            ]
            ==
            "MATCHED"
        ).sum()
    )

    exception_ground_truth = int(
        (
            ground_truth[
                "expected_status"
            ]
            ==
            "EXCEPTION"
        ).sum()
    )

    # ========================================================
    # EXCEPTION EVALUATION
    # ========================================================

    exception_mask = (
        comparison[
            "expected_status"
        ]
        ==
        "EXCEPTION"
    )

    exception_evaluated_mask = (
        exception_mask
        &
        (
            comparison[
                "evaluation_state"
            ]
            ==
            "EVALUATED"
        )
    )

    exception_evaluated = int(
        exception_evaluated_mask.sum()
    )

    exception_type_correct = int(
        (
            exception_evaluated_mask
            &
            comparison[
                "exception_type_correct"
            ]
        ).sum()
    )

    if exception_evaluated > 0:

        exception_type_accuracy = round(
            exception_type_correct
            /
            exception_evaluated
            *
            100,
            2
        )

    else:

        exception_type_accuracy = 0.0

    # ========================================================
    # EXCEPTION OUTCOME ACCURACY
    # ========================================================

    exception_status_correct = int(
        (
            exception_evaluated_mask
            &
            comparison[
                "status_correct"
            ]
        ).sum()
    )

    if exception_evaluated > 0:

        exception_resolution_accuracy = round(
            exception_status_correct
            /
            exception_evaluated
            *
            100,
            2
        )

    else:

        exception_resolution_accuracy = 0.0

    # ========================================================
    # DECISION BREAKDOWN
    # ========================================================

    deterministic_mask = (
        comparison[
            "decision_type"
        ]
        ==
        "DETERMINISTIC_MATCH"
    )

    rule_mask = (
        comparison[
            "decision_type"
        ]
        ==
        "RULE_BASED_RESOLUTION"
    )

    ai_mask = (
        comparison[
            "decision_type"
        ]
        ==
        "AI_REASONING"
    )

    human_mask = (
        comparison[
            "decision_type"
        ]
        ==
        "HUMAN_REVIEW"
    )

    recovery_mask = (
        comparison[
            "decision_type"
        ]
        ==
        "AI_FAILURE_RECOVERY"
    )

    deterministic_total = int(
        deterministic_mask.sum()
    )

    deterministic_correct = int(
        (
            deterministic_mask
            &
            comparison[
                "overall_correct"
            ]
        ).sum()
    )

    rule_total = int(
        rule_mask.sum()
    )

    rule_correct = int(
        (
            rule_mask
            &
            comparison[
                "overall_correct"
            ]
        ).sum()
    )

    ai_total = int(
        ai_mask.sum()
    )

    ai_correct = int(
        (
            ai_mask
            &
            comparison[
                "overall_correct"
            ]
        ).sum()
    )

    human_review = int(
        (
            comparison[
                "final_action"
            ]
            ==
            "HUMAN_REVIEW"
        ).sum()
    )

    failure_recovery = int(
        (
            comparison[
                "ai_override"
            ]
            == 1
        ).sum()
    )

    # ========================================================
    # MATCH / RESOLUTION METRICS
    # ========================================================

    matched_results = int(
        (
            comparison[
                "benchmark_status"
            ]
            ==
            "MATCHED"
        ).sum()
    )

    exception_results = int(
        (
            comparison[
                "benchmark_status"
            ]
            ==
            "EXCEPTION"
        ).sum()
    )

    # ========================================================
    # MATCH RATE
    # ========================================================

    if total_ground_truth > 0:

        match_rate = round(
            matched_results
            /
            total_ground_truth
            *
            100,
            2
        )

    else:

        match_rate = 0.0

    # ========================================================
    # OUTPUT THROUGHPUT
    # ========================================================

    elapsed_seconds = (
        time.perf_counter()
        -
        start_time
    )

    if elapsed_seconds > 0:

        throughput = round(
            total_database_results
            /
            elapsed_seconds,
            2
        )

    else:

        throughput = 0.0

    # ========================================================
    # RESULT BREAKDOWN
    # ========================================================

    result_breakdown = (
        comparison[
            "result_category"
        ]
        .value_counts()
    )

    decision_breakdown = (
        comparison[
            "decision_type"
        ]
        .value_counts()
    )

    match_breakdown = (
        comparison[
            "match_method"
        ]
        .value_counts()
    )

    # ========================================================
    # SAVE TRANSACTION DETAILS
    # ========================================================

    comparison.to_csv(
        BENCHMARK_DETAILS_PATH,
        index=False
    )

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    benchmark_metrics = {

        "ground_truth_records":
            total_ground_truth,

        "database_result_records":
            total_database_results,

        "transaction_id_matches":
            transaction_matches,

        "invoice_id_matches":
            invoice_matches,

        "invoice_transaction_id_matches":
            invoice_transaction_matches,

        "no_matches":
            no_matches,

        "evaluated_records":
            evaluated,

        "pending_records":
            pending,

        "correct_records":
            correct,

        "incorrect_records":
            incorrect,

        "accuracy_percent":
            accuracy,

        "matched_ground_truth":
            matched_ground_truth,

        "exception_ground_truth":
            exception_ground_truth,

        "matched_results":
            matched_results,

        "exception_results":
            exception_results,

        "match_rate_percent":
            match_rate,

        "exception_evaluated":
            exception_evaluated,

        "exception_status_correct":
            exception_status_correct,

        "exception_resolution_accuracy_percent":
            exception_resolution_accuracy,

        "exception_type_correct":
            exception_type_correct,

        "exception_type_accuracy_percent":
            exception_type_accuracy,

        "deterministic_total":
            deterministic_total,

        "deterministic_correct":
            deterministic_correct,

        "rule_based_total":
            rule_total,

        "rule_based_correct":
            rule_correct,

        "ai_total":
            ai_total,

        "ai_correct":
            ai_correct,

        "human_review":
            human_review,

        "failure_recovery":
            failure_recovery,

        "throughput_records_per_second":
            throughput,

        "evaluation_time_seconds":
            round(
                elapsed_seconds,
                4
            )
    }

    benchmark_df = pd.DataFrame(
        [benchmark_metrics]
    )

    benchmark_df.to_csv(
        BENCHMARK_PATH,
        index=False
    )

    # ========================================================
    # SUMMARY TEXT
    # ========================================================

    summary_lines = [

        "=" * 70,

        "AI FINANCE CONTROLLER - STEP 21",

        "CONTROLLED EVALUATION / BENCHMARK",

        "=" * 70,

        "",

        "BENCHMARK POLICY",

        "-" * 70,

        "This benchmark does NOT call Gemini.",

        "It evaluates existing database results against",
        "the ground-truth dataset.",

        "",

        "Ground truth MATCHED is evaluated against",
        "database RESOLVED / AI_RESOLVED.",

        "Ground truth EXCEPTION is evaluated against",
        "database UNRESOLVED / HUMAN_REVIEW.",

        "Exception type must also match for an exception",
        "record to be counted as fully correct.",

        "",

        "DATASET",

        "-" * 70,

        f"Ground truth records      : "
        f"{total_ground_truth}",

        f"Database result records   : "
        f"{total_database_results}",

        "",

        "MATCHING",

        "-" * 70,

        f"Transaction ID matches        : "
        f"{transaction_matches}",

        f"Invoice ID matches            : "
        f"{invoice_matches}",

        f"Invoice transaction matches   : "
        f"{invoice_transaction_matches}",

        f"No matches                    : "
        f"{no_matches}",

        "",

        "EVALUATION",

        "-" * 70,

        f"Evaluated records         : "
        f"{evaluated}",

        f"Pending records           : "
        f"{pending}",

        f"Correct                   : "
        f"{correct}",

        f"Incorrect                 : "
        f"{incorrect}",

        f"Overall accuracy          : "
        f"{accuracy:.2f}%",

        "",

        "RECONCILIATION",

        "-" * 70,

        f"Expected MATCHED          : "
        f"{matched_ground_truth}",

        f"Expected EXCEPTION        : "
        f"{exception_ground_truth}",

        f"Actual MATCHED            : "
        f"{matched_results}",

        f"Actual EXCEPTION          : "
        f"{exception_results}",

        f"Match / resolution rate   : "
        f"{match_rate:.2f}%",

        "",

        "EXCEPTION VALIDATION",

        "-" * 70,

        f"Evaluated exceptions       : "
        f"{exception_evaluated}",

        f"Correct exception outcome  : "
        f"{exception_status_correct}",

        f"Exception outcome accuracy : "
        f"{exception_resolution_accuracy:.2f}%",

        f"Correct exception type     : "
        f"{exception_type_correct}",

        f"Exception type accuracy    : "
        f"{exception_type_accuracy:.2f}%",

        "",

        "DECISION BREAKDOWN",

        "-" * 70,

        f"Deterministic total        : "
        f"{deterministic_total}",

        f"Deterministic correct      : "
        f"{deterministic_correct}",

        f"Rule-based total           : "
        f"{rule_total}",

        f"Rule-based correct         : "
        f"{rule_correct}",

        f"AI reasoning total         : "
        f"{ai_total}",

        f"AI reasoning correct       : "
        f"{ai_correct}",

        f"Human review               : "
        f"{human_review}",

        f"Failure recoveries         : "
        f"{failure_recovery}",

        "",

        "RESULT BREAKDOWN",

        "-" * 70,

        result_breakdown.to_string(),

        "",

        "MATCH METHOD BREAKDOWN",

        "-" * 70,

        match_breakdown.to_string(),

        "",

        "DECISION TYPE BREAKDOWN",

        "-" * 70,

        decision_breakdown.to_string(),

        "",

        "THROUGHPUT",

        "-" * 70,

        f"Evaluation time            : "
        f"{elapsed_seconds:.4f} seconds",

        f"Throughput                 : "
        f"{throughput:.2f} records/second",

        "",

        "OUTPUT FILES",

        "-" * 70,

        f"Benchmark metrics          : "
        f"{BENCHMARK_PATH}",

        f"Transaction details        : "
        f"{BENCHMARK_DETAILS_PATH}",

        f"Benchmark summary          : "
        f"{BENCHMARK_SUMMARY_PATH}",

        "",

        "=" * 70,

        "STEP 21 COMPLETED",

        "=" * 70
    ]

    summary_text = "\n".join(
        summary_lines
    )

    with open(
        BENCHMARK_SUMMARY_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            summary_text
        )

    # ========================================================
    # DISPLAY
    # ========================================================

    print()
    print(summary_text)

    print()

    print(
        "Benchmark metrics saved to:"
    )

    print(
        BENCHMARK_PATH
    )

    print()

    print(
        "Transaction-level benchmark saved to:"
    )

    print(
        BENCHMARK_DETAILS_PATH
    )

    print()

    print(
        "Benchmark summary saved to:"
    )

    print(
        BENCHMARK_SUMMARY_PATH
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        calculate_benchmark()

    except Exception as error:

        print()
        print("=" * 70)
        print("STEP 21 FAILED")
        print("=" * 70)

        print()
        print(
            f"Error: {error}"
        )

        raise
