# 003 — Validation feedback loop

## Context

Enterprise adapters lie. The agent must not trust its own write.

## Decision

After every PO mutation the system re-reads the PO and compares expected vs actual quantity plus MOQ, budget, storage, and supplier caps. Failure enters recovery (modify once). A second failure escalates.

## Reasoning

Observe → Act → Validate → Recover is the assignment's core, not prompt → answer.

## Tradeoffs

Recovery is limited to one retry to keep the demo bounded.

## Consequences

`PC-1002` forces a qty mismatch (400 requested, 500 written) then recovers to 400.
