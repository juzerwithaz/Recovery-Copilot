# Recovery-Copilot

An AI-native system that diagnoses *why* a subscription payment failed and responds accordingly — instead of retrying every failure the same way.

## The problem

Auto-debits on subscriptions fail constantly: expired cards, insufficient funds, bank server timeouts, revoked mandates, fraud flags. Most recovery tools treat every failure identically — retry the card, send the same SMS, repeat. That's not just inefficient, it's sometimes the wrong thing to do entirely: contacting a customer who explicitly revoked their mandate isn't just wasteful, it's inappropriate.

Recovery Copilot diagnoses the actual failure reason first, then applies a bounded, explainable policy — including knowing when *not* to act at all.

## Why reason-aware beats one-size-fits-all

| Failure reason | What it really means | Right response |
|---|---|---|
| Bank server timeout | Not the customer's fault | Silent auto-retry, no contact needed |
| Card expired | One-time fixable action | Send a payment link to update the card |
| Insufficient funds | Temporarily short, will recover | Timed nudge, avoid nagging |
| Mandate revoked | Customer said no | **Never contact again** |
| Fraud suspected | Risk-flagged | **Always routed to a human**, never automated |

## Architecture

failed_payments.csv
│
▼
diagnosis_engine.py ──► resolves ambiguous bank messages into real
│ categories via keyword rules; honestly
│ escalates what it can't confidently classify
▼
policy_engine.py ──► hard-coded, non-negotiable rules decide the
│ action (retry / contact / escalate / stop).
│ No AI model has authority here — every
│ decision traces to an explicit rule ID.
▼
response_simulator.py ─► simulates whether the chosen action recovers
│ the payment, using a benchmark-anchored
│ probability config (config/recovery_probabilities.py)
▼
simulation_runner.py ─► runs our policy AND a naive baseline through
│ 100 trials each, reporting mean ± spread
▼
integrations/ ─► generates real Razorpay test-mode payment
links for a sample of live cases


Every decision is logged to `outputs/audit_log.csv` with the exact rule that triggered it — nothing here is a black box.

## Results (100-trial average, ours vs. a naive same-treatment-for-everyone baseline)

| Metric | Our policy | Naive baseline |
|---|---|---|
| Recovery rate | **45.8% ± 2.3%** | 30.5% ± 2.6% |
| Contact events per resolved case | **1.55** | 4.21 |
| Opt-out rate (repeated contact on unresolved cases) | **5.1%** | 8.3% |

Escalated cases (fraud, revoked mandates, unresolved diagnoses, exhausted retries) are always counted as **0% recovered by design** in these numbers — never excluded to inflate the headline rate.

## Project structure

data/ synthetic dataset generation
config/ probability config table, source-tagged (benchmark vs. policy choice)
engine/ diagnosis, policy, response simulation, multi-trial comparison
integrations/ real Razorpay test-mode Payment Links API integration
outputs/ generated data, audit logs, results (gitignored where regenerable)


## Running it

pip install -r requirements.txt

cd data && python generate_dataset.py
cd ../engine && python policy_engine.py
cd ../engine && python simulation_runner.py


For the real Razorpay integration, create a `.env` file in the project root:

RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret

Then:

cd integrations && python generate_test_links.py


## What this is honestly not

A production system, or a claim to have solved payment recovery at scale. This is a deliberately scoped prototype demonstrating an architecture pattern — diagnose first, then apply bounded and gated policy — on synthetic data, built to show how the real version should be reasoned about, not to be the real version.

## Status

Core pipeline complete: data generation, diagnosis, policy engine, audit trail, baseline comparison, and live Razorpay test-mode integration are all working end to end.