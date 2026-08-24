from datetime import datetime

MAX_ATTEMPTS = 3
QUIET_HOURS_START = 21
QUIET_HOURS_END = 9


def decide_action(diagnosed_category, attempt_number, action_hour=None):
    if action_hour is None:
        action_hour = datetime.now().hour

    if diagnosed_category == "mandate_revoked":
        return {
            "action": "no_contact",
            "rule_id": "R1_never_contact_revoked_mandate",
            "reason": "Customer explicitly withdrew consent. Contacting again is not just wasteful, it's wrong.",
        }

    if diagnosed_category == "fraud_suspected":
        return {
            "action": "escalate_to_human_risk_review",
            "rule_id": "R2_fraud_always_human_reviewed",
            "reason": "Risk-flagged cases are strictly defense-only and never auto-actioned.",
        }

    if diagnosed_category == "unresolved":
        return {
            "action": "escalate_to_human_review",
            "rule_id": "R3_unresolved_diagnosis_escalates",
            "reason": "Diagnosis engine could not confidently classify this case - escalated rather than guessed.",
        }

    if attempt_number > MAX_ATTEMPTS:
        return {
            "action": "escalate_to_human_review",
            "rule_id": "R4_max_attempts_exhausted",
            "reason": f"Exceeded max attempt cap of {MAX_ATTEMPTS} - stopping automated retries per policy.",
        }

    in_quiet_hours = action_hour >= QUIET_HOURS_START or action_hour < QUIET_HOURS_END

    if diagnosed_category == "issuer_timeout":
        return {
            "action": "silent_auto_retry",
            "rule_id": "R5_transient_failure_silent_retry",
            "reason": "Not customer-caused; safe to retry automatically without any customer contact.",
        }

    if diagnosed_category == "card_expired":
        if in_quiet_hours:
            return {
                "action": "defer_contact_to_quiet_hours_end",
                "rule_id": "R6_quiet_hours_gate",
                "reason": f"Outreach blocked - action_hour={action_hour} falls in quiet hours (9pm-9am).",
            }
        return {
            "action": "send_payment_link_update_card",
            "rule_id": "R7_card_expired_one_shot_link",
            "reason": "One-shot action required from customer - send update-card link.",
        }

    if diagnosed_category == "insufficient_funds":
        if in_quiet_hours:
            return {
                "action": "defer_contact_to_quiet_hours_end",
                "rule_id": "R6_quiet_hours_gate",
                "reason": f"Outreach blocked - action_hour={action_hour} falls in quiet hours (9pm-9am).",
            }
        return {
            "action": "send_payment_link_timed_nudge",
            "rule_id": "R8_insufficient_funds_timed_nudge",
            "reason": "Nudge customer with a payment link, timed to avoid nagging while still likely broke.",
        }

    return {
        "action": "escalate_to_human_review",
        "rule_id": "R9_unhandled_category_failsafe",
        "reason": f"No policy rule matched diagnosed_category='{diagnosed_category}' - failing safe.",
    }


if __name__ == "__main__":
    import pandas as pd
    from diagnosis_engine import diagnose

    df = pd.read_csv("../outputs/failed_payments.csv")

    decisions = []
    for _, row in df.iterrows():
        diagnosed_category, rule_matched, confident = diagnose(
            row["failure_reason_code"], row.get("raw_bank_message", "")
        )
        decision = decide_action(diagnosed_category, row["attempt_number"], action_hour=14)
        decisions.append({
            "payment_id": row["payment_id"],
            "original_label": row["failure_reason_code"],
            "diagnosed_category": diagnosed_category,
            "diagnosis_rule": rule_matched,
            "attempt_number": row["attempt_number"],
            "policy_action": decision["action"],
            "policy_rule_id": decision["rule_id"],
            "policy_reason": decision["reason"],
        })

    result_df = pd.DataFrame(decisions)
    result_df.to_csv("../outputs/audit_log.csv", index=False)

    print(f"Processed {len(result_df)} cases. Audit log saved to outputs/audit_log.csv\n")
    print("Action distribution:")
    print(result_df["policy_action"].value_counts())
    print("\nRule distribution:")
    print(result_df["policy_rule_id"].value_counts())