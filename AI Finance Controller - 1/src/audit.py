import os
import json
from datetime import datetime


# ============================================================
# STEP 16 - AUDIT TRAIL
# ============================================================

DATA_DIR = r"C:\Users\pandi\Desktop\AI Finance Controller\data"

AUDIT_FILE = os.path.join(
    DATA_DIR,
    "audit_log.csv"
)


# ============================================================
# AUDIT LOGGER
# ============================================================

def write_audit_log(
    transaction_id,
    action,
    evidence=None,
    decision=None,
    reason="",
    confidence=None,
    agent_route="",
    failure_recovery=False
):
    """
    Write one audit event to audit_log.csv.
    """

    # --------------------------------------------------------
    # Prepare evidence
    # --------------------------------------------------------

    if evidence is None:
        evidence = []

    if isinstance(evidence, (dict, list)):
        evidence = json.dumps(
            evidence,
            default=str
        )

    else:
        evidence = str(evidence)


    # --------------------------------------------------------
    # Create audit record
    # --------------------------------------------------------

    record = {

        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "transaction_id":
            transaction_id,

        "action":
            action,

        "evidence":
            evidence,

        "decision":
            decision or "",

        "reason":
            reason,

        "confidence":
            confidence
            if confidence is not None
            else "",

        "agent_route":
            agent_route,

        "failure_recovery":
            failure_recovery
    }


    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    import pandas as pd

    new_log = pd.DataFrame([
        record
    ])


    # --------------------------------------------------------
    # Append to existing audit log
    # --------------------------------------------------------

    if os.path.exists(AUDIT_FILE):

        new_log.to_csv(
            AUDIT_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        new_log.to_csv(
            AUDIT_FILE,
            index=False
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    write_audit_log(

        transaction_id="TX_TEST",

        action="TEST_AUDIT_EVENT",

        evidence=[
            "Invoice amount = 10000",
            "Payment amount = 10000"
        ],

        decision="RESOLVED",

        reason="Test audit record",

        confidence=1.0,

        agent_route="DETERMINISTIC",

        failure_recovery=False
    )

    print(
        "Audit log written to:"
    )

    print(
        AUDIT_FILE
    )