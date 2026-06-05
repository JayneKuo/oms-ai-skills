---
name: exception
description: Diagnose OMS sales-order EXCEPTION status. Use when the user asks why an order is in exception, how to resolve it, or which exception orders need action. Must provide cause, solution, and next step.
---

# Exception Skill

## Runtime Guardrails

- Use this skill when the user asks why a sales order is in EXCEPTION, how to resolve it, or which exception orders need action.
- Always explain cause, solution, and next step. Never answer with only "the order is EXCEPTION".
- Base causes on real evidence: order detail, diagnosis fields, available actions, recommended next step, inventory summary, allocation evidence, dispatch logs, or explicit API errors.
- If evidence is missing, say what is confirmed and what is still unconfirmed. Do not invent inventory, routing, warehouse, or rule causes.
- Do not execute reopen, cancel, manual allocation, hold release, or replenishment creation here. Route confirmed actions to `operations`, `allocation`, `hold`, or `replenishment`.
- Prefer `diagnose_exception.py` over raw `query_orders.py` / `get_order_detail.py` when the user asks for cause, solution, or a batch action list.
- EXCEPTION list rows can be stale. Always verify current detail status before recommending reopen, allocation, or replenishment.
- If `reserve1` or another detail field explicitly says a product is out of stock, treat that as confirmed cause and route next step to `replenishment`; reopen should happen only after inventory/replenishment is handled and the business confirms retry.
- If detail status is no longer `EXCEPTION`, tell the user it moved out of exception and do not recommend exception actions.

## Scope

- Query EXCEPTION orders and verify their latest detail status.
- Extract confirmed exception causes from real detail fields, diagnosis fields, inventory evidence, allocation evidence, dispatch/log evidence, or explicit OMS errors.
- Recommend the business solution: replenish inventory, fix allocation blocker, reopen after the blocker is resolved, or manual review.
- Support batch diagnosis with compact per-order results.

## User Reply Template

```text
Result: [whether the order is currently EXCEPTION]
Evidence: [confirmed fields/logs/errors, or evidence gap]
Explanation: [business cause, such as out of stock, allocation blocker, or unconfirmed cause]
Solution: [replenishment / allocation check / operations reopen after blocker resolved / manual review]
Next step: [focused skill handoff or user confirmation needed]
```

## Script Inventory

```bash
python scripts/query_orders.py --status EXCEPTION --size 20
python scripts/get_order_detail.py --order SO00361770
python scripts/diagnose_exception.py --order SO00361770
python scripts/diagnose_exception.py --from-list --size 10
python scripts/diagnose_exception.py --orders SO001 SO002
```

## Forbidden

- Do not only say "the order is EXCEPTION" without cause, solution, and next step.
- Do not guess inventory, routing, warehouse, or rule causes without evidence.
- Do not execute reopen, cancel, allocation, hold release, or PO creation in this skill.
- Do not expose credentials or full raw payloads by default.