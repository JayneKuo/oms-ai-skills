# Full Real Staging Interface Execution Report

Date: 2026-06-03
Environment: staging loaded from `.env.example`
Credentials: omitted from this report

## Executive Summary

All independent sales-order skill groups were exercised against the real staging OMS APIs, including mutating operations. The test created and cancelled a real sales order, created replenishment purchase orders, verified allocation and hold behavior, and tested business-rule rejection paths.

Primary staging artifacts:

- Sales order: `SO01392094`
- Channel order number: `AI-FULL-20260603104205`
- Final sales order status: `CANCELLED`
- Single replenishment PO: `PO1P80454646`, status `DISPATCHED`
- Split replenishment PO: `PO1P804548520`, status `DISPATCHED`
- Replenishment retest PO: `PO1P80558502`, status `DISPATCHED`
- Replenishment split retest PO: `PO1P805585020`, status `DISPATCHED`
- Query retest sales order: `SO01406203`, status `IMPORTED`

Validation:

- `python -m compileall -q skills`: passed
- `npm.cmd test`: passed, 45 files / 81 tests

Production write policy:

- Read-only actions may run directly.
- Dry-run/draft actions may run directly and must state that nothing was submitted.
- Every real write/action requires user second confirmation before execution.

## Real Execution Matrix

| Skill | Interface | Operation type | Real result | Time |
| --- | --- | --- | --- | --- |
| query | `create_order.py` | write | Created `SO01392094`; order moved from `IMPORTED` to `WAREHOUSE_PROCESSING` | 4351 ms |
| query | `get_order_detail.py` | read | Read `SO01392094`; final status `CANCELLED`, dispatch `Cancelled` | 3782-4421 ms |
| query | `query_orders.py` | read | Order list query succeeded | 5262 ms |
| query | `query_orders.py --keyword SO01405073` | read | Exact order query returned `CANCELLED` and business summary | 7500 ms |
| query | `get_order_detail.py --order SO01392133` | read | Returned `WAREHOUSE_PROCESSING`, dispatch count `1`, `nextSkill=allocation` | 7500 ms |
| query | `query_orders.py --status ON_HOLD --size 3` | read | Returned 3 ON_HOLD rows out of total 34 with status translations | 7500 ms |
| query | `create_order.py` retest | write | Created `SO01406203`, initial status `IMPORTED`, with business summary | 7600 ms |
| exception | `query_orders.py --status EXCEPTION` | read | Exception list query succeeded | 4692 ms |
| exception | `get_order_detail.py` | read | Shared detail endpoint validated through order detail scenarios | 4421 ms |
| hold | `get_hold_reason.py` | read | Non-hold order correctly returned `NOT_APPLICABLE` | 3991-4591 ms |
| hold | `release_hold.py` | write | OMS returned `code=0`, `data=false`; interpreted as no active hold released | 4570 ms |
| hold | `get_allocation_items.py` | read | Allocation items query succeeded | 4609 ms |
| hold | `hold_rules.py --action list/get/active-count` | read | Listed 4 hold rules; inspected enabled imported rule `AI test`; active-count returned `0` | 4400-8100 ms |
| hold | `hold_rules.py --action draft/create` | dry-run/write-gated | Natural language produced a disabled imported permanent hold-rule draft; create without confirmation stayed dry-run and did not submit | 4400 ms |
| hold | `match_hold_rules_to_orders.py` | read/diagnosis | Mapped ON_HOLD orders to historical candidate rules by SKU `CCC`; no active-rule candidates found; exact causality kept unconfirmed without direct logs | 8900 ms |
| allocation | `check_manual_allocation.py` | read/check | OMS rejected current status with `ERROR.THE_STATUS_NOT_SUPPORT_ALLOCATED` | 4508 ms |
| allocation | `get_allocation_items.py` | read | Remaining allocation quantity was `0` after cancellation | 3973 ms |
| allocation | `manual_allocate.py` | write | OMS rejected cancelled order with `ERROR.THE_STATUS_NOT_SUPPORT_ALLOCATED` | 4064 ms |
| allocation | `explain_warehouse_assignment.py --order SO01392133 --compare-warehouse Ontario` | read/diagnosis | Confirmed warehouse `Valley View` and explained the automatic allocation reason from dispatch explain logs: inventory was insufficient in candidate warehouses, so OMS used the highest-priority warehouse rule | 12100 ms |
| operations | `reopen_order.py` | write | OMS rejected non-exception order with `Order not exception` | 4299 ms |
| operations | `cancel_order.py` | write | Cancel request returned `ongoingRespDTOS`; post-check confirmed sales order and dispatch were `Cancelled` | 5733 ms |
| operations | `batch_orders.py --action reopen` | write | Batch reopen correctly reported failed `Order not exception` | 4230 ms |
| operations | `batch_orders.py --action cancel` | write | Batch cancel reports per-order post-check states; already-cancelled orders are rejected by OMS but shown as cancelled when post-check proves it | 9600 ms |
| replenishment | `suggest_purchase_order.py --sku BATESTSKU-1 --quantity 100` | analysis/read | Suggestion succeeded with routing summary and warehouse display-name warning | 5343 ms |
| replenishment | `suggest_purchase_order.py --sku BATESTSKU-1` | boundary | Fast validation failure for missing quantity | 722 ms |
| replenishment | `get_routing_rules.py` | read | Routing rules query succeeded | 4440 ms |
| replenishment | `create_purchase_order.py` | write | Created `PO1P80454646`, status `DISPATCHED` | 4960 ms |
| replenishment | `create_purchase_order_split.py` | write | Created `PO1P804548520`, status `DISPATCHED` | 4252 ms |
| replenishment | `create_purchase_order.py` retest | write | Created `PO1P80558502`, status `DISPATCHED`, with business summary | 11200 ms |
| replenishment | `create_purchase_order_split.py` retest | write | Created `PO1P805585020`, status `DISPATCHED`, with per-warehouse business summary | 11200 ms |
| sales-order legacy | `batch_orders.py` | write smoke | Synced fix confirmed: `release_hold` no longer misreports `data=false` as success | 4596 ms |
| sales-order legacy | `manual_allocate.py` | write smoke | Synced friendly args confirmed; OMS rejected invalid status | 5392 ms |

## Issues Found And Fixed

1. Python skill auth used the wrong IAM base URL source.
   - Fixed all `skills/*/scripts/oms_client.py` files to use `OMS_BASE_URL`.
   - Impact: resolved real staging 401 failures.

2. `batch_orders.py --action release_hold` treated `code=0` as success even when `data=false`.
   - Fixed independent `operations` skill and legacy `sales-order` copy.
   - New behavior: `data=true` is required for release-hold success; otherwise `businessResult=not_released`.

3. Several write scripts were not PowerShell-friendly because they required raw JSON strings.
   - Fixed independent skills:
     - `skills/query/scripts/create_order.py`
     - `skills/allocation/scripts/manual_allocate.py`
     - `skills/replenishment/scripts/create_purchase_order.py`
     - `skills/replenishment/scripts/create_purchase_order_split.py`
   - Synced key fixes into legacy `skills/sales-order/scripts/*`.
   - New behavior: scripts still support JSON, but also accept `--sku`, `--qty`, `--warehouse`, `--quantity`, and address flags.

4. `get_hold_reason.py` could describe a stale hold for orders whose current detail status is not `ON_HOLD`.
   - Fixed to return `NOT_APPLICABLE` immediately for non-hold statuses.

5. Replenishment suggestions could imply a warehouse display name was confirmed when OMS only returned an ID.
   - Fixed agent output to include `targetWarehouseName`, `warehouseDisplayName`, `needsWarehouseNameConfirmation`, `routingRuleSummary`, and `recommendedNextStep`.

6. Exception diagnosis could overstate stale exception-list rows when the detail status had already changed.
   - Fixed to mark `STATUS_CHANGED_FROM_EXCEPTION` and avoid telling users the order is still blocked.

7. Allocation answers could be user-unfriendly when asked "why this warehouse?"
   - Added `skills/allocation/scripts/get_order_detail.py`.
   - Added `skills/allocation/scripts/get_routing_rules.py`.
   - Added `skills/allocation/scripts/explain_warehouse_assignment.py`.
   - Updated `skills/allocation/SKILL.md` and `agent/allocation/AGENT.md` with a warehouse-assignment explanation contract.
   - New behavior: the agent first queries `/api/linker-oms/opc/public-api/dispatch/dispatch-log/explain?orderNo=...` and uses it to explain routing rules checked, available warehouses, inventory checks, decisive rule/event, and final dispatch result. It only falls back to "result confirmed, reason not confirmed" when this evidence is unavailable.

8. Hold could not manage rule-level questions independently.
   - Added `skills/hold/scripts/hold_rules.py` for rule list/get/active-count/draft/create.
   - Added `skills/hold/scripts/match_hold_rules_to_orders.py` for ON_HOLD order to candidate-rule mapping.
   - Rewrote `skills/hold/SKILL.md` to require clear evidence boundaries.
   - New behavior: hold can answer what rules exist, how many orders are actively held by a rule, which orders are candidate matches, and draft hold rules from natural language. Rule creation remains dry-run unless explicitly confirmed.

9. Operations still had ownership ambiguity and weak cancel post-checking.
   - Rewrote `skills/operations/SKILL.md` to remove corrupted text and remove allocation/hold-release ownership.
   - Rewrote `reopen_order.py` with a business summary.
   - Enhanced `cancel_order.py` to post-check sales order and dispatch states after cancel.
   - Rewrote `batch_orders.py` to own batch `cancel` and `reopen` only.
   - New behavior: `ongoingRespDTOS` is reported as downstream/WMS cancellation in progress. Completion is claimed only after sales order and dispatch records are cancelled.

10. Replenishment recommendations and PO creation output needed clearer evidence.
   - Rewrote `suggest_purchase_order.py` to validate quantities, return recommendation evidence, expose alternatives, and distinguish warehouse ID uncertainty from user-specified warehouse names.
   - Rewrote `create_purchase_order.py` with clean help text and business summary.
   - Enhanced `create_purchase_order_split.py` with validation and per-warehouse summaries.
   - Rewrote `skills/replenishment/SKILL.md` to remove corrupted text and clarify that routing rules are replenishment context, not proof of sales-order allocation reasons.

11. Query and orchestrator still had corrupted prompt text and stale routing ownership.
   - Rewrote `skills/query/SKILL.md`, `query_orders.py`, `get_order_detail.py`, `create_order.py`, and query evals.
   - Rewrote `skills/order-orchestrator/SKILL.md` and `agent/order-orchestrator/AGENT.md`.
   - Query now returns business summaries, exact-detail fallback, and next focused skill.
   - Current ownership update: orchestrator routes release hold to `hold`, allocation writes and reopen-for-allocation retry to `allocation`, cancel to `operations`, and PO workflows to `replenishment`.

## Skill Capability Inventory

### query

Can:

- Create sales orders.
- Query sales order lists.
- Fetch sales order details.
- Explain current order status, dispatch status, items, address, allocation quantity, and cancellation state.
- Return business summaries and recommended next focused skill.

Boundary:

- Creation requires a unique channel order number.
- Staging may auto-route the order very quickly after creation, so follow-up actions must re-read order detail before deciding next steps.
- Exact SO-style order searches must use detail fallback before saying not found.

### exception

Can:

- Query exception orders.
- Fetch detail for an exception candidate.
- Detect stale exception-list rows where current detail status has moved on.
- Diagnose EXCEPTION cause from detail fields such as `reserve1`.
- Cross-check allocation item remaining quantity and dispatch explain presence for exception context.
- Run batch EXCEPTION diagnosis with per-order action buckets.
- Recommend whether to replenish, check allocation evidence, reopen after user second confirmation, or simply refresh status.

Boundary:

- Should not rely only on list status. Detail status is the source of truth.
- Does not execute writes.
- Must not recommend reopen when latest detail is no longer EXCEPTION.
- Must not guess inventory/routing causes without detail, allocation, dispatch, or log evidence.
- Real cases `SO01373341` and `SO01373322` confirmed out-of-stock diagnosis from `reserve1`; both had no dispatch, allocated quantity `0`, and remaining quantity `1`.
- Real boundary case `SO01392133` confirmed stale/non-exception handling: latest status was `WAREHOUSE_PROCESSING`, so exception actions should not be recommended.

### hold

Can:

- Check hold reason.
- Release hold.
- Query allocation items for hold-related troubleshooting.
- Diagnose hold with detail status, hold-rule evidence, allocation remaining, optional release, and post-release check.
- Query hold rules, inspect rule detail, and check active hold count by rule.
- Draft hold rules from natural language and create only after user second confirmation.
- Map ON_HOLD orders to active or historical candidate rules from rule config and order fields.

Boundary:

- `code=0,data=false` means no business release occurred. The user-facing response should say no active hold was released, not success.
- Do not submit release when latest detail status is not `ON_HOLD`.
- Do not claim exact hold-rule causality from candidate matching alone.
- Direct active-count proves count by rule, not the full order list.
- Natural-language create without `--confirm-create` is a dry-run.
- Real case `SO01376525` confirmed active `ON_HOLD`; `ORDER_HOLD_OR` rule endpoint returned 404 in staging, so the specific hold rule reason remained unconfirmed; allocation remaining was `1` for SKU `ccc`.
- Real release case `SO01376524` returned `code=0,data=true`; post-check status became `ALLOCATED`, so release was confirmed.
- Real non-hold case `SO01392133` now prechecks and returns `not_submitted` for release, avoiding unnecessary release calls.
- Real rule query found 4 staging rules. Enabled rule `AI test` targets imported orders and had active-count `0`.
- Real candidate matching found `SO01376525` and the first 5 ON_HOLD list orders match historical disabled `CCC` rules, especially `ccc3の2`; exact causality requires direct hold execution logs or hold records.

### allocation

Detailed validation: `docs/allocation-skill-validation-report.md`.

Can:

- Check whether manual allocation is allowed.
- Query remaining allocatable items.
- Fetch order detail for dispatch/allocation evidence.
- Fetch dispatch explain logs for automatic allocation reasons.
- Fetch current routing rule configuration as context.
- Explain warehouse assignment results with evidence boundaries.
- Submit manual allocation.
- Report OMS rule rejection clearly, including unsupported status.
- Block unnecessary allocation submission when precheck proves the order is already fully allocated and no allocatable products remain.
- Run batch allocation explain/items/check/manual allocation through bounded per-order execution when no OMS batch endpoint is available.

Boundary:

- Manual allocation is status-sensitive. Cancelled, warehouse-processing, or fully allocated orders may be rejected by OMS.
- Agent should pre-check remaining quantity and current status before asking the user to force allocation.
- A final warehouse proves the assignment result, not the selection reason. Exact reasons should come first from dispatch explain logs, then routing trace, dispatch log, candidate evaluation, or explicit fields.
- Routing rule configuration is useful context but is not proof that a specific rule selected the warehouse for a specific order.
- Real case `SO01392133` confirms dispatch explain logs can explain automatic allocation: candidate warehouses were Joliet, Valley View, and Fontana; all had zero inventory for `BATESTSKU-1`; the decisive rule routed inventory-short orders to the highest-priority warehouse, resulting in Valley View.
- Real case `SO01392133` also confirms already-allocated handling: remaining quantity was `0`, status was `WAREHOUSE_PROCESSING`, and the agent now reports existing allocation details without submitting another allocation request.
- Allocation execution is owned by `allocation`, not `operations`, to avoid conflicting behavior and repeated cross-agent loops.

### operations

Can:

- Cancel sales orders.
- Reopen exception orders.
- Batch reopen orders.
- Batch cancel orders.
- Confirm asynchronous cancellation by re-reading order detail.
- Confirm dispatch cancellation after cancel.

Boundary:

- Reopen only applies to exception orders.
- Cancel may return accepted/ongoing first; final status needs a follow-up detail query.
- Hold release belongs to `hold`, not operations.
- Operations does not own manual/auto/force allocation. Allocation reads and writes are handled by `allocation` to avoid duplicated responsibilities and loops.
- Real case `SO01405073` confirmed a dispatched/WMS-received order cancel returns `ongoingRespDTOS`; post-check then proved sales order `CANCELLED` and dispatch `Cancelled`.
- Repeating cancel on `SO01405073` returned `ERROR.THE_ORDER_HAS_BEEN_CANCELLED`; post-check correctly reported the current business state as already cancelled.

### replenishment

Can:

- Suggest purchase orders from SKU and quantity.
- Query routing rules.
- Create single replenishment purchase orders.
- Create split replenishment purchase orders.
- Explain warehouse display-name uncertainty when only warehouse IDs are available.
- Preserve user-specified warehouse names while warning that OMS acceptance should be confirmed.
- Return business summaries for single and split PO creation.

Boundary:

- Purchase order creation requires a valid OMS warehouse name.
- Suggestion must ask for quantity if omitted.
- When routing rules return only IDs, user should confirm the target warehouse display name before creation.
- `DISPATCHED` means the PO entered warehouse flow; it does not prove inventory has been received.
- Real retest created `PO1P80558502` and split-path `PO1P805585020`, both `DISPATCHED`.

### order-orchestrator

Can:

- Route user requests to the correct independent skill.
- Keep read-only diagnostics separate from confirmed write operations.
- Ask for confirmation before irreversible user-facing operations.
- Pass shared `orderContext.detail` forward to avoid repeated base lookups.

Boundary:

- Should re-read order detail after any mutating operation before final user response.
- Should not promise a final state from an async response alone.
- Must not use legacy `sales-order` as a hidden dependency for split-agent workflows.

## User-Facing Prompt And Output Recommendations

- Use direct business language: "The cancel request was accepted; I rechecked and the order is now Cancelled."
- For rejected writes, say "OMS rejected this because the current status does not support manual allocation" instead of generic failure.
- Always distinguish API transport success from business success.
- For state-changing operations, include `orderNo`, final status, and next action.
- For every real write/action, require user second confirmation before execution. Confirmation must include environment, action, target object(s), business risk, and exact confirmation phrase.
- For cancel operations with dispatch/WMS records, `ongoingRespDTOS` means downstream Kafka/WMS cancellation is in progress. Only report completion after follow-up detail confirms both sales order and dispatch are `Cancelled`.
- For hold-rule questions, summarize rule status/mode/priority/scope and active-count when requested. For "which orders were held by this rule", use direct hold records/logs when available; otherwise say the result is candidate/historical matching from rule config and order fields.
- For natural-language hold rule creation, first show the generated draft and confirmation requirement. Warn when the draft is `ENABLED`.
- For replenishment, show SKU, quantity, suggested warehouse, and whether the warehouse name needs confirmation.
- For allocation, show the warehouse result plus dispatch explain evidence: routing rules checked, available warehouses, inventory checks, decisive rule/event, final dispatch result, and confidence. If dispatch explain evidence is unavailable, say what log/trace is needed instead of guessing.
- Do not expose environment credentials, tokens, or full raw payloads to end users unless they explicitly ask for technical debugging.

## Release Readiness

Ready with caveats:

- The independent skills now authenticate and execute against staging.
- The main write workflows were tested with real staging mutations.
- Unit tests pass.
- Product policy accepted: every real write/action requires user second confirmation before execution.
- Scope note: legacy `skills/sales-order` is kept for regression compatibility only and is not part of the current optimization scope.
