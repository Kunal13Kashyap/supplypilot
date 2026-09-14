# 001 — Hybrid agent architecture

## Context

ProcureAI must investigate purchasing cases, call tools, decide, execute, and validate. A single LLM prompt cannot own this loop.

## Decision

Use LangGraph for an explicit multi-step state machine. The LLM plans explanations and can request knowledge search. Deterministic Python owns replenishment math, constraints, and all database writes.

## Reasoning

Reviewers can observe each node. Evaluation tests assert tool use and numeric outcomes independently of the model.

## Tradeoffs

LangGraph adds a dependency. A hand-rolled FSM would be smaller. LangGraph matches the assignment and keeps transitions explicit.

## Consequences

Agent runs persist `ToolCall`, `Decision`, `ValidationEvent`. MOCK and OpenAI providers share the same graph.
