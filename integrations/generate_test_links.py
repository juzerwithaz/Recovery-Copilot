import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from integrations.razorpay_client import create_payment_link

SAMPLE_SIZE = 5
LINK_GENERATING_ACTIONS = {"send_payment_link_update_card", "send_payment_link_timed_nudge"}


def main():
    audit_log = pd.read_csv("../outputs/audit_log.csv")
    failed_payments = pd.read_csv("../outputs/failed_payments.csv")

    candidates = audit_log[audit_log["policy_action"].isin(LINK_GENERATING_ACTIONS)].copy()

    if len(candidates) == 0:
        print("No cases found where policy action generates a payment link. Nothing to do.")
        return

    sample = candidates.sample(n=min(SAMPLE_SIZE, len(candidates)), random_state=42)
    sample = sample.merge(
        failed_payments[["payment_id", "amount"]], on="payment_id", how="left"
    )

    results = []
    for _, row in sample.iterrows():
        result = create_payment_link(
            amount_rupees=row["amount"],
            description=f"Recovery Copilot - {row['diagnosed_category']} recovery attempt",
            reference_id=row["payment_id"],
            diagnosed_category=row["diagnosed_category"],
            rule_id=row["policy_rule_id"],
        )

        if "error" in result:
            print(f"FAILED for {row['payment_id']}: {result['error']}")
        else:
            print(f"Created link for {row['payment_id']} ({row['diagnosed_category']}): {result['short_url']}")

        results.append({
            "payment_id": row["payment_id"],
            "diagnosed_category": row["diagnosed_category"],
            "amount": row["amount"],
            **result,
        })

    pd.DataFrame(results).to_csv("../outputs/generated_payment_links.csv", index=False)
    print(f"\nSaved {len(results)} results to outputs/generated_payment_links.csv")


if __name__ == "__main__":
    main()