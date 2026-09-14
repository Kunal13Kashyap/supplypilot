# 004 — LLM vs deterministic rules

## Context

LLMs are unreliable at arithmetic and policy.

## Decision

`calculate_replenishment` and `validate_purchase_quantity` are pure functions. The LLM never receives a database session. Structured `DecisionOutput` numbers are taken from the engine even when OpenAI writes the narrative.

## Reasoning

Evaluation must be stable in MOCK_MODE without an API key.

## Tradeoffs

The model cannot invent a creative qty that violates storage. That is intended.

## Consequences

Prompts contain no business formula. Formula lives in `app/rules/replenishment.py` and seeded `business_rules`.
