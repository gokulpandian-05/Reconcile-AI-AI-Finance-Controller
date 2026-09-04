import os
import sqlite3
import pandas as pd


# ============================================================
# AI FINANCE CONTROLLER
# STEP 19 - GROUND-TRUTH VALIDATION & ACCURACY
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

METRICS_OUTPUT_PATH = os.path.join(
    DATA_DIR,
    "metrics.csv"
)


# ============================================================
# LOAD DATABASE RESULTS
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
            ORDER BY transaction_id
            """,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

def load_ground_truth():

    if not os.path.exists(GROUND_TRUTH_PATH):

        print(
            "\nWARNING: ground_truth.csv not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(
        GROUND_TRUTH_PATH
    )

    return df


# ============================================================
# NORMALIZE CONTROLLER STATUS
# ============================================================

def normalize_controller_status(value):

    if pd.isna(value):

        return ""

    value = str(value).strip().upper()

    aliases = {

        "MATCH":
            "RESOLVED",

        "MATCHED":
            "RESOLVED",

        "RESOLVED":
            "RESOLVED",

        "AI_RESOLVED":
            "RESOLVED",

        "UNRESOLVED":
            "UNRESOLVED",

        "HUMAN_REVIEW":
            "UNRESOLVED",

        "PENDING_AI_TEST":
            "PENDING_AI_TEST"
    }

    return aliases.get(
        value,
        value
    )


# ============================================================
# NORMALIZE GROUND-TRUTH STATUS
# ============================================================

def normalize_ground_truth_status(value):

    if pd.isna(value):

        return ""

    value = str(value).strip().upper()

    aliases = {

        "MATCH":
            "RESOLVED",

        "MATCHED":
            "RESOLVED",

        "RESOLVED":
            "RESOLVED",

        "EXCEPTION":
            "UNRESOLVED",

        "UNRESOLVED":
            "UNRESOLVED",

        "HUMAN_REVIEW":
            "UNRESOLVED"
    }

    return aliases.get(
        value,
        value
    )


# ============================================================
# CALCULATE METRICS
# ============================================================

def calculate_metrics():

    results = load_database_results()

    if results.empty:

        print(
            "\nNo reconciliation results found "
            "in database."
        )

        return


    # ========================================================
    # NORMALIZE DATABASE COLUMNS
    # ========================================================

    results["final_status"] = (
        results["final_status"]
        .apply(normalize_controller_status)
    )

    results["final_action"] = (
        results["final_action"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    results["ai_attempts"] = pd.to_numeric(
        results["ai_attempts"],
        errors="coerce"
    ).fillna(0)

    results["ai_override"] = pd.to_numeric(
        results["ai_override"],
        errors="coerce"
    ).fillna(0)


    # ========================================================
    # BASIC COUNTS
    # ========================================================

    total_records = len(results)


    # ========================================================
    # DETERMINISTIC MATCHES
    # ========================================================

    deterministic_mask = (
        (results["final_status"] == "RESOLVED")
        &
        (results["final_action"] == "NO_ACTION")
    )

    deterministic_matches = int(
        deterministic_mask.sum()
    )


    # ========================================================
    # RULE-BASED RESOLUTIONS
    # ========================================================

    rule_based_mask = (
        (results["final_status"] == "RESOLVED")
        &
        (
            results["final_action"]
            == "RULE_BASED_RESOLUTION"
        )
    )

    rule_based_resolved = int(
        rule_based_mask.sum()
    )


    # ========================================================
    # AI RESOLVED
    # ========================================================

    ai_resolved_mask = (
        (results["final_status"] == "RESOLVED")
        &
        (results["ai_attempts"] > 0)
        &
        (~deterministic_mask)
        &
        (~rule_based_mask)
    )

    ai_resolved = int(
        ai_resolved_mask.sum()
    )


    # ========================================================
    # TOTAL RESOLVED
    # ========================================================

    resolved = int(
        (
            results["final_status"]
            == "RESOLVED"
        ).sum()
    )


    # ========================================================
    # UNRESOLVED
    # ========================================================

    unresolved_mask = (
        results["final_status"]
        == "UNRESOLVED"
    )

    unresolved = int(
        unresolved_mask.sum()
    )


    # ========================================================
    # PENDING AI TEST
    # ========================================================

    pending_mask = (
        results["final_status"]
        == "PENDING_AI_TEST"
    )

    pending_ai_test = int(
        pending_mask.sum()
    )


    # ========================================================
    # HUMAN REVIEW
    # ========================================================

    human_review_mask = (
        results["final_action"]
        == "HUMAN_REVIEW"
    )

    human_review = int(
        human_review_mask.sum()
    )


    # ========================================================
    # AI RECORDS
    # ========================================================

    ai_records = int(
        (
            results["ai_attempts"]
            > 0
        ).sum()
    )


    # ========================================================
    # TOTAL AI ATTEMPTS
    # ========================================================

    ai_attempts = int(
        results["ai_attempts"].sum()
    )


    # ========================================================
    # FAILURE RECOVERY
    # ========================================================

    failure_recovery = int(
        (
            results["ai_override"]
            == 1
        ).sum()
    )


    # ========================================================
    # DETERMINISTIC MATCH RATE
    # ========================================================

    if total_records > 0:

        deterministic_match_rate = (
            deterministic_matches
            / total_records
            * 100
        )

    else:

        deterministic_match_rate = 0.0


    # ========================================================
    # FINAL RESOLUTION RATE
    #
    # Counts every RESOLVED result.
    # ========================================================

    if total_records > 0:

        final_resolution_rate = (
            resolved
            / total_records
            * 100
        )

    else:

        final_resolution_rate = 0.0


    # ========================================================
    # STEP 19
    # GROUND-TRUTH VALIDATION
    # ========================================================

    ground_truth = load_ground_truth()

    accuracy = None

    ground_truth_records = 0
    evaluated_records = 0
    correct_records = 0
    incorrect_records = 0
    pending_ground_truth_records = 0


    if not ground_truth.empty:

        # ----------------------------------------------------
        # Find transaction ID column
        # ----------------------------------------------------

        gt_id_column = None

        for column in ground_truth.columns:

            if column.lower().strip() in [
                "transaction_id",
                "transactionid",
                "tx_id"
            ]:

                gt_id_column = column

                break


        # ----------------------------------------------------
        # Find expected-status column
        # ----------------------------------------------------

        gt_status_column = None

        for column in ground_truth.columns:

            if column.lower().strip() in [
                "ground_truth",
                "expected_status",
                "expected_result",
                "true_status",
                "actual_status"
            ]:

                gt_status_column = column

                break


        # ----------------------------------------------------
        # Validate columns
        # ----------------------------------------------------

        if (
            gt_id_column is not None
            and
            gt_status_column is not None
        ):

            gt = ground_truth[
                [
                    gt_id_column,
                    gt_status_column
                ]
            ].copy()

            gt.columns = [
                "transaction_id",
                "expected_status"
            ]


            # ------------------------------------------------
            # Normalize ground truth
            # ------------------------------------------------

            gt["transaction_id"] = (
                gt["transaction_id"]
                .astype(str)
                .str.strip()
            )

            gt["expected_status"] = (
                gt["expected_status"]
                .apply(
                    normalize_ground_truth_status
                )
            )


            # ------------------------------------------------
            # Normalize database transaction IDs
            # ------------------------------------------------

            results["transaction_id"] = (
                results["transaction_id"]
                .astype(str)
                .str.strip()
            )


            # ------------------------------------------------
            # Merge database + ground truth
            # ------------------------------------------------

            comparison = results.merge(
                gt,
                on="transaction_id",
                how="inner"
            )


            ground_truth_records = len(
                comparison
            )


            if not comparison.empty:

                # --------------------------------------------
                # Exclude PENDING_AI_TEST
                #
                # These records were intentionally not sent
                # to Gemini because TEST_MODE=True.
                # --------------------------------------------

                evaluated = comparison[
                    comparison["final_status"]
                    != "PENDING_AI_TEST"
                ].copy()


                pending_ground_truth_records = int(
                    (
                        comparison["final_status"]
                        == "PENDING_AI_TEST"
                    ).sum()
                )


                evaluated_records = len(
                    evaluated
                )


                if evaluated_records > 0:

                    evaluated["correct"] = (
                        evaluated["final_status"]
                        ==
                        evaluated["expected_status"]
                    )


                    correct_records = int(
                        evaluated["correct"].sum()
                    )


                    incorrect_records = int(
                        (
                            ~evaluated["correct"]
                        ).sum()
                    )


                    accuracy = (
                        correct_records
                        / evaluated_records
                        * 100
                    )


                    accuracy = round(
                        accuracy,
                        2
                    )


                print()
                print(
                    "Ground truth records compared:"
                    f" {ground_truth_records}"
                )

                print(
                    "Ground truth records evaluated:"
                    f" {evaluated_records}"
                )

                print(
                    "Ground truth records pending:"
                    f" {pending_ground_truth_records}"
                )


            else:

                print(
                    "\nWARNING: No transaction IDs "
                    "matched ground_truth.csv."
                )


        else:

            print(
                "\nWARNING: Could not identify "
                "ground-truth columns."
            )

            print(
                "Ground truth columns:"
            )

            print(
                list(
                    ground_truth.columns
                )
            )


    # ========================================================
    # DISPLAY MAIN METRICS
    # ========================================================

    print()

    print(
        "=" * 55
    )

    print(
        " AI FINANCE CONTROLLER METRICS"
    )

    print(
        "=" * 55
    )


    print(
        f"Total records             : "
        f"{total_records}"
    )

    print(
        f"Deterministically matched : "
        f"{deterministic_matches}"
    )

    print(
        f"Rule-based resolved       : "
        f"{rule_based_resolved}"
    )

    print(
        f"AI resolved               : "
        f"{ai_resolved}"
    )

    print(
        f"Resolved                  : "
        f"{resolved}"
    )

    print(
        f"Unresolved                : "
        f"{unresolved}"
    )

    print(
        f"Pending AI test           : "
        f"{pending_ai_test}"
    )

    print(
        f"Human review              : "
        f"{human_review}"
    )

    print(
        f"AI records                : "
        f"{ai_records}"
    )

    print(
        f"AI attempts               : "
        f"{ai_attempts}"
    )

    print(
        f"Failure recovery events   : "
        f"{failure_recovery}"
    )


    print(
        f"\nDeterministic match rate  : "
        f"{deterministic_match_rate:.2f}%"
    )

    print(
        f"Final resolution rate     : "
        f"{final_resolution_rate:.2f}%"
    )


    if accuracy is not None:

        print(
            f"Ground-truth accuracy    : "
            f"{accuracy:.2f}%"
        )

    else:

        print(
            "Ground-truth accuracy    : "
            "N/A"
        )


    print(
        "=" * 55
    )


    # ========================================================
    # GROUND-TRUTH SUMMARY
    # ========================================================

    print(
        "\nGROUND-TRUTH VALIDATION"
    )

    print(
        "-" * 55
    )

    print(
        f"Ground truth records     : "
        f"{ground_truth_records}"
    )

    print(
        f"Evaluated records        : "
        f"{evaluated_records}"
    )

    print(
        f"Correct                  : "
        f"{correct_records}"
    )

    print(
        f"Incorrect                : "
        f"{incorrect_records}"
    )

    print(
        f"Pending / not evaluated  : "
        f"{pending_ground_truth_records}"
    )

    if accuracy is not None:

        print(
            f"Accuracy                 : "
            f"{accuracy:.2f}%"
        )

    else:

        print(
            "Accuracy                 : N/A"
        )


    # ========================================================
    # STATUS BREAKDOWN
    # ========================================================

    print(
        "\nFinal status breakdown:"
    )

    print(
        results[
            "final_status"
        ]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # ACTION BREAKDOWN
    # ========================================================

    print(
        "\nFinal action breakdown:"
    )

    print(
        results[
            "final_action"
        ]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # FAILURE RECOVERY DETAILS
    # ========================================================

    recovery_records = results[
        results["ai_override"] == 1
    ]


    if not recovery_records.empty:

        print(
            "\nFailure recovery records:"
        )

        print(
            recovery_records[
                [
                    "transaction_id",
                    "final_status",
                    "final_action",
                    "ai_attempts"
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # SAVE METRICS
    # ========================================================

    metrics_output = {

        "total_records":
            total_records,

        "deterministic_matches":
            deterministic_matches,

        "rule_based_resolved":
            rule_based_resolved,

        "ai_resolved":
            ai_resolved,

        "resolved":
            resolved,

        "unresolved":
            unresolved,

        "pending_ai_test":
            pending_ai_test,

        "human_review":
            human_review,

        "ai_records":
            ai_records,

        "ai_attempts":
            ai_attempts,

        "failure_recovery_events":
            failure_recovery,

        "deterministic_match_rate":
            round(
                deterministic_match_rate,
                2
            ),

        "final_resolution_rate":
            round(
                final_resolution_rate,
                2
            ),

        "ground_truth_records":
            ground_truth_records,

        "evaluated_records":
            evaluated_records,

        "correct_records":
            correct_records,

        "incorrect_records":
            incorrect_records,

        "pending_ground_truth_records":
            pending_ground_truth_records,

        "ground_truth_accuracy":
            accuracy
    }


    metrics_df = pd.DataFrame(
        [metrics_output]
    )


    metrics_df.to_csv(
        METRICS_OUTPUT_PATH,
        index=False
    )


    print()
    print(
        "Metrics saved to:"
    )

    print(
        METRICS_OUTPUT_PATH
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    calculate_metrics()