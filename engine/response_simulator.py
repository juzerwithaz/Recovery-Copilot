import random
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.recovery_probabilities import RECOVERY_CONFIG, NAIVE_BASELINE_CONFIG


def simulate_outcome(failure_reason, days_since_failure=0, rng=None, use_naive_baseline=False):
    rng = rng or random

    if use_naive_baseline:
        cfg = NAIVE_BASELINE_CONFIG
    else:
        if failure_reason not in RECOVERY_CONFIG:
            raise ValueError(
                f"Unknown failure_reason '{failure_reason}'. "
                f"This must be a diagnosed category, not a raw/ambiguous label."
            )
        cfg = RECOVERY_CONFIG[failure_reason]

    if cfg["contact_mode"] == "no_contact":
        return False, 0.0

    prob = cfg["base_conversion_prob"]
    MAX_DECAY_DAYS = 14
    effective_days = min(days_since_failure, MAX_DECAY_DAYS)
    prob -= cfg["decay_per_day"] * effective_days

    if cfg["payday_boost"] > 0 and cfg["avg_payday_cycle_days"] > 0:
        day_in_cycle = days_since_failure % cfg["avg_payday_cycle_days"]
        if day_in_cycle <= cfg["payday_window_days"]:
            prob += cfg["payday_boost"]

    prob = max(0.0, min(1.0, prob))
    recovered = rng.random() < prob
    return recovered, prob


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("../outputs/failed_payments.csv")
    known = df[df["failure_reason_code"] != "ambiguous_bank_error"].copy()

    ATTEMPT_ACTION_DELAY_DAYS = {1: 0, 2: 2, 3: 5}
    known["days_since_failure"] = known["attempt_number"].map(ATTEMPT_ACTION_DELAY_DAYS)

    results = []
    for _, row in known.iterrows():
        recovered, prob = simulate_outcome(row["failure_reason_code"], row["days_since_failure"])
        results.append({"failure_reason_code": row["failure_reason_code"], "recovered": recovered, "prob_used": prob})

    res_df = pd.DataFrame(results)
    print("Single-run recovery rate by category (sanity check only - not final metrics):\n")
    summary = res_df.groupby("failure_reason_code").agg(
        cases=("recovered", "count"),
        recovered_count=("recovered", "sum"),
        avg_prob_used=("prob_used", "mean"),
    )
    summary["recovery_rate"] = (summary["recovered_count"] / summary["cases"]).round(3)
    print(summary)
    print(f"\nOverall recovery rate (known categories only, single run): "
          f"{res_df['recovered'].mean():.3f}")