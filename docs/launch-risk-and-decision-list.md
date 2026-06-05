# Launch Risk And Decision List

Date: 2026-06-04

## High Priority

| Risk / decision | Impact | Recommendation |
| --- | --- | --- |
| Write confirmation policy | Any real write/action can change OMS workflow state. | Require user second confirmation for every real write/action in production. Read-only and dry-run/draft actions can run directly. Confirmation should include environment, action, target, risk, and exact phrase. |
| Hold exact causality endpoint gap | "Which rule held this exact order" cannot always be proven from current exposed APIs. Candidate matching may be mistaken for direct causality. | Keep candidate wording. Add or expose hold record/order event log endpoint if exact causality is a launch requirement. |
| Cancel downstream state | `ongoingRespDTOS` means WMS/Kafka cancellation is still processing. | Never call cancel complete until post-check confirms sales order and dispatch are cancelled. |
| Allocation ownership | Operations previously overlapped with allocation. | Keep all manual/auto/force/batch allocation under `allocation` only. |

## Medium Priority

| Risk / decision | Impact | Recommendation |
| --- | --- | --- |
| Replenishment warehouse ID only | Some recommendation APIs return warehouse IDs without display names. | Ask user to confirm warehouse display name before PO creation. |
| PO `DISPATCHED` wording | Users may think inventory has arrived. | Say PO entered warehouse flow, not received. |
| Legacy `sales-order` presence | Split agents could accidentally call legacy paths and reintroduce old slow behavior. | Keep legacy for compatibility only; orchestrator must route to focused agents. |
| Batch execution time | OMS lacks some batch endpoints, so scripts run bounded per-order calls. | Keep bounded concurrency and partial results. Surface slowest duration and per-order outcomes. |

## Low Priority

| Risk / decision | Impact | Recommendation |
| --- | --- | --- |
| Raw JSON exposure | Business users may be confused by technical fields. | Default to concise business summaries. Show raw payloads only for debugging requests. |
| Staging data volatility | Fixed sample orders may change status over time. | Keep reports as dated evidence and refresh regression samples before production launch. |

## Go/No-Go Recommendation

Go with guardrails:

- Enable split-agent routing through `order-orchestrator`.
- Require user second confirmation for all real write/action operations.
- Preserve evidence boundaries in user-facing answers.
- Treat hold exact causality as candidate unless direct log evidence exists.
