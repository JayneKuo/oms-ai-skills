# Replenishment Skill Validation Report

Validation date: 2026-06-04

Scope: `skills/replenishment` only.

## Real Staging Cases

| Scenario | Result |
| --- | --- |
| Suggest PO for `BATESTSKU-1`, qty `100` | Recommendation returned one visible warehouse ID `2005833934970490882`; display name was not returned, so user must confirm warehouse name before creation. Routing context loaded 1 page. Active rules included `MINIMAL_SPLIT`, `CONFIG_AUTO_CREATE_PRODUCT_IF_NOT_EXISTS`, `CONFIG_AUTO_CREATE_PO_PRODUCT`, and `ONE_WAREHOUSE_BACKUP`. |
| Missing quantity boundary | `suggest_purchase_order.py --sku BATESTSKU-1` failed fast with a clear validation error requiring `--quantity`. |
| User-specified warehouse | `suggest_purchase_order.py --sku BATESTSKU-1 --quantity 5 --warehouse "Valley View"` preserved the user warehouse and warned to confirm OMS accepts that warehouse name. |
| Single PO creation | `create_purchase_order.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 1` created `PO1P80558502`, status `DISPATCHED`. |
| Split PO creation path | `create_purchase_order_split.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 1` created `PO1P805585020`, status `DISPATCHED`. |

## Fixes Applied

- Rewrote `suggest_purchase_order.py` to:
  - validate positive quantities,
  - return evidence lines for the recommendation,
  - expose alternatives,
  - distinguish OMS-returned warehouse IDs from user-specified warehouse names,
  - state that routing rules are replenishment context only.
- Rewrote `create_purchase_order.py` to remove corrupted prompt text and add `businessSummary`.
- Enhanced `create_purchase_order_split.py` with input validation and per-warehouse business summaries.
- Rewrote `skills/replenishment/SKILL.md` to remove corrupted text and clarify boundaries.

## Ability Boundary

Replenishment can independently complete:

- Suggest replenishment by SKU/quantity.
- Explain why a purchase warehouse is recommended from available warehouse and routing context evidence.
- Preserve a user-specified target warehouse while warning that OMS acceptance should be confirmed.
- Create single-warehouse purchase orders.
- Create split purchase orders, one PO per warehouse entry.
- Return PO number, warehouse, SKU/quantity, status, and next step.

Replenishment must not:

- Explain why a sales order was allocated to a warehouse; use `allocation`.
- Diagnose ON_HOLD/EXCEPTION root cause from scratch.
- Hide warehouse display-name uncertainty.
- Claim `DISPATCHED` PO status means inventory has already been received.

## User-Facing Example

```text
建议补货到仓库 ID 2005833934970490882。原因是当前 inventory/list 只返回了这一个可见仓，routing context 中 `ONE_WAREHOUSE_BACKUP` 处于启用状态，因此单仓补货方案是兼容的。但接口没有返回可读仓名，所以创建 PO 前需要确认这个 ID 对应的仓库名称。
```
