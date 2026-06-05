# OMS AI Skills Launch Acceptance Package

Date: 2026-06-04

Environment: staging from `.env.example`

Credentials: omitted

## Verdict

Launch readiness: **Ready with documented caveats**.

The independent order skills have been tested against real staging APIs, including read workflows, rule diagnosis, allocation explanation, cancel post-check, hold release boundaries, PO creation, and batch partial-failure behavior.

Production write policy: read-only actions may run directly; dry-run/draft actions may run directly; every real write/action must require user second confirmation before execution.

## Fixed Regression Matrix

| Flow | Real sample | Owning skill path | Acceptance result |
| --- | --- | --- | --- |
| Query current order | `SO01392133` | `query` | Passed. Detail returns `WAREHOUSE_PROCESSING`, dispatch count `1`, and `nextSkill=allocation`. |
| Explain warehouse allocation | `SO01392133` | `query -> allocation` | Passed. Allocation uses dispatch explain logs and explains Valley View from routing rule, candidate warehouses, inventory checks, and final dispatch. |
| Diagnose EXCEPTION shortage | `SO01373341` | `exception -> replenishment` | Passed. Exception confirms out-of-stock SKU `DSPM-NL21-WOODLGH` and routes to replenishment before reopen. |
| Diagnose ON_HOLD rule | `SO01376525` | `hold` | Passed with caveat. Hold identifies historical/candidate rules by SKU `CCC`; exact causality remains unconfirmed without direct hold logs. |
| Cancel dispatched order boundary | `SO01405073` | `operations` | Passed. Repeat cancel is rejected as already cancelled, but post-check confirms sales order and dispatch are cancelled. |
| Replenishment recommendation | `DSPM-NL21-WOODLGH`, qty `1` | `replenishment` | Passed. Suggests visible warehouse ID with routing context and display-name confirmation warning. |
| Hold rule creation from natural language | "Launch dry run imported hold" | `hold` | Passed. Natural language created a disabled rule draft; no OMS write was submitted without `--confirm-create`. |
| Batch allocation partial failure | `SO01392133`, `SO00000000` | `allocation` | Passed. Batch returned one ok and one failed result with bounded execution. |

## Final Agent Capability Checklist

| Agent | Independent capability | Write ownership | Launch status |
| --- | --- | --- | --- |
| `query` | List/detail/status, exact detail fallback, business summary, explicit test-order creation | Test order creation after second confirmation | Ready |
| `exception` | EXCEPTION diagnosis, stale-status detection, out-of-stock routing, batch diagnosis | None | Ready |
| `hold` | ON_HOLD diagnosis, release hold, hold rule list/get/active-count, rule-to-order candidate mapping, natural-language rule draft/create | Release hold and hold rule create after second confirmation | Ready with caveats |
| `allocation` | Allocation result/reason, dispatch/DN/WMS/fulfillment state, dispatch explain, remaining qty, manual allocation eligibility, dispatch release/retry, batch allocation, allocation writes | Manual/auto/batch allocation after second confirmation and precheck | Ready |
| `operations` | Cancel, batch cancel, cancel-specific downstream/WMS post-check, rejection interpretation | Cancel after second confirmation | Ready |
| `replenishment` | Replenishment recommendation, warehouse evidence, single/split PO creation | PO creation after second confirmation | Ready with caveats |
| `order-orchestrator` | Intent routing, shared `orderContext` reuse, multi-step composition | No direct writes | Ready |

## Ownership Rules To Enforce At Runtime

- `release hold` belongs to `hold`, not `operations`.
- `manual/auto/force/batch allocation`, dispatch release/retry, and general dispatch/fulfillment diagnosis belong to `allocation`, not `operations`.
- `cancel` belongs to `operations`; `reopen-for-allocation retry` belongs to `allocation`.
- `hold rule query/create` belongs to `hold`.
- `PO/replenishment` belongs to `replenishment`.
- `sales-order` legacy must not be used as a hidden dependency for split-agent workflows.

## Production Confirmation Policy

- Read-only actions: execute directly.
- Dry-run or draft actions: execute directly and state that nothing was submitted.
- Real writes/actions: require explicit second confirmation before execution.

Real writes/actions include:

- Test-order creation.
- Cancel and reopen.
- Release hold.
- Manual/auto/force/batch allocation.
- Hold rule create/enable/update.
- PO creation and split PO creation.

Confirmation prompts must include environment, action, target object(s), business risk, and exact confirmation phrase.

## Evidence Boundaries

- Hold rule exact causality is not always provable from exposed staging APIs. Current implementation can show candidate/historical rule matches from rule config and order fields, but must not claim exact causality without hold execution logs, order event logs, or hold records.
- Replenishment warehouse recommendation may only have warehouse ID evidence. If display name is missing, the user must confirm the target warehouse display name before PO creation.
- Dispatch/DN/WMS/warehouse-processing visibility is allocation-domain evidence after allocation; operations only uses dispatch state to prove cancel completion.
- Cancel may return `ongoingRespDTOS`; this means downstream/WMS cancellation is in progress. Completion requires post-check of sales order and dispatch records.
- `DISPATCHED` purchase order status means the PO entered warehouse flow; it does not prove inventory has been received.
- Routing rule configuration is context, not proof of sales-order allocation. Allocation reason must come from dispatch explain logs or equivalent execution trace.

## User-Facing Output Rules

- Start with the result.
- Then explain the evidence-backed reason.
- Then give solution and next step.
- Do not expose raw JSON by default.
- Do not claim success from `code=0` alone.
- For writes, distinguish submitted, ongoing, rejected, and business-completed.
- For batch operations, return per-order outcomes and do not let one slow/failed order hide the rest.

## Final Verification

- `python -m compileall -q skills`: passed
- `npm.cmd test`: passed, 45 files / 81 tests

## Remaining Launch Decisions

- Product policy accepted: every real write/action requires user second confirmation in production UX.
- Product policy accepted: users may create ENABLED hold rules only after user second confirmation; otherwise the skill should keep rule creation as a dry-run/draft.
- Observability: if exact hold causality is required, expose or document a direct hold-record/order-event endpoint for the agent.
