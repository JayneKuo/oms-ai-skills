---
name: order-orchestrator
description: Coordinate split OMS order skills. Use as the default order entry point to route requests to query, exception, hold, allocation, operations, or replenishment, while reusing shared order context and avoiding duplicate base lookups.
---

# Order Orchestrator Skill

## Runtime Guardrails

- Use this skill as the default entry point for OMS order requests after the large `sales-order` skill was split into focused skills.
- Production confirmation policy: read-only actions may run directly; dry-run/draft actions may run directly; every real write/action must require user second confirmation before execution.
- Route narrow requests to exactly one focused skill whenever possible.
- For multi-step requests, call focused skills in business-process order and merge only their conclusions.
- Do not call OMS APIs directly from this skill. Evidence and execution belong to `query`, `exception`, `hold`, `allocation`, `operations`, or `replenishment`.
- Prefer the smallest capable skill to reduce latency and tool calls.
- Never use legacy `sales-order` as a hidden dependency for split-agent workflows.
- Never guess causes when a focused skill lacks evidence. Say what is confirmed, what remains unconfirmed, and what should be checked next.
- In multi-skill workflows, pass shared `orderContext` forward. Do not make each skill repeat the same order-detail query unless fields are missing, context is stale, or a write operation just happened.

## Routing Priorities

1. Status/list/detail only: `query`.
2. EXCEPTION cause or solution: `exception`.
3. ON_HOLD, hold rule, hold rule management, release hold: `hold`.
4. Warehouse allocation result/reason, dispatch/DN/WMS/fulfillment state, warehouse processing progress, remaining quantity, reopen-for-allocation retry, manual/auto/force allocation, batch allocation: `allocation`.
5. Cancel and batch cancel: `operations`.
6. Replenishment, recommended purchase warehouse, PO creation: `replenishment`.

## Ownership Boundaries

- `query` owns base lookup and test-order creation only.
- `exception` owns exception cause/solution diagnosis only.
- `hold` owns hold evidence, hold rule query/create draft, rule-to-order candidate mapping, and release hold.
- `allocation` owns allocation evidence, allocation explanation, dispatch/fulfillment/WMS state, DN lookup, remaining quantity, reopen-for-allocation retry, dispatch release/retry, and allocation writes.
- `operations` owns cancel only; it does not own reopen, hold release, allocation, dispatch release/retry, or general fulfillment diagnosis.
- `replenishment` owns replenishment recommendation and PO creation; it does not explain sales-order allocation reasons.

## Shared Context Rules

- First detail lookup owns `orderContext.detail`.
- Later skills reuse `orderContext.detail` and fetch only missing domain evidence.
- Domain evidence examples: dispatch explain logs, allocation items, hold-rule logs, routing rules, PO recommendation data.
- After any write operation, mark prior detail as stale and re-check before claiming the business state is complete.
- Avoid loops like `query -> allocation get_order_detail -> operations get_order_detail` when no write or stale context exists.

Allowed re-query cases:

- Required fields are missing from `orderContext`.
- The user explicitly asks for latest status after a delay.
- A write just occurred, such as cancel, reopen, release hold, allocation write, hold rule create, or PO creation.
- A focused skill needs a domain endpoint, such as dispatch explain, hold rule, allocation items, or PO recommendation.

## Business Flow Examples

Exception and replenishment:

1. `query` gets detail once.
2. `exception` diagnoses using existing detail plus missing exception evidence.
3. If out of stock, `replenishment` uses SKU/quantity context to suggest or create PO.

Hold and allocation:

1. `query` gets detail once.
2. `hold` checks hold evidence or releases hold after user second confirmation.
3. If allocation status/remaining is needed, `allocation` fetches allocation items only.

Warehouse assignment:

1. `query` gets detail once.
2. `allocation` fetches dispatch explain logs and allocation items.
3. Final answer includes result, reason, confidence, and next step.

Dispatch/fulfillment state:

1. `query` may get detail once.
2. `allocation` reads dispatch/DN/WMS handoff fields and allocation items; it fetches dispatch explain only if the user asks why the warehouse was selected.
3. Final answer says whether allocation is complete, what dispatch/DN/WMS state is confirmed, and whether the next step is warehouse/WMS or allocation retry.

Cancel dispatched order:

1. `query` may get detail for pre-check/risk message.
2. `operations` cancels after user second confirmation.
3. `operations` post-checks sales order and dispatch state before claiming completion.

## Final Output Contract

Final answers must be business-operations friendly:

1. Result.
2. Reason.
3. Solution.
4. Next step.

Do not expose raw JSON by default. Do not turn API acceptance into business completion without post-check evidence.

When composing multiple focused agents, include a compact agent trace:

```text
Handled by: [query/allocation/hold/etc.]
Reused context: [yes/no and why]
Additional evidence fetched: [dispatch explain / hold rules / allocation items / none]
```

## Confirmation Policy

The orchestrator must enforce this rule uniformly:

- Read-only: execute directly.
- Dry-run or draft: execute directly and state that nothing was submitted.
- Real write/action: require explicit second confirmation before execution.

Real writes/actions include test-order creation, cancel, reopen, release hold, manual/auto/force/batch allocation, hold rule create/enable/update, PO creation, and split PO creation.

The confirmation prompt must include environment, action, target object(s), business risk, and exact confirmation phrase.
