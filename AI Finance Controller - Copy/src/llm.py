
import os
import json
import time
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Check your .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)

MODEL_NAME = "gemini-3.7-flash"


# ============================================================
# RESPONSE SCHEMA
# ============================================================

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "exception_type": {
            "type": "string"
        },
        "explanation": {
            "type": "string"
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "calculation": {
            "type": "string"
        },
        "status": {
            "type": "string",
            "enum": [
                "RESOLVED",
                "UNRESOLVED"
            ]
        },
        "confidence": {
            "type": "number"
        },
        "recommended_action": {
            "type": "string"
        },
        "override": {
            "type": "boolean"
        },
        "override_reason": {
            "type": "string"
        }
    },
    "required": [
        "exception_type",
        "explanation",
        "evidence",
        "calculation",
        "status",
        "confidence",
        "recommended_action",
        "override",
        "override_reason"
    ]
}


# ============================================================
# PYTHON FINANCIAL VALIDATION
# ============================================================

def validate_financial_data(transaction):

    settlement = transaction.get(
        "settlement",
        {}
    )

    checks = transaction.get(
        "checks",
        {}
    )

    # --------------------------------------------------------
    # No settlement data
    # --------------------------------------------------------

    if not settlement:

        return {
            "valid": False,
            "expected_net": None,
            "actual_net": None,
            "difference": None,
            "reason": "Settlement information is missing."
        }

    gross = settlement.get(
        "gross_amount"
    )

    fee = settlement.get(
        "fee"
    )

    tax = settlement.get(
        "tax"
    )

    adjustment = settlement.get(
        "adjustment"
    )

    actual_net = settlement.get(
        "net_amount"
    )

    # --------------------------------------------------------
    # Check required values
    # --------------------------------------------------------

    values = [
        gross,
        fee,
        tax,
        adjustment,
        actual_net
    ]

    if any(
        value is None
        for value in values
    ):

        return {
            "valid": False,
            "expected_net": None,
            "actual_net": actual_net,
            "difference": None,
            "reason": "Incomplete settlement data."
        }

    # --------------------------------------------------------
    # Deterministic calculation
    #
    # Net = Gross - Fee - Tax + Adjustment
    # --------------------------------------------------------

    expected_net = (
        float(gross)
        - float(fee)
        - float(tax)
        + float(adjustment)
    )

    difference = (
        expected_net
        - float(actual_net)
    )

    difference = round(
        difference,
        2
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    valid = (
        abs(difference) < 0.01
    )

    if valid:

        reason = (
            "Settlement calculation is fully "
            "supported by the supplied evidence."
        )

    else:

        reason = (
            f"Unexplained settlement difference: "
            f"{abs(difference):.2f}"
        )

    return {
        "valid": valid,
        "expected_net": round(
            expected_net,
            2
        ),
        "actual_net": round(
            float(actual_net),
            2
        ),
        "difference": difference,
        "reason": reason
    }


# ============================================================
# BUILD GEMINI PROMPT
# ============================================================

def build_prompt(
    transaction,
    python_validation
):

    return f"""
You are an AI financial exception analyst.

Analyze ONLY the supplied transaction evidence.

Do NOT invent:
- amounts
- transactions
- customers
- settlement records
- fees
- taxes
- adjustments
- explanations unsupported by evidence

If evidence is insufficient, return:
status = "UNRESOLVED"
recommended_action = "HUMAN_REVIEW"

IMPORTANT:

Python deterministic validation is authoritative
for arithmetic calculations.

You may explain the result, but you must NOT
contradict the Python validation.

Transaction:

{json.dumps(
    transaction,
    indent=2,
    default=str
)}

Python financial validation:

{json.dumps(
    python_validation,
    indent=2,
    default=str
)}

Return ONLY valid JSON matching the required schema.

Rules:

1. Use only supplied evidence.
2. Do not hallucinate missing information.
3. If Python validation is invalid, do not approve
   the settlement.
4. If Python validation shows an unexplained difference,
   recommend HUMAN_REVIEW unless the supplied evidence
   clearly explains the difference.
5. Confidence must be between 0 and 1.
6. Evidence must contain only facts from the transaction.
7. If the settlement calculation is valid, it may be
   marked RESOLVED.
"""


# ============================================================
# SAFE FALLBACK
# ============================================================

def fallback_result(
    transaction,
    python_validation,
    error_message="AI processing failed."
):

    return {
        "transaction_id":
            transaction.get(
                "transaction_id"
            ),

        "exception_type":
            transaction.get(
                "exception_type"
            ),

        "explanation":
            "Gemini exception analysis could not "
            "be completed.",

        "evidence": [],

        "calculation": "",

        "status":
            "UNRESOLVED",

        "confidence":
            0.0,

        "recommended_action":
            "HUMAN_REVIEW",

        "override":
            True,

        "override_reason":
            error_message,

        "llm_attempt":
            0,

        "python_validation":
            python_validation
    }


# ============================================================
# EXTRACT JSON SAFELY
# ============================================================

def parse_json_response(text):

    text = text.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```\s*$",
        "",
        text
    )

    text = text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Try to find JSON object
    # --------------------------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        json_text = text[
            start:end + 1
        ]

        return json.loads(
            json_text
        )

    raise ValueError(
        "Gemini returned invalid JSON."
    )


# ============================================================
# VALIDATE AI DECISION
# ============================================================

def validate_ai_decision(
    result,
    python_validation
):

    # --------------------------------------------------------
    # Ensure confidence is valid
    # --------------------------------------------------------

    confidence = result.get(
        "confidence",
        0
    )

    try:

        confidence = float(
            confidence
        )

    except:

        confidence = 0.0

    confidence = max(
        0.0,
        min(
            1.0,
            confidence
        )
    )

    result["confidence"] = confidence

    # --------------------------------------------------------
    # HALLUCINATION / CONTRADICTION PROTECTION
    # --------------------------------------------------------

    if not python_validation["valid"]:

        ai_action = result.get(
            "recommended_action",
            ""
        )

        # AI must not approve an invalid settlement

        if ai_action == "APPROVE_SETTLEMENT":

            result["override"] = True

            result[
                "override_reason"
            ] = (
                "Gemini recommended settlement approval "
                "but Python deterministic validation "
                "detected a financial difference."
            )

            result[
                "status"
            ] = "UNRESOLVED"

            result[
                "recommended_action"
            ] = "HUMAN_REVIEW"

            result[
                "confidence"
            ] = 0.0

        # Also prevent RESOLVED status

        if result.get(
            "status"
        ) == "RESOLVED":

            result["override"] = True

            result[
                "override_reason"
            ] = (
                "Python financial validation failed. "
                "AI resolution cannot be trusted."
            )

            result[
                "status"
            ] = "UNRESOLVED"

            result[
                "recommended_action"
            ] = "HUMAN_REVIEW"

    # --------------------------------------------------------
    # If validation is valid, keep deterministic result
    # --------------------------------------------------------

    else:

        # A valid calculation can be resolved,
        # but AI should still provide explanation.

        if result.get(
            "recommended_action"
        ) == "HUMAN_REVIEW":

            result["override"] = False

    return result


# ============================================================
# MAIN LLM FUNCTION
# ============================================================

def explain_exception(
    transaction,
    max_retries=3
):

    # --------------------------------------------------------
    # STEP 1
    # Python validation happens BEFORE Gemini
    # --------------------------------------------------------

    python_validation = (
        validate_financial_data(
            transaction
        )
    )

    # --------------------------------------------------------
    # STEP 2
    # Build prompt
    # --------------------------------------------------------

    prompt = build_prompt(
        transaction,
        python_validation
    )

    # --------------------------------------------------------
    # STEP 3
    # Gemini configuration
    # --------------------------------------------------------

    config = types.GenerateContentConfig(

        response_mime_type="application/json",

        response_schema=RESPONSE_SCHEMA,

        temperature=0.1
    )

    # --------------------------------------------------------
    # STEP 4
    # Retry Gemini
    # --------------------------------------------------------

    for attempt in range(
        1,
        max_retries + 1
    ):

        print(
            f"Gemini analysis attempt "
            f"{attempt}/{max_retries}..."
        )

        try:

            response = (
                client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=config
                )
            )

            # ------------------------------------------------
            # Extract response
            # ------------------------------------------------

            text = response.text

            result = parse_json_response(
                text
            )

            # ------------------------------------------------
            # Add transaction ID
            # ------------------------------------------------

            result[
                "transaction_id"
            ] = transaction.get(
                "transaction_id"
            )

            # ------------------------------------------------
            # Validate AI result
            # ------------------------------------------------

            result = validate_ai_decision(
                result,
                python_validation
            )

            # ------------------------------------------------
            # Add validation result
            # ------------------------------------------------

            result[
                "python_validation"
            ] = python_validation

            result[
                "llm_attempt"
            ] = attempt

            return result

        except Exception as e:

            error_message = str(e)

            print(
                f"Gemini attempt {attempt} failed: "
                f"{error_message}"
            )

            # ================================================
            # 429 = QUOTA EXHAUSTED
            # DO NOT RETRY
            # ================================================

            if (
                "429" in error_message
                or
                "RESOURCE_EXHAUSTED"
                in error_message
            ):

                print(
                    "Gemini quota exhausted."
                )

                print(
                    "Stopping retries and "
                    "sending record to HUMAN_REVIEW."
                )

                result = fallback_result(
                    transaction,
                    python_validation,
                    "Gemini API quota exhausted."
                )

                result[
                    "llm_attempt"
                ] = attempt

                return result

            # ================================================
            # 503 = TEMPORARY SERVER FAILURE
            # Retry
            # ================================================

            if (
                "503" in error_message
                or
                "UNAVAILABLE"
                in error_message
            ):

                if attempt < max_retries:

                    wait_time = (
                        2 ** attempt
                    )

                    print(
                        f"Retrying in "
                        f"{wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue

            # ================================================
            # OTHER ERROR
            # ================================================

            result = fallback_result(
                transaction,
                python_validation,
                error_message
            )

            result[
                "llm_attempt"
            ] = attempt

            return result

    # ========================================================
    # FINAL FALLBACK
    # ========================================================

    return fallback_result(
        transaction,
        python_validation,
        "Maximum Gemini attempts reached."
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_transaction = {

        "transaction_id":
            "TX045",

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

        "exception_type":
            "SETTLEMENT_DIFFERENCE",

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
        "\n=========================================="
    )

    print(
        "AI FINANCE CONTROLLER"
    )

    print(
        "GEMINI LLM EXCEPTION ANALYSIS"
    )

    print(
        "=========================================="
    )

    result = explain_exception(
        test_transaction
    )

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )

    print(
        "=========================================="
    )
