def validate_ai_decision(ai_result, financial_validation):

    python_valid = financial_validation["valid"]

    # -------------------------------------------------
    # Python says the evidence is NOT sufficient
    # -------------------------------------------------

    if not python_valid:

        # Even if Gemini says RESOLVED,
        # Python overrides it.

        return {
            "status": "UNRESOLVED",
            "recommended_action": "HUMAN_REVIEW",
            "override": True,
            "override_reason": (
                "AI resolution rejected because "
                "financial evidence does not fully "
                "support the resolution."
            )
        }

    # -------------------------------------------------
    # Python says evidence is valid
    # -------------------------------------------------

    if ai_result["status"] == "RESOLVED":

        return {
            "status": "RESOLVED",
            "recommended_action": ai_result[
                "recommended_action"
            ],
            "override": False,
            "override_reason": ""
        }

    # AI itself says unresolved

    return {
        "status": "UNRESOLVED",
        "recommended_action": "HUMAN_REVIEW",
        "override": False,
        "override_reason": (
            "AI could not safely resolve the exception."
        )
    }