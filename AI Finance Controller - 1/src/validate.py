def validate_financial_evidence(transaction):
    """
    Python is the financial authority.
    Independently verifies settlement arithmetic.
    """

    settlement = transaction.get("settlement")

    if not settlement:
        return {
            "valid": False,
            "reason": "Settlement record is missing."
        }

    gross = settlement.get("gross_amount")
    fee = settlement.get("fee")
    tax = settlement.get("tax")
    adjustment = settlement.get("adjustment")
    actual_net = settlement.get("net_amount")

    # Check required values
    values = [gross, fee, tax, adjustment, actual_net]

    if any(value is None for value in values):
        return {
            "valid": False,
            "reason": "Required settlement evidence is missing."
        }

    # Python independently calculates expected amount
    expected_net = (
        gross
        - fee
        - tax
        + adjustment
    )

    difference = round(
        expected_net - actual_net,
        2
    )

    if difference == 0:
        return {
            "valid": True,
            "expected_net": expected_net,
            "actual_net": actual_net,
            "difference": 0,
            "reason": "Settlement calculation is fully supported."
        }

    return {
        "valid": False,
        "expected_net": expected_net,
        "actual_net": actual_net,
        "difference": difference,
        "reason": (
            f"Unexplained settlement difference: "
            f"{abs(difference):.2f}"
        )
    }

if __name__ == "__main__":

    transaction = {
        "settlement": {
            "gross_amount": 10000,
            "fee": 100,
            "tax": 0,
            "adjustment": 0,
            "net_amount": 9400
        }
    }

    result = validate_financial_evidence(transaction)

    print(result)