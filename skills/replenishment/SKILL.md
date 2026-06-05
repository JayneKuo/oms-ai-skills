---
name: replenishment
description: Handle OMS sales-order-related replenishment recommendations and purchase order creation. Use when the user asks whether inventory should be replenished, which purchase warehouse to use, why a purchase warehouse is recommended, or asks to create single/split purchase orders.
---

# Replenishment Skill

## Runtime Guardrails

- Use this skill for replenishment recommendation, purchase warehouse recommendation, single-warehouse PO creation, and split PO creation.
- Read-only replenishment recommendations may run directly. Every real PO creation or split PO creation must require user second confirmation before execution.
- Recommendation reasons must come from real evidence such as available warehouses, routing context, WMS/fulfillment availability, ranking/priority, or user constraints.
- Always tell the user the recommended warehouse, why it is recommended, whether there are alternatives, and whether warehouse-name confirmation is needed.
- Do not explain why a sales order was allocated to a warehouse; route that to `allocation`.
- Do not diagnose ON_HOLD or EXCEPTION root cause; use `hold` or `exception` first, then return here for replenishment once SKU/quantity need is clear.
- Do not create a purchase order until the user has explicitly confirmed warehouse and SKU quantities in a second confirmation turn, even if the original request contains all required details.
- If OMS only returns a warehouse ID and not a display name, say the warehouse display name must be confirmed before PO creation.
- If the user specifies a warehouse name, preserve it but still confirm it is accepted by OMS.

## User Reply Shape

1. Result: recommended replenishment plan or PO creation result.
2. Reason: evidence behind the recommended warehouse or split.
3. Alternatives: other available warehouses if known.
4. Next step: confirmation, PO monitoring, or retry allocation after inventory arrives.

For PO write requests before execution, reply first:

```text
This is a real OMS purchase-order action, so I will not execute it yet.
Environment: [staging/production]
Operation: [create PO / create split PO]
Targets: [warehouse list, SKU quantities]
Risk: [real purchase orders will be created and may enter warehouse/inbound workflows]
To proceed, reply exactly: [confirmation phrase]
```

## Script Inventory

```bash
python scripts/get_order_detail.py --order SO00361770
python scripts/suggest_purchase_order.py --sku BATESTSKU-1 --quantity 10
python scripts/suggest_purchase_order.py --skus '[{"sku":"BATESTSKU-1","quantity":10}]'
python scripts/suggest_purchase_order.py --sku BATESTSKU-1 --quantity 10 --warehouse "Valley View"
python scripts/create_purchase_order.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 10
python scripts/create_purchase_order_split.py --orders '[{"warehouse":"Valley View","skus":[{"sku":"BATESTSKU-1","quantity":5}]}]'
python scripts/create_purchase_order_split.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 5
python scripts/get_routing_rules.py
```

## Recommendation Rules

- `suggest_purchase_order.py` must validate positive SKU quantities.
- Use inventory/list to find visible warehouses.
- Use routing/v2/rules as replenishment context only. It does not prove sales-order allocation reasons.
- If only one warehouse is visible, it can be recommended as the only visible option, with medium confidence.
- If no warehouse is visible, ask the user to provide one.
- If `ONE_WAREHOUSE_BACKUP` is enabled, a single-warehouse replenishment plan is compatible with current routing context.
- If the user asks for split replenishment, preserve the requested split and explain the per-warehouse PO outputs.

## Creation Rules

- `create_purchase_order.py` creates one PO for one warehouse.
- `create_purchase_order_split.py` creates one PO per warehouse entry.
- Creation output must include PO number, warehouse, SKU/quantity, status, and next step.
- `DISPATCHED` means the PO entered the warehouse flow; do not claim received inventory until receiving/inbound evidence confirms it.

## Forbidden

- Do not claim a purchase warehouse recommendation is the reason a sales order was allocated to that warehouse.
- Do not hide warehouse-name uncertainty.
- Do not create a PO with missing or non-positive quantities.
- Do not expose credentials or raw payloads by default.
