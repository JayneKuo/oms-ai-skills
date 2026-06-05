# Independent Agent Capability Inventory

Date: 2026-06-03

Recommended public entry point: `order-orchestrator`.

Matrix reference: `docs/agent-matrix.md`.

Legacy compatibility entry point: `sales-order`.

## Capability Summary

| Agent / Skill | Primary Role | Real Scripts | Can Execute Writes? | Launch Status |
| --- | --- | --- | --- | --- |
| `query` | Lightweight order lookup, basic status explanation, exact detail fallback, explicit test-order creation | `query_orders.py`, `get_order_detail.py`, `create_order.py` | Test-order creation only after second confirmation | Ready with guardrails |
| `exception` | EXCEPTION diagnosis and next-step planning | `query_orders.py`, `get_order_detail.py`, `diagnose_exception.py` | No | Ready with guardrails |
| `hold` | ON_HOLD diagnosis, hold evidence, hold rule query, rule-to-order candidate mapping, release assessment, natural-language hold rule drafting | `get_order_detail.py`, `get_hold_reason.py`, `get_allocation_items.py`, `release_hold.py`, `diagnose_hold.py`, `hold_rules.py`, `match_hold_rules_to_orders.py` | Release hold exists; hold rule create exists but defaults to dry-run and requires second confirmation for real submit | Ready with caution |
| `allocation` | Allocation result, automatic allocation reason, remaining quantity, manual-allocation eligibility, batch allocation workflows | `explain_warehouse_assignment.py`, `check_manual_allocation.py`, `get_allocation_items.py`, `manual_allocate.py`, `batch_allocation.py`, dispatch explain endpoint | Allocation reads and writes are owned here; writes require user second confirmation and precheck | Ready |
| `operations` | High-impact non-allocation order writes: cancel and reopen | `get_order_detail.py`, `reopen_order.py`, `cancel_order.py`, `batch_orders.py` | Yes, only after second confirmation; no allocation or hold-release writes | Ready for controlled use |
| `replenishment` | Replenishment recommendation, purchase warehouse explanation, single/split PO creation | `get_order_detail.py`, `suggest_purchase_order.py`, `get_routing_rules.py`, `create_purchase_order.py`, `create_purchase_order_split.py` | PO creation only after second confirmation | Ready with caution |
| `order-orchestrator` | Routing, shared context reuse, and multi-step composition | No direct scripts | No direct writes | Ready as default entry |

## Agent Details

### query

Use for:

- Sales order list lookup.
- Sales order detail lookup.
- Basic current status explanation.
- Confirming whether an order exists.
- Creating an explicitly requested test order, then checking status.
- Returning business summaries and recommended next focused skill.

Do not use for:

- EXCEPTION root-cause diagnosis.
- ON_HOLD rule or hold reason.
- Warehouse allocation reason.
- Replenishment planning.
- Cancel, reopen, release hold, manual allocation, or batch actions.

User-facing output:

- Translate statuses into business language.
- Say what is confirmed.
- Give the next skill/action if deeper diagnosis is needed.
- Do not expose raw API payloads by default.
- Exact SO-style order lookups must not be declared missing until detail fallback is checked.

### exception

Use for:

- Diagnosing orders currently in EXCEPTION.
- Explaining cause, solution, and next step.
- Separating stale EXCEPTION list results from current detail status.
- Deciding whether follow-up should go to allocation, replenishment, or operations.
- Batch diagnosis of EXCEPTION lists with per-order cause/action buckets.

Do not use for:

- Executing reopen/cancel/manual allocation/PO creation.
- Guessing causes without order detail, diagnosis fields, inventory/allocation evidence, dispatch evidence, or logs.

User-facing output:

- Result: still EXCEPTION or moved out of EXCEPTION.
- Reason: evidence-backed cause or explicit evidence gap.
- Solution: business action.
- Next step: route to correct skill or ask for confirmation.
- If detail field `reserve1` confirms out of stock, show affected SKU and route to replenishment before reopen.

### hold

Use for:

- Checking whether an order is currently ON_HOLD.
- Finding hold-rule evidence.
- Querying hold rules and inspecting rule details.
- Checking active hold count by rule.
- Mapping ON_HOLD orders to active or historical candidate rules.
- Drafting hold rules from natural language.
- Creating hold rules only after user second confirmation.
- Explaining release-hold result.
- Handling unavailable hold-rule endpoint without guessing.
- Distinguishing hold blockers from allocation blockers.
- Releasing hold with precheck and post-release status verification.

Do not use for:

- Explaining allocation cause.
- Executing unrelated order operations.
- Guessing payment/fraud/manual-hold reasons without rule/log evidence.
- Claiming exact rule causality from rule/order candidate matching alone.
- Creating enabled hold rules without user second confirmation.

User-facing output:

- If current status is not `ON_HOLD`, say there is no active hold to release.
- If rule/log evidence is unavailable, say the specific reason is unconfirmed.
- Do not claim hold release is complete unless follow-up status proves it.
- Use `diagnose_hold.py` by default; release success requires `code=0,data=true` and post-check status no longer `ON_HOLD`.
- Use `hold_rules.py` for list/get/active-count/draft/create.
- Use `match_hold_rules_to_orders.py` when the user asks which orders were held by which rule. If no direct hold record/log exists, label the result as candidate or historical candidate.

### allocation

Use for:

- Checking allocation items.
- Checking remaining quantity.
- Checking manual-allocation eligibility.
- Explaining current warehouse allocation result.
- Explaining automatic allocation reason from dispatch explain logs, including routing rules checked, available warehouses, inventory checks, decisive rule/event, and final dispatch.
- Explaining allocation reason when dispatch/allocation/route/log evidence exists.
- Batch allocation explain/items/check/manual-auto allocation using bounded concurrency when OMS has no batch endpoint.

Do not use for:

- Executing any real manual/auto/force/batch allocation write without user second confirmation.
- Inferring allocation reason from final warehouse/status fields alone.
- Replenishment or PO creation.

User-facing output:

- Separate allocation result from allocation reason.
- Prefer `explain_warehouse_assignment.py`; it first queries `/api/linker-oms/opc/public-api/dispatch/dispatch-log/explain?orderNo=...`.
- If remaining is `0`, say manual allocation is not needed or not possible.
- If remaining is `0`, explain the existing warehouse/dispatch/SKU allocation details and say there are no allocatable products; do not submit allocation by default.
- If eligibility API returns a technical error code, translate it into business language.
- For batch requests, return concise per-order status and partial results; do not make the user wait for one slow order to finish before seeing all outcomes.

### operations

Use for:

- Reopen.
- Cancel.
- Batch cancel/reopen.
- Non-allocation high-impact writes only; allocation execution belongs to `allocation`.
- Interpreting async/submitted operation outcomes.
- Confirming downstream cancel state by re-reading sales order and dispatch records.

Do not use for:

- Initial diagnosis of EXCEPTION/ON_HOLD/allocation/replenishment.
- Release hold; use `hold`.
- Manual/auto/force allocation; use `allocation`.
- Any real write/action without user second confirmation.

Confirmation must include:

- Environment.
- Operation.
- Target order(s).
- Business risk.
- Exact confirmation phrase.

User-facing output:

- Distinguish "API accepted/submitted" from "business state completed".
- For cancel, show whether OMS returned success, failed, or ongoing rows.
- For cancel with dispatch records, only call it completed when sales order and dispatch are cancelled.
- If cancel is rejected because the order is already cancelled, say the new request was rejected but the current business state is already cancelled when post-check proves it.

### replenishment

Use for:

- Replenishment recommendation.
- Purchase warehouse recommendation.
- Routing-rule context for replenishment.
- Single-warehouse PO creation.
- Split PO creation.
- Preserving user-specified warehouse names while warning that OMS acceptance should be confirmed.
- Returning PO number, warehouse, SKU/quantity, status, and next step.

Do not use for:

- Explaining why a sales order was allocated to a warehouse.
- ON_HOLD or EXCEPTION diagnosis.
- Cancel/reopen/manual allocation.

User-facing output:

- Recommended warehouse.
- Evidence behind recommendation.
- Alternatives if available.
- Whether warehouse display name needs confirmation.
- Confirmation before PO creation when policy requires it.
- `DISPATCHED` PO means the PO entered warehouse flow; it does not prove inventory has been received.

### order-orchestrator

Use for:

- Default order-related user entry.
- Routing narrow requests to focused agents.
- Multi-step workflows such as query -> exception -> replenishment.
- Merging conclusions into a business-friendly final answer.
- Passing `orderContext.detail` forward so focused agents do not repeat base detail lookups.

Do not use for:

- Direct OMS API calls.
- Direct script execution.
- Direct writes.

Global confirmation policy:

- Read-only actions execute directly.
- Dry-run/draft actions execute directly and must state nothing was submitted.
- Every real write/action requires user second confirmation before execution.

Routing priorities:

1. Status/list/detail: `query`.
2. EXCEPTION cause/solution: `exception`.
3. ON_HOLD/hold rule/release hold: `hold`.
4. Allocation result/reason/remaining: `allocation`.
5. Cancel/reopen/batch/confirmed writes: `operations`.
6. Replenishment/recommended PO warehouse/PO creation: `replenishment`.
