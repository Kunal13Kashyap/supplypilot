# 002 — Human-in-the-loop

## Context

High-impact purchase orders must not auto-execute.

## Decision

Risk is computed deterministically from financial impact, decision type, and quantity delta. LOW may execute. MEDIUM and HIGH wait for an approver. Approval is an audited API call that resumes the LangGraph execute subgraph.

## Reasoning

The assignment requires challenging recommendations and optional human approval. Binding approval to roles (buyer vs approver) makes the control plane visible.

## Tradeoffs

Demo users must switch accounts to approve. That is preferable to silently auto-approving the golden path.

## Consequences

`PC-1001` stops at `awaiting_approval`. Approver executes and validation follows.
