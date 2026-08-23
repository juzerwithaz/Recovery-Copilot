import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

NUM_SUBSCRIPTIONS = 350

FAILURE_REASONS = [
    "insufficient_funds",
    "card_expired",
    "issuer_timeout",
    "mandate_revoked",
    "fraud_suspected",
    "ambiguous_bank_error",
]
FAILURE_WEIGHTS = [0.36, 0.19, 0.14, 0.10, 0.15, 0.10]

BANK_NAMES = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Mahindra", "Yes Bank", "IDFC First"]
ERROR_CODES = ["E1042", "DC-77", "TXN_FAIL_09", "RC=51", "ERR203", "BNK-441", "AUTH_TIMEOUT_12"]

def generate_ambiguous_message():
    templates = [
        lambda: f"{random.choice(BANK_NAMES)}: transaction declined, code {random.choice(ERROR_CODES)}. contact bank.",
        lambda: f"Txn faild - {random.choice(ERROR_CODES)}. Pls retyr after sometime or contct suport.",
        lambda: f"Payment not completed. {random.choice(BANK_NAMES)} returned no further reason.",
        lambda: f"Declined by issuer ({random.choice(ERROR_CODES)}) - insufficient info from gateway response.",
        lambda: f"NPCI/{random.choice(BANK_NAMES).split()[0].upper()}: mandate execution failed, reason unspecified, retry advised after 24h.",
        lambda: f"Gateway timeout while contacting {random.choice(BANK_NAMES)} - transaction status unknown, may have partially processed.",
        lambda: f"{random.choice(ERROR_CODES)}: soft decline, customer action may be required but not specified by issuer.",
    ]
    return random.choice(templates)()

def random_time_component():
    return random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)

def build_subscription_pool(n):
    pool = []
    for i in range(1, n + 1):
        pool.append({
            "subscription_id": f"sub_{i}",
            "customer_id": f"cust_{1000 + i}",
        })
    return pool

subscriptions = build_subscription_pool(NUM_SUBSCRIPTIONS)

records = []
payment_counter = 1
base_date = datetime.now()

for sub in subscriptions:
    num_attempts = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1], k=1)[0]
    reason = random.choices(FAILURE_REASONS, weights=FAILURE_WEIGHTS, k=1)[0]
    amount = round(random.uniform(199, 4999), 2)

    if reason in ("mandate_revoked", "fraud_suspected"):
        num_attempts = 1

    days_ago_start = random.randint(3, 90)
    running_days_offset = days_ago_start
    for attempt in range(1, num_attempts + 1):
        if attempt > 1:
            running_days_offset -= random.randint(1, 3)
            running_days_offset = max(running_days_offset, 0)
        h, m, s = random_time_component()
        failed_at = (base_date - timedelta(days=running_days_offset)).replace(hour=h, minute=m, second=s)

        records.append({
            "payment_id": f"pay_{payment_counter:05d}",
            "customer_id": sub["customer_id"],
            "subscription_id": sub["subscription_id"],
            "amount": amount,
            "failure_reason_code": reason,
            "raw_bank_message": generate_ambiguous_message() if reason == "ambiguous_bank_error" else "",
            "attempt_number": attempt,
            "failed_at": failed_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
        payment_counter += 1

df = pd.DataFrame(records)
df = df.sort_values(["subscription_id", "attempt_number"]).reset_index(drop=True)
df.to_csv("failed_payments.csv", index=False)

print(f"Generated {len(df)} records across {NUM_SUBSCRIPTIONS} subscriptions.")
print("\nBreakdown by failure reason (row count):")
print(df["failure_reason_code"].value_counts())
print("\nAttempt-number distribution:")
print(df["attempt_number"].value_counts().sort_index())
print("\nSubscriptions with >1 recorded attempt:", (df.groupby("subscription_id").size() > 1).sum())
print("Any subscription_id mapped to >1 customer_id?",
      (df.groupby("subscription_id")["customer_id"].nunique() > 1).any())

def chain_is_ordered(group):
    g = group.sort_values("attempt_number")
    return g["failed_at"].is_monotonic_increasing

bad_chains = df.groupby("subscription_id").filter(
    lambda g: len(g) > 1 and not chain_is_ordered(g)
)
print("Subscriptions where attempt order disagrees with timestamp order:",
      bad_chains["subscription_id"].nunique())
print("fraud_suspected row count:", (df["failure_reason_code"] == "fraud_suspected").sum())
print("\nSaved to failed_payments.csv")