# OMS Agent/Skill Launch Runbook

Date: 2026-06-05

This runbook defines how the split OMS agents and skills should behave in production-style use. It focuses on three goals:

1. Each focused agent can complete its own domain workflow independently.
2. Agents can be composed by `order-orchestrator` without repeated base lookups or circular handoffs.
3. Users receive consistent, business-friendly answers with clear evidence and safe confirmation gates.

## Global Execution Policy

| Action type | Behavior |
| --- | --- |
| Read-only lookup, diagnosis, explanation, recommendation | Run directly. |
| Dry-run, preview, or draft | Run directly and explicitly say nothing was submitted to OMS. |
| Real write/action | Stop and ask for user second confirmation before execution. |

Real write/action includes test order creation, cancel, reopen, release hold, manual allocation, auto allocation, force allocation, batch allocation, hold rule create/enable/update, PO creation, and split PO creation.

The confirmation prompt must include:

- Environment.
- Operation.
- Target order/rule/SKU/warehouse list.
- Business risk.
- Exact confirmation phrase.

## Default Routing Matrix

| User intent | First agent | Why | Must not do |
| --- | --- | --- | --- |
| "Find this order", "what status is it", "does it exist" | `query` | Fast base lookup and status translation. | Deep root-cause diagnosis or writes. |
| "Why is this order in EXCEPTION", "how do I fix this exception" | `exception` | Owns exception cause, solution, and next action. | Reopen/cancel/create PO directly. |
| "Why is this ON_HOLD", "which hold rule", "show hold rules", "create hold rule" | `hold` | Owns hold evidence, rule lookup, rule-to-order mapping, release assessment, and rule drafts. | Allocation or operations writes. |
| "Where was it allocated", "why this warehouse", "can I allocate", "auto/manual allocate" | `allocation` | Owns allocation result, dispatch explain logs, remaining quantity, and allocation writes. | Cancel/reopen or PO creation. |
| "Cancel this order", "reopen this order", "batch cancel/reopen" | `operations` | Owns high-impact non-allocation order writes and downstream state interpretation. | Hold release, allocation, replenishment. |
| "Do we need replenishment", "which purchase warehouse", "create PO/split PO" | `replenishment` | Owns replenishment recommendation and PO creation. | Explain sales-order allocation reason. |
| Multi-step order request | `order-orchestrator` | Routes in business-process order and passes shared context. | Direct OMS API calls. |

## Business-Flow Order

When the user gives a broad or multi-step request, follow this order:

1. `query`: establish current order status and reusable `orderContext`.
2. `hold`: if status is `ON_HOLD` or the user asks about hold/rules.
3. `exception`: if status is `EXCEPTION` or the user asks about exception cause.
4. `allocation`: if warehouse, dispatch, remaining quantity, or allocation eligibility is involved.
5. `replenishment`: if shortage/SKU quantity/PO is involved.
6. `operations`: only for confirmed cancel/reopen workflow.

Do not move to a write agent until the read/diagnosis agent has explained the current state and the user has provided second confirmation for the write.

## Shared Context Contract

In orchestrated mode, the first agent that fetches order detail must pass this context forward:

```json
{
  "orderContext": {
    "orderNo": "SO...",
    "fetchedAt": "2026-06-05T00:00:00Z",
    "sourceAgent": "query",
    "detail": {},
    "businessSummary": {}
  }
}
```

Later agents must reuse `orderContext.detail` unless:

- Required fields are missing.
- The user asks for latest status after a delay.
- A write just occurred and post-write verification is required.
- A domain-specific endpoint is needed, such as dispatch explain logs, hold rules, allocation items, routing rules, or PO recommendation evidence.

Forbidden loop:

```text
query -> focused agent get_order_detail -> operations get_order_detail
```

This loop is forbidden when the original detail is still fresh and no write has occurred.

## Standard Output Template

Every focused agent should answer in this shape:

```text
Result: [business result in one sentence]
Evidence: [confirmed facts and sources; no raw JSON by default]
Explanation: [why this happened, or what is still unconfirmed]
Actionability: [what can/cannot be done now]
Next step: [no action / focused handoff / second confirmation request]
```

For batch requests:

```text
Result: [overall count by success/blocked/needs-confirmation/error]
Per-order summary:
- [orderNo]: [status/result] | [evidence] | [next step]
Boundary: [timeouts, partial evidence, or skipped writes]
Next step: [confirmation phrase or follow-up check]
```

For real write requests before execution:

```text
This is a real OMS action, so I will not execute it yet.
Environment: [staging/production]
Operation: [cancel/reopen/release hold/allocation/create PO/etc.]
Targets: [orders/rules/SKUs/warehouses]
Risk: [business impact and downstream impact]
To proceed, reply exactly: [confirmation phrase]
```

After a real write:

```text
Submission result: [accepted/rejected/ongoing/not submitted]
Post-check result: [current OMS state and downstream/dispatch state if relevant]
Confirmed: [what is proven]
Not confirmed yet: [what still needs WMS/inbound/log evidence]
Next step: [monitor/retry/handoff/no action]
```

## Agent-Specific Output Requirements

| Agent | Must include | Evidence boundary |
| --- | --- | --- |
| `query` | Order status, plain-language meaning, confirmed identifiers, next focused agent. | Do not diagnose root cause from status alone. |
| `exception` | Cause, affected SKU/quantity when known, recommended resolution, reopen timing. | Do not invent shortage/routing causes without detail/log evidence. |
| `hold` | Current hold state, direct rule/log proof or candidate rule boundary, release/create-rule next step. | Candidate matching is not direct causality. |
| `allocation` | Assigned warehouse, dispatch number/status, SKU quantities, remaining quantity, dispatch explain reason when available. | Final warehouse proves result, not reason. |
| `operations` | Pre-check risk, second confirmation request, submission result, post-check state, downstream/WMS boundary. | API acceptance is not business completion. |
| `replenishment` | Recommended warehouse, SKU/quantity, reason, alternatives, PO status after creation. | PO `DISPATCHED` does not mean inventory is received. |
| `order-orchestrator` | Merged result, which agent handled each part, reused context, next step. | It must not claim evidence that focused agents did not provide. |

## Regression Prompts

Use these prompts for launch regression:

| Prompt | Expected agent | Expected behavior |
| --- | --- | --- |
| "查一下 SO01392133 当前是什么状态" | `query` | Return exact detail and status meaning. |
| "SO01392133 为什么分到 Valley View" | `allocation` | Use dispatch explain logs before any fallback. |
| "这个已分仓订单重新分仓" | `allocation` | Explain remaining quantity and existing allocation; do not submit if remaining is zero. |
| "查一下有哪些 hold 规则" | `hold` | Return rule names, status, hold mode, priority, scope. |
| "这些 ON_HOLD 订单分别被什么规则卡住" | `hold` | Return direct proof if available; otherwise candidate/historical boundary. |
| "创建一个 imported order 的 hold 规则" | `hold` | Draft first; real create requires second confirmation. |
| "取消一个 warehouse processing 的订单" | `operations` | Pre-check dispatch/WMS risk; require second confirmation; post-check dispatch. |
| "这个 EXCEPTION 订单怎么处理" | `exception` | Explain cause, solution, next step; route shortage to replenishment. |
| "给这个 SKU 补货到哪个仓" | `replenishment` | Recommend warehouse with evidence and alternatives. |
| "创建 split PO" | `replenishment` | Preview target warehouses/SKUs; require second confirmation. |

## Launch Readiness Checklist

- [ ] Every focused agent has base query or equivalent current-state evidence.
- [ ] Every real write path has second-confirmation copy.
- [ ] Allocation explanations use dispatch explain/log evidence when available.
- [ ] Hold rule causality does not overstate candidate matching.
- [ ] Operations does not own allocation or hold release.
- [ ] Replenishment does not claim PO dispatch equals received inventory.
- [ ] Batch workflows return per-order outcomes and do not block on one slow order.
- [ ] `order-orchestrator` passes shared context and avoids repeated detail loops.
