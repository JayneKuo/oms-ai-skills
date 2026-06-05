# Allocation Skill Validation Report

Validation date: 2026-06-03

Scope: `skills/allocation` only. Legacy `skills/sales-order` is excluded from optimization per product direction.

## Real Staging Case

- Test order: `SO01392133`
- Channel order: `AI-FLOW-20260603115233`
- SKU: `BATESTSKU-1`, qty `2 EA`
- Current sales order status: `WAREHOUSE_PROCESSING`
- Dispatch: `SO01392133-1`
- WMS/downstream order: `DN-3658390`
- Assigned warehouse: `Valley View`, accounting code `889`
- Dispatch status: `Warehouse Received`

## Scripts Verified

| Script | Scenario | Result |
| --- | --- | --- |
| `get_order_detail.py` | Basic standalone order lookup | Passed; returned order, item, dispatch, WMS status, and assigned warehouse. |
| `get_allocation_items.py` | Remaining quantity lookup | Passed; returned total qty `2`, allocated `2`, remaining `0`. |
| `check_manual_allocation.py` | Manual allocation eligibility | Passed; OMS rejected with `ERROR.THE_STATUS_NOT_SUPPORT_ALLOCATED`, which is correct for this warehouse-processing order. |
| `manual_allocate.py` | Already allocated `HAND_SKU_AUTO_DISPATCH` boundary | Passed after fix; precheck returned `PRECHECK_BLOCKED`, `_request.submittedToOms=false`, existing allocation details, and no allocatable products. |
| `batch_allocation.py` | Batch allocation explain/items/check/manual allocation | Passed; `items` returned one ok and one failed order in one batch, `manual_allocate` blocked already allocated order without OMS submission, and `explain` returned per-order summaries. |
| `explain_warehouse_assignment.py` | Automatic allocation explanation | Passed; used dispatch explain logs and returned confirmed reason. |
| `explain_warehouse_assignment.py --compare-warehouse Ontario` | "Why not another warehouse?" boundary | Passed; explained Ontario was not in the available candidate list. |
| `explain_warehouse_assignment.py --order SO00000000` | Missing order boundary | Passed after fix; now reports order not found/inaccessible instead of implying no allocation. |
| `get_routing_rules.py` | Routing rule context | Passed; returned default rule configuration as context only. |

## Confirmed Allocation Reason

The dispatch explain endpoint was verified:

```text
GET /api/linker-oms/opc/public-api/dispatch/dispatch-log/explain?orderNo=SO01392133
```

Confirmed evidence:

- Rules checked: `Allow Split Fulfillment`, `Auto create product`, `Auto create product for PO`, `lf the inventory is insufficient, it will be directed to the highest priority warehouse`.
- Candidate warehouses: `Joliet-890`, `Valley View-889`, `Fontana-931`.
- Inventory checks: `BATESTSKU-1` had `0 EA` in Joliet, Valley View, and Fontana.
- Decisive event: inventory insufficient, route to highest-priority warehouse.
- Final dispatch: `SO01392133-1` to `Valley View`.

User-facing explanation should be:

```text
订单 SO01392133 当前分到 Valley View。分仓解释日志确认这是系统自动分仓：
本次候选仓是 Joliet-890、Valley View-889、Fontana-931；SKU BATESTSKU-1 在这些候选仓库存均为 0 EA。
因此命中“库存不足时转到最高优先级仓库”的规则，最终生成 dispatch SO01392133-1 到 Valley View。
Ontario 没有进入本次可用仓候选列表，所以不能作为本次自动分仓的备选原因。
当前 remaining=0，订单已进入 Warehouse Processing，OMS 不支持再手动分仓。
```

## Fixes Applied

- `explain_warehouse_assignment.py` now fetches dispatch explain logs first and treats them as highest-priority reason evidence.
- Automatic dispatch is displayed as "系统自动分仓" instead of a raw/unknown enum when explain logs exist.
- Candidate warehouse explanation now distinguishes "not selected" from "not in candidate list".
- Missing/nonexistent orders now return an explicit not-found/inaccessible summary.
- `manual_allocate.py` now re-reads order state after any accepted allocation write through `postAllocationCheck`.
- Rejected manual allocation now returns `businessSummary.state = rejected` so the agent will not claim allocation success.
- Already allocated orders now block before submitting manual/auto allocation. The response explains current warehouse, dispatch, SKU quantities, `remaining=0`, and that no allocatable products remain.
- Batch allocation workflows now live in allocation, not operations, with `batch_allocation.py` for explain/items/check/manual allocation.
- `SKILL.md` now requires post-write re-read and dispatch explain evidence in user-facing replies.

## Ability Boundary

Allocation can independently complete:

- Order detail lookup needed for allocation context.
- Remaining quantity check.
- Manual-allocation eligibility check.
- Auto allocation reason explanation from dispatch explain logs.
- Candidate warehouse explanation when candidate evidence exists.
- Manual allocation submission after user second confirmation, with post-write re-read if OMS accepts.
- Already allocated / no-remaining-product handling without submitting a needless write.
- Batch explain/items/check/manual allocation with bounded concurrency, partial results, and per-order summaries.

Allocation must not:

- Guess "closest warehouse", "enough inventory", "ZIP rule", or "priority" from final warehouse alone.
- Tell the user manual allocation succeeded when OMS returns a nonzero business code.
- Recommend manual allocation when `remaining=0` or current status is not supported.
- Execute allocation by default when the precheck already proves the order is fully allocated or has no allocatable products.
- Loop back to query agent for base detail in orchestrated mode if `orderContext.detail` is already supplied.

## Remaining Launch Risk

The successful manual allocation path was not proven on this case because the order is already fully allocated and in `WAREHOUSE_PROCESSING`. The rejection path is correct and important for launch. To fully prove a successful manual allocation, use an eligible unallocated/imported order fixture and run:

```bash
python skills/allocation/scripts/manual_allocate.py --order <ORDER_NO> --dispatch-type HAND_WHOLE_AUTO_DISPATCH
```

Expected success behavior: OMS returns `code=0`, script includes `postAllocationCheck`, and the agent reports actual post-allocation warehouse, dispatch number/status, SKU quantities, remaining quantity, and confirmed reason if logs exist.
