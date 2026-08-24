import re

KEYWORD_RULES = [
    ("fraud_suspected", [r"\bfraud\b", r"\brisk flag", r"suspicious"]),
    ("mandate_revoked", [r"mandate revoked", r"mandate cancel", r"consent withdrawn"]),
    ("card_expired", [r"card.*expir", r"update.*card", r"card details"]),
    ("issuer_timeout", [
        r"timeout", r"gateway timeout", r"server", r"unknown.*status",
        r"partially processed", r"mandate execution failed",
    ]),
    ("insufficient_funds", [r"insufficient", r"low balance", r"declined by issuer", r"soft decline"]),
]


def diagnose(failure_reason_code, raw_bank_message=""):
    KNOWN_CATEGORIES = {
        "insufficient_funds", "card_expired", "issuer_timeout",
        "mandate_revoked", "fraud_suspected",
    }

    if failure_reason_code in KNOWN_CATEGORIES:
        return failure_reason_code, "already_labeled", True

    if failure_reason_code != "ambiguous_bank_error":
        return "unresolved", "unknown_input_label", False

    message = raw_bank_message.lower()
    for category, patterns in KEYWORD_RULES:
        for pattern in patterns:
            if re.search(pattern, message):
                return category, f"matched_pattern:'{pattern}'", True

    return "unresolved", "no_keyword_match", False


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("../outputs/failed_payments.csv")
    ambiguous = df[df["failure_reason_code"] == "ambiguous_bank_error"].copy()

    results = ambiguous.apply(
        lambda row: diagnose(row["failure_reason_code"], row["raw_bank_message"]), axis=1
    )
    ambiguous["diagnosed_category"] = [r[0] for r in results]
    ambiguous["rule_matched"] = [r[1] for r in results]
    ambiguous["confident"] = [r[2] for r in results]

    print(f"Diagnosed {len(ambiguous)} ambiguous cases:\n")
    print(ambiguous["diagnosed_category"].value_counts())
    print(f"\nUnresolved (honestly couldn't classify): "
          f"{(ambiguous['diagnosed_category'] == 'unresolved').sum()} "
          f"of {len(ambiguous)}")