# Query Skill Validation Report

Validation date: 2026-06-04

Scope: `skills/query` only.

## Real Staging Cases

| Scenario | Result |
| --- | --- |
| Exact order query | `query_orders.py --keyword SO01405073` returned cancelled order `SO01405073` with `businessSummary.status=CANCELLED`. |
| Detail lookup with handoff | `get_order_detail.py --order SO01392133` returned status `WAREHOUSE_PROCESSING`, dispatch count `1`, and `nextSkill=allocation`. |
| ON_HOLD list | `query_orders.py --status ON_HOLD --size 3` returned 3 rows out of total 34 and translated the status as held/blocked. |
| Test order creation | `create_order.py` created `SO01406203`, initial status `IMPORTED`, channel order `AI-QUERY-20260604170337`. |

## Fixes Applied

- Rewrote `query_orders.py` to remove corrupted help text and add `businessSummary`.
- Rewrote `get_order_detail.py` to add status translations, dispatch count, and recommended next focused skill.
- Rewrote `create_order.py` to remove corrupted text, validate positive quantities, and add creation summary.
- Rewrote `skills/query/SKILL.md` and `skills/query/evals/evals.json` with clear ownership and handoff rules.

## Ability Boundary

Query can independently complete:

- List sales orders by status.
- Find orders by keyword.
- Use exact detail fallback for SO-style order numbers when page search returns no rows.
- Fetch single order detail.
- Translate basic status into business language.
- Create explicit test sales orders.
- Recommend the next focused skill without diagnosing the cause itself.

Query must not:

- Explain hold rules.
- Diagnose EXCEPTION root cause.
- Explain allocation reason.
- Cancel/reopen/release hold/manual allocate.
- Recommend or create replenishment PO unless routed to `replenishment`.

## User-Facing Example

```text
订单 SO01392133 当前是 Warehouse Processing，说明已经进入仓库处理/履约流程。它有 1 个 dispatch。这个结果只确认当前阶段；如果你想知道为什么分到这个仓，需要交给 allocation 查询 dispatch explain 和分仓证据。
```
