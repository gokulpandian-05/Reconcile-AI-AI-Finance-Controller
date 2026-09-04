import sys
import os

# ------------------------------------------------------------
# Make sure src/ modules can be imported
# ------------------------------------------------------------

SRC_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ------------------------------------------------------------
# Project modules
# ------------------------------------------------------------

from llm import explain_exception
from audit import write_audit_log
from database import save_reconciliation_result


# ============================================================
# AI FINANCE CONTROLLER
# STEP 12 - AGENT
# STEP 17 - SQLITE STORAGE
# ============================================================


class FinanceAgent:
    """
    Workflow controller for one financial transaction.

    Python / deterministic logic:
        - Financial calculations remain authoritative.

    Gemini:
        - Provides contextual explanation.

    Agent:
        - Coordinates the workflow.
        - Applies routing.
        - Handles failures.
        - Writes audit information.
        - Stores final reconciliation results in SQLite.
    """

    def __init__(self):

        self.name = (
            "AI Finance Controller Agent"
        )


    # ========================================================
    # PROCESS ONE TRANSACTION
    # ========================================================

    def process_transaction(
        self,
        transaction,
        ai_required=True
    ):

        transaction_id = transaction.get(
            "transaction_id"
        )

        exception_type = transaction.get(
            "exception_type"
        )

        print(
            f"\nAgent processing: {transaction_id}"
        )

        print(
            f"Exception type: {exception_type}"
        )


        # ====================================================
        # ROUTE 1
        # NO AI REQUIRED
        # ====================================================

        if not ai_required:

            result = {

                "transaction_id":
                    transaction_id,

                "exception_type":
                    exception_type,

                "status":
                    "RESOLVED",

                "recommended_action":
                    "NO_ACTION",

                "explanation":
                    "Transaction resolved using "
                    "deterministic rules. "
                    "AI reasoning was not required.",

                "confidence":
                    1.0,

                "evidence":
                    [],

                "calculation":
                    "",

                "override":
                    False,

                "override_reason":
                    "",

                "llm_attempt":
                    0,

                "agent_route":
                    "DETERMINISTIC",

                "failure_recovery":
                    False
            }


            # ------------------------------------------------
            # Audit deterministic decision
            # ------------------------------------------------

            write_audit_log(

                transaction_id=transaction_id,

                action="DETERMINISTIC_RESOLUTION",

                evidence=[],

                decision="RESOLVED",

                reason=(
                    "Transaction resolved using "
                    "deterministic rules."
                ),

                confidence=1.0,

                agent_route="DETERMINISTIC",

                failure_recovery=False
            )


            # ------------------------------------------------
            # Save deterministic result to SQLite
            # ------------------------------------------------

            save_reconciliation_result(

                transaction_id=transaction_id,

                exception_type=exception_type,

                final_status="RESOLVED",

                final_action="NO_ACTION",

                ai_confidence=1.0,

                ai_override=False,

                ai_attempts=0,

                ai_explanation=(
                    "Transaction resolved using "
                    "deterministic rules. "
                    "AI reasoning was not required."
                )
            )


            return result


        # ====================================================
        # ROUTE 2
        # AI REQUIRED
        # ====================================================

        try:

            print(
                "Agent route: AI_REASONING"
            )


            # ------------------------------------------------
            # Send transaction to LLM
            # ------------------------------------------------

            result = explain_exception(
                transaction
            )


            # ------------------------------------------------
            # Add agent metadata
            # ------------------------------------------------

            result["agent_route"] = (
                "AI_REASONING"
            )


            # ------------------------------------------------
            # Determine whether failure recovery occurred
            #
            # This is based on the LLM fallback result.
            # A quota/API failure can therefore be recorded
            # without treating it as an unexpected Python
            # exception.
            # ------------------------------------------------

            override_reason = str(
                result.get(
                    "override_reason",
                    ""
                )
            ).lower()


            result["failure_recovery"] = (

                "quota"
                in override_reason

                or

                "api"
                in override_reason

                or

                "failed"
                in override_reason

                or

                "timeout"
                in override_reason

                or

                "resource_exhausted"
                in override_reason
            )


            # ------------------------------------------------
            # AUDIT SUCCESS / LLM COMPLETION
            # ------------------------------------------------

            write_audit_log(

                transaction_id=transaction_id,

                action="AI_ANALYSIS_COMPLETED",

                evidence=result.get(
                    "evidence",
                    []
                ),

                decision=result.get(
                    "status",
                    "UNRESOLVED"
                ),

                reason=result.get(

                    "override_reason",

                    result.get(
                        "explanation",
                        ""
                    )
                ),

                confidence=result.get(
                    "confidence",
                    0.0
                ),

                agent_route=(
                    "AI_REASONING"
                ),

                failure_recovery=result.get(
                    "failure_recovery",
                    False
                )
            )


            # ------------------------------------------------
            # If LLM itself returned a fallback because of
            # quota/API failure, create a specific audit event.
            # ------------------------------------------------

            if result.get(
                "failure_recovery",
                False
            ):

                write_audit_log(

                    transaction_id=transaction_id,

                    action="LLM_FAILURE_RECOVERY",

                    evidence=[],

                    decision=result.get(
                        "status",
                        "UNRESOLVED"
                    ),

                    reason=result.get(
                        "override_reason",
                        "LLM failure recovery triggered."
                    ),

                    confidence=result.get(
                        "confidence",
                        0.0
                    ),

                    agent_route=(
                        "FAILURE_RECOVERY"
                    ),

                    failure_recovery=True
                )


            # ------------------------------------------------
            # STEP 17
            # SAVE RESULT TO SQLITE
            # ------------------------------------------------

            save_reconciliation_result(

                transaction_id=transaction_id,

                exception_type=transaction.get(
                    "exception_type"
                ),

                final_status=result.get(
                    "status",
                    "UNRESOLVED"
                ),

                final_action=result.get(
                    "recommended_action",
                    "HUMAN_REVIEW"
                ),

                ai_confidence=result.get(
                    "confidence",
                    0.0
                ),

                ai_override=result.get(
                    "override",
                    False
                ),

                ai_attempts=result.get(
                    "llm_attempt",
                    0
                ),

                ai_explanation=result.get(
                    "explanation",
                    ""
                )
            )


            # ------------------------------------------------
            # Return final agent result
            # ------------------------------------------------

            return result


        # ====================================================
        # UNEXPECTED AGENT FAILURE
        # ====================================================

        except Exception as e:

            error_message = str(e)


            print(
                f"Agent failure for "
                f"{transaction_id}: "
                f"{error_message}"
            )


            # ------------------------------------------------
            # FAILURE RECOVERY AUDIT
            # ------------------------------------------------

            write_audit_log(

                transaction_id=transaction_id,

                action="AGENT_FAILURE",

                evidence=[],

                decision="UNRESOLVED",

                reason=error_message,

                confidence=0.0,

                agent_route="FAILURE_RECOVERY",

                failure_recovery=True
            )


            # ------------------------------------------------
            # FAILURE RESULT
            # ------------------------------------------------

            failure_result = {

                "transaction_id":
                    transaction_id,

                "exception_type":
                    exception_type,

                "status":
                    "UNRESOLVED",

                "recommended_action":
                    "HUMAN_REVIEW",

                "explanation":
                    "Agent could not complete "
                    "the transaction workflow.",

                "confidence":
                    0.0,

                "evidence":
                    [],

                "calculation":
                    "",

                "agent_route":
                    "FAILURE_RECOVERY",

                "failure_recovery":
                    True,

                "override":
                    True,

                "override_reason":
                    error_message,

                "llm_attempt":
                    0
            }


            # ------------------------------------------------
            # SAVE FAILURE TO SQLITE
            # ------------------------------------------------

            try:

                save_reconciliation_result(

                    transaction_id=transaction_id,

                    exception_type=exception_type,

                    final_status="UNRESOLVED",

                    final_action="HUMAN_REVIEW",

                    ai_confidence=0.0,

                    ai_override=True,

                    ai_attempts=0,

                    ai_explanation=(
                        "Agent could not complete "
                        "the transaction workflow."
                    )
                )

            except Exception as db_error:

                print(
                    "Database save failed: "
                    f"{db_error}"
                )


            return failure_result


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def process_transaction(
    transaction,
    ai_required=True
):

    agent = FinanceAgent()

    return agent.process_transaction(

        transaction,

        ai_required=ai_required
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_transaction = {

        "transaction_id":
            "TX045",

        "exception_type":
            "SETTLEMENT_DIFFERENCE",

        "invoice": {

            "invoice_id":
                "INV045",

            "customer_id":
                "C0045",

            "invoice_amount":
                10000
        },

        "payment": {

            "transaction_id":
                "TX045",

            "payment_amount":
                10000
        },

        "settlement": {

            "settlement_id":
                "SET_TX045",

            "gross_amount":
                10000,

            "fee":
                250,

            "tax":
                0,

            "adjustment":
                0,

            "net_amount":
                9750
        },

        "checks": {

            "invoice_equals_payment":
                True,

            "settlement_calculation_valid":
                True,

            "difference":
                0,

            "reason":
                "Settlement calculation is fully "
                "supported by the supplied evidence."
        }
    }


    print(
        "=========================================="
    )

    print(
        " AI FINANCE CONTROLLER AGENT TEST"
    )

    print(
        "=========================================="
    )


    result = process_transaction(

        test_transaction,

        ai_required=True
    )


    print(
        "\nFINAL AGENT RESULT:"
    )

    print(result)


    print(
        "\n=========================================="
    )