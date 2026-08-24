import random
import pandas as pd
from diagnosis_engine import diagnose
from policy_engine import decide_action, MAX_ATTEMPTS
from baseline_policy import decide_action_naive
from response_simulator import simulate_outcome

ATTEMPT_ACTION_DELAY_DAYS = {1: 0, 2: 2, 3: 5}
CONTACT_ACTIONS = {"send_payment_link_update_card", "send_payment_link_timed_nudge", "generic_retry_and_sms"}
ZERO_BY_DESIGN_ACTIONS = {
    "no_contact", "escalate_to_human_risk_review",
    "escalate_to_human_review", "stop_naive_no_cap_logic",
}


def run_single_trial(df, seed, use_naive):
    rng = random.Random(seed)

    total_failed_amount = 0.0
    total_recovered_amount = 0.0
    contact_events = 0
    resolved_subscriptions = 0
    opt_out_flagged = 0
    escalated_or_terminal = 0

    for sub_id, group in df.groupby("subscription_id"):
        group = group.sort_values("attempt_number")
        amount = group.iloc[0]["amount"]
        total_failed_amount += amount

        original_label = group.iloc[0]["failure_reason_code"]
        raw_message = group.iloc[0].get("raw_bank_message", "")
        diagnosed_category, _, _ = diagnose(original_label, raw_message)

        recovered_this_sub = False
        contacts_for_this_sub = 0
        unresolved_after_first_contact = False

        for _, row in group.iterrows():
            attempt = int(row["attempt_number"])
            days_since = ATTEMPT_ACTION_DELAY_DAYS.get(attempt, 5)

            if use_naive:
                decision = decide_action_naive(diagnosed_category, attempt)
            else:
                decision = decide_action(diagnosed_category, attempt, action_hour=14)

            action = decision["action"]

            if action in ZERO_BY_DESIGN_ACTIONS:
                escalated_or_terminal += 1
                break

            if action in CONTACT_ACTIONS:
                contacts_for_this_sub += 1
                contact_events += 1
                if contacts_for_this_sub >= 2 and unresolved_after_first_contact:
                    if diagnosed_category in ("card_expired", "mandate_revoked"):
                        opt_out_flagged += 1

            recovered, _ = simulate_outcome(
                diagnosed_category, days_since, rng=rng, use_naive_baseline=use_naive
            )

            if recovered:
                recovered_this_sub = True
                total_recovered_amount += amount
                break
            else:
                unresolved_after_first_contact = True

        if recovered_this_sub:
            resolved_subscriptions += 1

    n_subs = df["subscription_id"].nunique()
    return {
        "total_failed": total_failed_amount,
        "total_recovered": total_recovered_amount,
        "recovery_rate": total_recovered_amount / total_failed_amount if total_failed_amount else 0,
        "contact_events": contact_events,
        "contact_events_per_resolved": contact_events / resolved_subscriptions if resolved_subscriptions else 0,
        "resolved_subscriptions": resolved_subscriptions,
        "resolution_rate": resolved_subscriptions / n_subs if n_subs else 0,
        "opt_out_flagged": opt_out_flagged,
        "opt_out_rate": opt_out_flagged / n_subs if n_subs else 0,
        "escalated_or_terminal": escalated_or_terminal,
    }


def run_multi_trial(df, n_trials=100, use_naive=False, base_seed=1000):
    trials = [run_single_trial(df, base_seed + i, use_naive) for i in range(n_trials)]
    return pd.DataFrame(trials)


def summarize(trials_df, label):
    print(f"\n=== {label} (n={len(trials_df)} trials) ===")
    for col in ["recovery_rate", "resolution_rate", "opt_out_rate"]:
        mean = trials_df[col].mean()
        std = trials_df[col].std()
        print(f"{col}: {mean:.3f} ± {std:.3f}")
    print(f"escalated_or_terminal (per trial, mean): {trials_df['escalated_or_terminal'].mean():.1f}")
    print(f"contact_events (per trial, mean): {trials_df['contact_events'].mean():.1f}")
    print(f"contact_events per resolved case (mean): {trials_df['contact_events_per_resolved'].mean():.2f}")
    print(f"total_recovered (mean across trials): ₹{trials_df['total_recovered'].mean():,.0f} "
          f"of ₹{trials_df['total_failed'].mean():,.0f} failed")


if __name__ == "__main__":
    df = pd.read_csv("../outputs/failed_payments.csv")

    ours = run_multi_trial(df, n_trials=100, use_naive=False)
    naive = run_multi_trial(df, n_trials=100, use_naive=True)

    summarize(ours, "OUR REASON-AWARE POLICY")
    summarize(naive, "NAIVE BASELINE (same treatment for everyone)")

    print("\n=== HEADLINE COMPARISON ===")
    print(f"Recovery rate lift: {(ours['recovery_rate'].mean() - naive['recovery_rate'].mean()) * 100:.1f} "
          f"percentage points")
    print(f"Opt-out rate reduction: {(naive['opt_out_rate'].mean() - ours['opt_out_rate'].mean()) * 100:.1f} "
          f"percentage points lower with our policy")

    ours_out = ours.copy(); ours_out["policy"] = "ours"
    naive_out = naive.copy(); naive_out["policy"] = "naive"
    pd.concat([ours_out, naive_out]).to_csv("../outputs/multi_trial_results.csv", index=False)
    print("\nFull per-trial results saved to outputs/multi_trial_results.csv")