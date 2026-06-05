---
name: allocation
description: Diagnose and operate OMS sales-order allocation, dispatch assignment, reopen-for-allocation retry, remaining quantity, manual/auto allocation eligibility, and allocation explanations. Use when the user asks which warehouse an order went to, why it went there, whether allocation can be performed, or whether an exception order should be reopened to retry allocation.
---

# Allocation Skill

## Manual Dispatch Types

The allocation skill must distinguish these dispatch modes:

- `HAND_WHOLE_DISPATCH`: manually assign the whole order to a specified warehouse.
- `HAND_SKU_DISPATCH`: manually assign specific SKU quantities to specified warehouse(s). Use this when the user says to allocate by SKU or split SKUs across warehouses.
- `HAND_WHOLE_AUTO_DISPATCH`: ask OMS to auto-dispatch the whole order by current dispatch rules.
- `HAND_SKU_AUTO_DISPATCH`: ask OMS to auto-dispatch specific SKU quantities by current dispatch rules.
- `REOPEN_DISPATCH` / order reopen: retry allocation/dispatch after an EXCEPTION blocker is resolved. This belongs to allocation because the business outcome is re-entering allocation, not a generic order operation.

Before any dispatch write, check manual allocation eligibility and remaining quantities. Specified-warehouse dispatch requires a confirmed warehouse name/accounting code if OMS needs it. Auto-dispatch does not require a warehouse, but the user-facing answer must say OMS will re-run allocation rules rather than force a chosen warehouse.

If the order is already fully allocated (`remaining=0`) or OMS says the current status does not support manual allocation, do not submit a manual/auto allocation request by default. Explain the existing allocation details instead: assigned warehouse, dispatch number/status, SKU quantities, remaining quantity, and why there are no allocatable products. A rejected or blocked allocation attempt is not a failure to execute; it is a business-state answer that the order is already allocated or not eligible.

For automatic allocation explanations, first query the dispatch explain log endpoint:

```text
GET /api/linker-oms/opc/public-api/dispatch/dispatch-log/explain?orderNo={orderNo}
```

This endpoint can return the concrete routing rule check, fulfillment items, available warehouses, inventory checks, decisive rule/event, and final dispatch result. Use it as the highest-priority source for "why this warehouse?".

After any successful manual/auto dispatch submission, the agent must re-read the order and return the actual post-allocation result to the user. `manual_allocate.py` now includes `postAllocationCheck` when OMS returns `code=0`; user-facing replies must use it to show the assigned warehouse, dispatch number/status, SKU quantities, remaining quantity, and dispatch explain log reason when available. Do not stop at "allocation submitted successfully."

Examples:

```bash
python scripts/manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_AUTO_DISPATCH --confirm-allocation
python scripts/manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_DISPATCH --warehouse "Valley View" --accounting-code 889 --confirm-allocation
python scripts/manual_allocate.py --order SO001 --dispatch-type HAND_SKU_AUTO_DISPATCH --sku SKU-A --qty 2 --confirm-allocation
python scripts/manual_allocate.py --order SO001 --dispatch-type HAND_SKU_DISPATCH --warehouse "Valley View" --sku SKU-A --qty 2 --confirm-allocation
```
## Runtime Guardrails

- Use this skill for warehouse allocation result, allocation evidence, manual-allocation eligibility, and remaining quantity checks.
- Read-only allocation checks/explanations may run directly. Any real manual/auto/force/batch allocation write must require user second confirmation before execution.
- This skill owns allocation writes too: manual specified-warehouse dispatch, manual SKU dispatch, whole-order auto dispatch, SKU auto dispatch, reopen-for-allocation retry, force allocation after second confirmation, and batch allocation. Do not delegate allocation execution to `operations`.
- Warehouse assignment reasons must come from real allocation, dispatch explain logs, route execution logs, or explicit order-detail evidence. Final warehouse/status fields alone prove the result, not the reason.
- Always check remaining quantity before recommending manual allocation. If remaining is zero, say manual allocation is not needed or not possible.
- For already allocated orders, do not say "I will allocate it" or "allocation failed" first. Say "this order is already allocated", show the dispatch/warehouse/SKU/remaining details, and explain there are no allocatable products left.
- Do not execute any real allocation write without user second confirmation. The confirmation prompt must include environment, order count/order list, dispatch mode, target warehouse/SKU quantities if applicable, business risk, and exact confirmation phrase.
- If evidence is incomplete, explain only the confirmed allocation result and say what evidence is still needed to explain the reason.
- If a dispatch write succeeds, include the post-submit warehouse result from `postAllocationCheck`. If the write is rejected, do not claim a new warehouse assignment.
- `manual_allocate.py` performs a pre-allocation check. When it returns `code=PRECHECK_BLOCKED` and `_request.submittedToOms=false`, the agent must explain the existing allocation state and must not claim that OMS executed a new allocation.

## User Reply Shape

1. Result: allocated warehouse or manual-allocation eligibility.
2. Reason: evidence-backed explanation, or clear evidence gap.
3. Actionability: whether manual intervention is needed.
4. Next step: check logs, ask for second confirmation before a real allocation write, or no action.

For successful allocation writes, the reply shape becomes:

1. Submission result: OMS accepted the allocation request.
2. Post-check result: actual warehouse, dispatch number/status, SKU quantities, and remaining quantity.
3. Reason confidence: confirmed reason, partial evidence, or reason not confirmed.
4. Next step: no action, check WMS/downstream status, or check routing trace/logs.

For blocked allocation writes where the order is already allocated:

1. Current state: order status, warehouse, dispatch number/status.
2. Item state: SKU, ordered quantity, remaining quantity.
3. Business conclusion: no allocatable products remain, so allocation was not submitted.
4. Reason/evidence: allocation items, order dispatch, and dispatch explain log when available.
5. Next step: check WMS/downstream progress or choose a different eligible order if the user wants to test manual allocation.

For allocation write requests before execution, reply first:

```text
This is a real OMS allocation action, so I will not execute it yet.
Environment: [staging/production]
Operation: [manual whole-order / manual SKU / auto whole-order / auto SKU / reopen allocation retry / force / batch allocation]
Targets: [order list, warehouse if specified, SKU quantities if specified]
Risk: [OMS may create or change dispatch allocation and downstream warehouse processing may start]
To proceed, reply exactly: [confirmation phrase]
```

## Warehouse Assignment Explanation Contract

When the user asks why an order was assigned to a warehouse, the answer must include these parts:

1. Result: the assigned warehouse, dispatch number/status if available, and current order status.
2. Dispatch method: manual specified warehouse, manual SKU split, auto whole-order dispatch, auto SKU dispatch, or unknown from available fields.
3. Confirmed reason: only state a reason when route execution, dispatch log, allocation evidence, or another explicit field proves it.
4. Evidence used: list the exact data source, such as `orderDispatchList`, `dispatchType`, allocation item remaining quantity, routing trace, or routing rule config.
5. Why not other warehouses: only answer this when candidate warehouse evaluation or rejection evidence exists.
6. Confidence: say whether the reason is confirmed, partially inferred, or not confirmed.
7. Next step: tell the user what to check next if the reason is not confirmed.

Evidence priority:

1. Dispatch explain log for this exact order: `/opc/public-api/dispatch/dispatch-log/explain?orderNo=...`.
2. Routing execution trace or dispatch log for this exact order.
3. Dispatch record fields such as `orderDispatchList`, `dispatchType`, `sendType`, dispatch status, operator, and timestamps.
4. Allocation item quantities and remaining quantity.
5. Routing rule configuration. This is context only unless a trace/log proves it was applied.

Do not say the order went to a warehouse because it was closest, had inventory, had highest priority, matched zip code, or matched SKU rules unless the fetched evidence explicitly says so. A final `warehouseName` proves the assignment result, not the selection reason.

Preferred script for this question:

```bash
python scripts/explain_warehouse_assignment.py --order SO00361770
python scripts/explain_warehouse_assignment.py --order SO00361770 --compare-warehouse "Valley View"
```

## Script Inventory

```bash
python scripts/check_manual_allocation.py --order SO00361770
python scripts/get_allocation_items.py --order SO00361770
python scripts/get_order_detail.py --order SO00361770
python scripts/get_routing_rules.py
python scripts/explain_warehouse_assignment.py --order SO00361770
python scripts/reopen_order.py --order SO00361770 --confirm-reopen
python scripts/manual_allocate.py --order SO00361770 --warehouse WH-001 --skus '[{"sku":"SKU-A","qty":2}]' --confirm-allocation
python scripts/batch_allocation.py --action explain --orders SO001 SO002
python scripts/batch_allocation.py --action items --orders SO001 SO002
python scripts/batch_allocation.py --action check --orders SO001 SO002
python scripts/batch_allocation.py --action reopen --orders SO001 SO002 --confirm-allocation
python scripts/batch_allocation.py --action manual_allocate --orders SO001 SO002 --dispatch-type HAND_WHOLE_AUTO_DISPATCH --confirm-allocation
```

## Batch Execution Contract

Support batch user requests for every allocation capability:

- Batch query/explain: `batch_allocation.py --action explain`.
- Batch remaining items: `batch_allocation.py --action items`.
- Batch manual eligibility: `batch_allocation.py --action check`.
- Batch reopen allocation retry: `batch_allocation.py --action reopen`.
- Batch manual/auto allocation after user second confirmation: `batch_allocation.py --action manual_allocate`.

When OMS has no dedicated batch endpoint, use bounded per-order execution instead of a long serial loop:

- Keep concurrency bounded (`--max-workers`, default 4, maximum 8).
- Return per-order results; one failed/slow order must not block the rest.
- Keep user-facing batch output compact: order, status, warehouse/dispatch, remaining, action result, and next step.
- If many orders are requested, process in chunks and return progress/partial results instead of waiting indefinitely.
- For batch writes, run the same precheck as single writes. Already allocated orders must be reported as `not_submitted`, not as failed allocation.

## User Reply Template

```text
I checked this order's allocation state in staging.
Result: [allocated warehouse / eligibility / remaining quantity].
Reason: [evidence from dispatch explain, dispatch record, allocation items, or explicit evidence gap].
Next step: [no action / check WMS / ask for second confirmation before a real allocation write].
```

## Forbidden

- Do not treat the final warehouse field as the allocation reason.
- Do not recommend manual allocation when remaining quantity is `0`.
- Do not explain "why this warehouse" without dispatch/routing/allocation evidence.
