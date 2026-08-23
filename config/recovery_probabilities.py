RECOVERY_CONFIG = {
    "insufficient_funds": {
        "contact_mode": "repeated_nudge",
        "base_conversion_prob": 0.30,
        "decay_per_day": 0.015,
        "payday_boost": 0.15,
        "payday_window_days": 2,
        "avg_payday_cycle_days": 30,
        "source": (
            "benchmark-derived: general shape informed by published subscription "
            "dunning research (roughly 2% of monthly subscription payments fail, "
            "accounting for ~22% of at-risk ARR if unaddressed) and standard "
            "dunning cadence conventions (e.g. Day 1/3/7 retry windows)."
        ),
    },
    "card_expired": {
        "contact_mode": "one_shot_link",
        "base_conversion_prob": 0.50,
        "decay_per_day": 0.0,
        "payday_boost": 0.0,
        "payday_window_days": 0,
        "avg_payday_cycle_days": 0,
        "source": (
            "policy-choice: modeled as a one-shot conversion event since it "
            "requires a single deliberate customer action (updating card details), "
            "not a passive wait."
        ),
    },
    "issuer_timeout": {
        "contact_mode": "auto_silent_retry",
        "base_conversion_prob": 0.80,
        "decay_per_day": 0.0,
        "payday_boost": 0.0,
        "payday_window_days": 0,
        "avg_payday_cycle_days": 0,
        "source": (
            "policy-choice: transient infra failures are not customer-caused "
            "and typically resolve on a fast silent retry; no customer contact needed."
        ),
    },
    "mandate_revoked": {
        "contact_mode": "no_contact",
        "base_conversion_prob": 0.0,
        "decay_per_day": 0.0,
        "payday_boost": 0.0,
        "payday_window_days": 0,
        "avg_payday_cycle_days": 0,
        "source": "policy-choice: consent was explicitly withdrawn; recovery is deliberately not attempted.",
    },
    "fraud_suspected": {
        "contact_mode": "human_escalation",
        "base_conversion_prob": 0.0,
        "decay_per_day": 0.0,
        "payday_boost": 0.0,
        "payday_window_days": 0,
        "avg_payday_cycle_days": 0,
        "source": "policy-choice: risk-flagged cases are strictly defense-only and always routed to human review.",
    },
}

NAIVE_BASELINE_CONFIG = {
    "contact_mode": "generic_retry",
    "base_conversion_prob": 0.25,
    "decay_per_day": 0.02,
    "payday_boost": 0.0,
    "payday_window_days": 0,
    "avg_payday_cycle_days": 0,
    "source": "policy-choice: represents a naive same-treatment-for-everyone baseline for comparison.",
}