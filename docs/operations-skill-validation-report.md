# Operations Skill Validation Report

Validation date: 2026-06-04

Scope: `skills/operations` only.

## Real Staging Cases

| Order | Scenario | Result |
| --- | --- | --- |
| `SO01405073` | Created test order, then cancelled after dispatch/WMS handoff | Order moved to `WAREHOUSE_PROCESSING`, dispatch `SO01405073-1`, WMS/dispatch status `Warehouse Received`; cancel returned `ongoingRespDTOS`; post-check confirmed sales order `CANCELLED` and dispatch `Cancelled`. |
| `SO01405073` | Repeat cancel boundary | OMS returned failed row `ERROR.THE_ORDER_HAS_BEEN_CANCELLED`; post-check confirmed the current business state is already cancelled. |
| `SO01392133` | Reopen non-exception boundary | OMS rejected with `Order not exception`; script reports `businessSummary.state=rejected`. |
| `SO00000000` | Batch reopen missing order boundary | OMS rejected with `not found this order`; batch result kept per-order failure. |
| `SO01405073`, `SO00000000` | Batch cancel mixed boundary | Cancel API returned a failed row for already-cancelled `SO01405073`; post-check marked `SO01405073` cancelled and `SO00000000` not confirmed. |

## Fixes Applied

- Rewrote `skills/operations/scripts/reopen_order.py` to remove corrupted prompt text and add a business summary.
- Enhanced `skills/operations/scripts/cancel_order.py` to:
  - summarize success/fail/ongoing rows,
  - post-check sales order detail,
  - summarize dispatch cancel status,
  - treat `ongoingRespDTOS` as downstream processing, not completion,
  - report already-cancelled orders as rejected submission but cancelled current state when post-check proves it.
- Rewrote `skills/operations/scripts/batch_orders.py` so operations owns batch `cancel` and `reopen` only.
- Removed release-hold ownership from operations documentation; hold release belongs to `hold`.
- Rewrote `skills/operations/SKILL.md` to remove乱码 and remove allocation/hold conflicts.

## Ability Boundary

Operations can independently complete:

- Pre-confirmed cancel for one or more sales orders.
- Pre-confirmed reopen for one or more sales orders.
- Interpret cancel `successRespDTOS`, `failRespDTOS`, and `ongoingRespDTOS`.
- Re-check sales order and dispatch state after cancel.
- Explain OMS rejection in business language.
- Batch cancel/reopen with per-order outcomes.

Operations must not:

- Release hold. Use `hold`.
- Manually allocate, auto allocate, force allocate, or explain allocation. Use `allocation`.
- Diagnose EXCEPTION root cause from scratch. Use `exception` first.
- Claim async cancel is complete before sales order and dispatch states prove it.

## User-Facing Example

```text
取消请求已经提交到 staging。OMS 返回 ongoing，说明下游 WMS/dispatch 取消还在处理，不能只凭接口返回说完成。我复查后看到销售单 SO01405073 已经是 Cancelled，dispatch SO01405073-1 也是 Cancelled，所以这次取消现在可以确认完成。
```
