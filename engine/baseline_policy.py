MAX_ATTEMPTS = 3


def decide_action_naive(diagnosed_category, attempt_number):
    if attempt_number > MAX_ATTEMPTS:
        return {
            "action": "stop_naive_no_cap_logic",
            "rule_id": "NAIVE_max_attempts",
            "reason": "Even the naive baseline stops at some point - kept fair, not infinite spam.",
        }

    return {
        "action": "generic_retry_and_sms",
        "rule_id": "NAIVE_contact_everyone_same_way",
        "reason": "Naive baseline: same treatment regardless of failure reason.",
    }