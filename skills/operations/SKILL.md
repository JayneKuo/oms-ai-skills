---
name: operations
description: Execute high-impact non-allocation OMS sales-order operations, mainly cancel, after user second confirmation. Use when the user asks to cancel one or more orders or asks for batch cancel. Distinguish API acceptance, downstream ongoing processing, rejection, and final business state.
---

# Operations Skill

## Runtime Guardrails

- Use this skill for high-impact non-allocation writes: cancel and batch cancel.
- Read-only pre-checks may run directly. Every real cancel/batch cancel write must require user second confirmation before execution.
- Always require user second confirmation before writes. The confirmation prompt must include environment, operation, target order(s), business risk, and the exact confirmation phrase.
- Do not diagnose ON_HOLD, EXCEPTION, allocation reason, or replenishment from scratch. Ask the relevant focused skill to provide diagnosis first.
- Do not execute manual allocation, auto allocation, force allocation, reopen-for-allocation retry, dispatch release/retry, allocation precheck, allocation explanation, or general dispatch/fulfillment diagnosis. All allocation/dispatch/fulfillment reads and writes are owned by `allocation`, except cancel-specific dispatch post-checks.
- Do not release hold here. Hold release belongs to `hold`, because it requires hold-rule evidence, latest ON_HOLD status, and post-release hold checks.
- After execution, distinguish API acceptance from completed business outcome. Never call a submitted/ongoing request "fully successful" until a follow-up status check proves it.
- Cancel with dispatch/WMS records may return `ongoingRespDTOS`. Treat this as downstream Kafka/WMS cancellation in progress, not final success.
- For cancel, re-check order detail and dispatch status. Only say cancellation completed after the sales order is `CANCELLED` and every dispatch is cancelled, or no dispatch exists.
- If OMS rejects cancel because the order is already cancelled, use post-check to tell the user the new submission was rejected but the current business state is already cancelled.
- Keep user-facing language operational and concise. Avoid raw JSON unless requested.

## User Reply Shape

Before execution:

1. Risk notice.
2. Environment, operation, target order(s), and risk.
3. Exact confirmation phrase.

After execution:

1. Submitted, rejected, ongoing, or completed result.
2. What is confirmed and what is not yet confirmed.
3. Downstream/WMS state when dispatch records exist.
4. Next status check or escalation advice.

## Script Inventory

```bash
python scripts/get_order_detail.py --order SO00361770
python scripts/cancel_order.py --orders SO00361770 --confirm-cancel
python scripts/cancel_order.py --orders SO001 SO002 --post-check-delay 3 --confirm-cancel
python scripts/batch_orders.py --action cancel --orders SO001 SO002 --confirm-execute
```

## Confirmation Template

```text
This is a real OMS action, so I will not execute it yet.
Environment: [staging/production]
Operation: [cancel]
Targets: [order list]
Risk: [the order may stop fulfillment or trigger downstream WMS/dispatch cancellation]
To proceed, reply exactly: [confirmation phrase]
```

## Cancel Result Rules

- `successRespDTOS`: OMS reports row-level cancel success. Still re-check detail when dispatch exists.
- `ongoingRespDTOS`: cancel has entered downstream processing. Do not say completed until post-check proves it.
- `failRespDTOS`: submission failed for those rows. If post-check shows the order is already cancelled, say the new request was rejected because there is nothing left to cancel.
- Sales order `CANCELLED` plus cancelled dispatch records means cancellation is confirmed.
- Sales order `CANCELLED` but dispatch still active means sales order cancellation is visible, but downstream cancellation is not fully confirmed.

## Forbidden

- Do not perform allocation under operations.
- Do not perform reopen-for-allocation retry under operations; route it to allocation.
- Do not answer general dispatch/DN/WMS/fulfillment progress questions under operations; route them to allocation.
- Do not release hold under operations.
- Do not call accepted/ongoing cancel "successful" before post-check.
- Do not expose credentials or full raw payloads by default.
