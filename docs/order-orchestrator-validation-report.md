# Order Orchestrator Validation Report

Validation date: 2026-06-04

Scope: `skills/order-orchestrator` and `agent/order-orchestrator`.

## Matrix Validation

| User intent | Route | Context rule |
| --- | --- | --- |
| "查一下 SO01405073 状态" | `query` | Query returns status only. No downstream skill needed. |
| "SO01392133 为什么分到 Valley View" | `query -> allocation` | Query fetches detail once; allocation fetches dispatch explain logs and allocation items only. |
| "SO01376525 为什么 ON_HOLD / 哪条规则" | `query -> hold` or direct `hold` | Hold owns hold evidence, rule lookup, candidate rule mapping, and release hold. |
| "取消 SO01405073" | `operations` | Operations owns cancel; it post-checks sales order and dispatch state after write. |
| "释放 hold 后看看还有没有商品能分仓" | `hold -> allocation` | Hold releases/checks hold; allocation checks remaining/allocation. Operations is not involved. |
| "异常缺货就补货" | `query -> exception -> replenishment` | Exception diagnoses shortage; replenishment uses SKU/quantity context to recommend/create PO. |
| "手动分仓/自动分仓/批量分仓" | `allocation` | Allocation owns all allocation writes and batch allocation. |
| "创建 hold 规则" | `hold` | Hold drafts rule first; real create requires user second confirmation. |
| "创建 PO" | `replenishment` | Replenishment owns single/split PO creation. |

## Fixes Applied

- Rewrote `skills/order-orchestrator/SKILL.md` to remove corrupted text.
- Rewrote `agent/order-orchestrator/AGENT.md` to remove corrupted text.
- Corrected routing ownership:
  - release hold -> `hold`,
  - manual/auto/force/batch allocation -> `allocation`,
  - cancel/batch cancel -> `operations`,
  - reopen-for-allocation retry -> `allocation`,
  - PO/replenishment -> `replenishment`.
- Clarified shared `orderContext` reuse and allowed re-query cases.
- Added explicit rule: never use legacy `sales-order` as a hidden dependency for split-agent workflows.

## No-Loop Contract

The orchestrator should avoid:

- `query -> allocation get_order_detail` when query already has fresh detail.
- `query -> hold -> operations release_hold`; release hold belongs to hold.
- `query -> operations -> allocation manual_allocate`; allocation writes belong to allocation.
- Rechecking detail repeatedly before a write. Re-query is required after the write, not before every focused step.

## User-Facing Example

```text
我会先用 query 确认订单当前状态，然后把同一份订单详情传给 allocation。allocation 只补查分仓日志和 allocation items，不会再重复查基础详情。最终回复会合并当前状态、分仓结果、分仓原因和下一步。
```
