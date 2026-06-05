# Independent OMS Order Agent Matrix

Date: 2026-06-03

Scope: split order agents under `agent/` and `skills/`. Legacy `sales-order` is excluded from optimization scope and kept only for compatibility/regression.

## Operating Principle

Each focused agent must be able to complete its own business loop without calling the legacy `sales-order` agent:

1. Understand the user intent in its domain.
2. Call its own skill scripts or evidence sources.
3. Return a business-friendly result, reason, solution, and next step.
4. Handoff only when the request leaves its domain or requires a confirmed write.

`order-orchestrator` is the public routing layer. It does not own OMS API calls; it calls focused agents in business-process order and merges their conclusions.

Every functional agent owns a minimum base-query capability: `get_order_detail.py`. This does not make every agent a general query agent; it lets each agent independently verify the latest order status before diagnosing, acting, or handing off. `query` remains the dedicated list/detail/status agent.

For launch execution details, see `docs/oms-agent-skill-launch-runbook.md`. That runbook is the source for default routing, standard output templates, second-confirmation prompts, and regression prompts.

## Shared Context And De-Duplication

Standalone mode and orchestrated mode are different:

- Standalone mode: a focused agent may call `get_order_detail.py` itself to verify current order status.
- Orchestrated mode: the first agent that fetches order detail must pass an `orderContext` object to later agents. Later agents must reuse it instead of calling the same detail endpoint again.

Allowed re-query cases:

1. Required fields are missing from `orderContext`, such as `orderDispatchList`, `itemLines`, current `status`, address, or SKU fields.
2. The prior context is stale for the requested decision, for example the user asks for latest status after a delay.
3. A write operation just occurred, such as cancel, reopen, release hold, manual allocation, or PO creation, and a post-write status check is required.
4. The later agent needs a domain-specific evidence endpoint that is not in context, such as dispatch explain logs, hold-rule logs, routing rules, allocation items, or PO recommendation evidence.

Forbidden loop:

`query -> focused agent get_order_detail -> operations get_order_detail` when the original detail is still fresh and no write has happened. The orchestrator should pass `orderContext` and ask focused agents to return only missing domain evidence.

Recommended shared context shape:

```json
{
  "orderNo": "SO...",
  "fetchedAt": "2026-06-03T12:00:00Z",
  "sourceAgent": "query",
  "detail": {},
  "dispatchExplain": {},
  "allocationItems": {},
  "holdEvidence": {},
  "operationResult": {}
}
```

## Agent Capability Matrix

| Agent | Owns | Independent scripts / evidence | Write ability | Required user-facing output | Handoff target |
| --- | --- | --- | --- | --- | --- |
| `query` | Order list, exact detail fallback, basic status, test order creation | `query_orders.py`, `get_order_detail.py`, `create_order.py` | Test-order creation only after second confirmation | Order exists/status/stage, confirmed facts, business summary, next focused agent if deeper analysis is needed | `exception`, `hold`, `allocation`, `operations`, `replenishment` |
| `allocation` | Warehouse result, automatic/manual allocation reason, remaining qty, manual allocation eligibility, batch allocation workflows | `explain_warehouse_assignment.py`, `get_allocation_items.py`, `check_manual_allocation.py`, `get_order_detail.py`, `get_routing_rules.py`, `manual_allocate.py`, `batch_allocation.py`, dispatch explain endpoint | Manual/auto/force/batch allocation belongs to allocation; every real write requires second confirmation and precheck | Assigned warehouse, dispatch number/status, SKU qty, remaining qty, dispatch explain reason, confidence; batch replies include per-order state | `replenishment` if shortage needs PO; `operations` only for non-allocation order writes |
| `exception` | EXCEPTION list/detail diagnosis and resolution recommendation | `query_orders.py`, `get_order_detail.py`, detail diagnosis fields, dispatch/allocation evidence when available | No | Whether still exception, evidence-backed cause or evidence gap, solution, next action | `operations` for reopen/cancel; `allocation` for allocation blockers; `replenishment` for shortage |
| `hold` | ON_HOLD status, hold rule evidence, hold rule query/create draft, rule-to-order candidate mapping, release-hold assessment | `get_order_detail.py`, `get_hold_reason.py`, `release_hold.py`, `get_allocation_items.py`, `diagnose_hold.py`, `hold_rules.py`, `match_hold_rules_to_orders.py`, ORDER_HOLD_OR rule execution when available | Release script exists; hold rule create exists but defaults to dry-run; every real hold write requires second confirmation | Hold status, matched rule/log if available, candidate/historical rule matches with evidence boundary, rule summary, release result, allocation-vs-hold blocker distinction | `operations` only for non-hold order writes; `allocation` if remaining/allocation is the blocker |
| `operations` | High-impact non-allocation cancel/reopen and async result interpretation | `get_order_detail.py`, `cancel_order.py`, `reopen_order.py`, `batch_orders.py` | Yes, only after user second confirmation; no allocation writes and no hold-release writes | Submitted/completed/ongoing result, what is confirmed, downstream/WMS follow-up, rejection reason, post-cancel dispatch state | Back to `allocation`/`hold` for domain-specific post-checks |
| `replenishment` | Replenishment recommendation, purchase warehouse explanation, single/split PO creation | `get_order_detail.py`, `suggest_purchase_order.py`, `get_routing_rules.py`, `create_purchase_order.py`, `create_purchase_order_split.py` | PO creation after second confirmation | Recommended warehouse, evidence, alternatives, name-confirmation need, PO number/status after creation, inventory-not-yet-received boundary | `allocation` for sales-order warehouse reason; `operations` for order actions |
| `order-orchestrator` | Intent routing, shared context reuse, and multi-agent workflow composition | No direct scripts; uses focused agents | No direct writes | Merged business answer: result, reason, solution, next step, evidence boundaries | Focused agents only |

## Business Flow Matrix

| Business stage | First agent | Required checks | Possible next agent |
| --- | --- | --- | --- |
| User asks "where is this order?" | `query` | Detail lookup; translate status | `allocation` if warehouse reason is requested |
| Order is `WAREHOUSE_PROCESSING` / dispatched | `allocation` | Dispatch detail, dispatch explain log, remaining qty | `operations` for cancel/reopen only; `replenishment` if stock issue |
| Order is `EXCEPTION` | `exception` | List/detail freshness, evidence fields, solution path | `operations`, `allocation`, `replenishment` |
| Order is `ON_HOLD` | `hold` | Detail status, hold rule/log, candidate rule mapping, release result, remaining qty | `operations`, `allocation` |
| User asks about hold rules | `hold` | Rule list/get/active-count; candidate order matching if requested | `order-orchestrator` for summary only |
| User asks to cancel/reopen/batch | `operations` | Confirmation, execute, follow-up detail/status, dispatch cancel status | `query`, `allocation` |
| User asks "need replenishment / create PO" | `replenishment` | SKU/qty, warehouse recommendation, routing context, confirmation | `allocation` after inventory arrives |
| Multi-step request | `order-orchestrator` | Route in business order; no direct API calls | Any focused agent |

## Multi-Agent Call Rules

| Situation | Rule |
| --- | --- |
| First agent already fetched order detail | Pass `orderContext.detail` to the next agent. |
| Allocation needs warehouse reason | Reuse `orderContext.detail`; fetch only dispatch explain logs if missing. |
| Hold needs release assessment | Reuse `orderContext.detail`; fetch only hold rule evidence and allocation items if missing. |
| Hold needs rule query/create | Use `hold_rules.py`; create stays dry-run unless the user gives second confirmation for a real submit. |
| Hold needs "which orders by rule" | Use direct hold records/logs if available; otherwise use candidate matching and label the evidence boundary. |
| Operations is asked to cancel/reopen | Reuse prior detail for pre-check/risk message; re-query only after the write. |
| Replenishment follows exception/allocation | Reuse SKU/order context; fetch PO-specific recommendation evidence only. |
| Any write completes or returns ongoing | Mark context as state-changing and require post-write re-query before final completion claim. |

## Independence Criteria

An agent is considered independent only if it has all of these:

- Own scripts or explicit evidence endpoints in its skill folder.
- Minimum base query: `get_order_detail.py` for current order status/context, except `order-orchestrator` which does not execute scripts.
- A clear `Use When` domain and explicit "do not own" boundaries.
- A user-facing output contract that does not expose raw JSON by default.
- A failure/boundary behavior, such as rejected writes, stale list rows, async downstream work, or missing evidence.
- A defined handoff target for work outside its domain.

## Current Readiness

| Agent | Independent readiness | Notes |
| --- | --- | --- |
| `query` | Ready | Exact order number falls back to detail lookup; detail returns business summary and next focused skill. |
| `allocation` | Ready | Automatic allocation reason now comes from dispatch explain logs before fallback evidence. |
| `exception` | Ready with guardrails | Can list/detail exceptions; should not execute reopen itself. |
| `hold` | Ready with caution | Can diagnose/release/query rules/draft rules/map candidate rule matches; must not overstate `data=false`, candidate matches, or unconfirmed hold causes. |
| `operations` | Ready for controlled use | Requires confirmation; cancel now post-checks sales order and dispatch state; release hold belongs to `hold`. |
| `replenishment` | Ready with caution | Single and split PO creation work; recommendation explains warehouse ID/name uncertainty and routing context. |
| `order-orchestrator` | Ready as router | No direct scripts by design; corrected ownership for hold release, allocation writes, and operations writes. |

## Minimum Regression Scenarios

| Scenario | Expected owning agent | Expected result |
| --- | --- | --- |
| Query `SO01392133` | `query` | Returns exact detail via fallback and status `WAREHOUSE_PROCESSING`. |
| Explain why `SO01392133` went to `Valley View` | `allocation` | Uses dispatch explain logs: candidate warehouses, inventory check, decisive rule, final dispatch. |
| Try manual allocation on fully allocated order | `allocation` | OMS rejection is translated; no new warehouse is claimed. |
| Query EXCEPTION list | `exception` | Returns candidates and requires detail freshness before diagnosis. |
| Reopen non-exception order | `operations` | Reports OMS rejection `Order not exception`. |
| Release hold on non-hold order | `hold` | Says no active hold/release not applicable. |
| Query hold rules | `hold` | Lists rule name/status/mode/priority/scope and active count when requested. |
| Ask which rules held ON_HOLD orders | `hold` | Returns direct proof if logs exist, otherwise candidate/historical matches with evidence boundary. |
| Suggest PO for SKU/qty | `replenishment` | Gives warehouse, reason/context, confirmation need. |

## Legacy Phase-1 Compatibility

This section is retained for older phase-1 scope docs and tests. It does not change the current split-agent optimization scope.

| Legacy Agent | Purpose | Publish Model | Phase 1 Status |
| --- | --- | --- | --- |
| Sales Order Agent | Query, diagnose, and act on sales orders | Multi-skill business agent | implementation-first |
| Product Agent | Query, create, sync, and diagnose products | Multi-skill business agent | documentation-only |
| Purchase Order Agent | Query, create, push, and diagnose purchase orders | Multi-skill business agent | documentation-only |
