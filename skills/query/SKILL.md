---
name: query
description: Lightweight OMS sales-order lookup: list search, exact order detail, basic status explanation, and explicit test-order creation. Use when the user only needs to find an order, check status, confirm existence, or create a test order. Do not perform deep diagnosis or order operations.
---

# Query Skill

## Runtime Guardrails

- Use this skill only for lightweight sales-order lookup, detail lookup, basic status explanation, and explicitly requested test-order creation.
- Read-only query actions may run directly. Test-order creation is a real write/action and must require user second confirmation before execution.
- Do not diagnose EXCEPTION root causes, ON_HOLD rules, warehouse assignment reasons, replenishment needs, or write operations beyond test-order creation.
- If deeper analysis is needed, route to the focused skill: `exception`, `hold`, `allocation`, `operations`, or `replenishment`.
- Exact order-number lookup must use detail fallback if page search returns no rows.
- Final replies must be business-friendly: summarize the result, translate status into plain language, say what is confirmed, and give the next step.
- Do not paste raw JSON or unexplained fields unless the user explicitly asks for technical detail.

## Script Inventory

```bash
python scripts/query_orders.py --status EXCEPTION --size 20
python scripts/query_orders.py --keyword SO00361770
python scripts/get_order_detail.py --order SO00361770
python scripts/create_order.py --channel-order-no AI-ORDER-123 --sku BATESTSKU-1 --qty 1 --ship-name "Test User" --address1 "123 Main St" --city "Los Angeles" --state CA --zip-code 90001 --confirm-create
```

## Status Translation

- `IMPORTED`: order is imported and waiting for processing.
- `ALLOCATED`: order has allocation information and may need allocation evidence for details.
- `WAREHOUSE_PROCESSING`: order is in warehouse processing/fulfillment.
- `DISPATCHED`: order has been dispatched to warehouse flow.
- `EXCEPTION`: order needs exception diagnosis.
- `ON_HOLD`: order is blocked by hold and needs hold diagnosis.
- `CANCELLED`: order is cancelled.
- `SHIPPED`: order is shipped.

## Output Shape

```text
Result: [order/list found or not found]
Meaning: [plain-language status meaning]
Confirmed facts: [orderNo, status, channel order no, dispatch count if visible]
Next step: [no action, or route to focused skill]
```

For test-order creation requests, do not submit immediately. Reply first:

```text
This is a real OMS action, so I will not create the test order yet.
Environment: [staging/production]
Operation: create test sales order
Targets: [channel order no, SKU, quantity, ship-to summary]
Risk: [a real order will be created in OMS and may enter allocation/warehouse workflows]
To proceed, reply exactly: [confirmation phrase]
```

## Handoff Rules

- `ON_HOLD` -> `hold`.
- `EXCEPTION` -> `exception`.
- Warehouse result/reason/remaining -> `allocation`.
- Reopen/retry allocation -> `allocation`.
- Cancel -> `operations`.
- Replenishment/PO -> `replenishment`.

## Orchestrator Context

When used by `order-orchestrator`, return/pass:

```json
{
  "orderContext": {
    "sourceAgent": "query",
    "detail": {},
    "businessSummary": {}
  }
}
```

Downstream agents should reuse this context and fetch only domain-specific evidence.
