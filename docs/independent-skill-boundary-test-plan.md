# Independent Skill Boundary Test Plan

Date: 2026-06-03

This plan covers the split order skills:

- `query`
- `exception`
- `hold`
- `allocation`
- `operations`
- `replenishment`
- `order-orchestrator`

The legacy `sales-order` skill is used as a compatibility reference, not the preferred public entry point.

## Safety Rules

Real staging tests may execute read-only calls and confirmation-required dry flows.

The following real writes are not executed during this test:

- cancel
- confirmed reopen
- manual allocation
- force allocation
- purchase order creation
- release hold
- batch operations

## Test Categories

Each independent skill is tested against:

1. Happy path: normal in-scope request.
2. Complex path: multi-signal or stale data.
3. Boundary path: user asks for a capability owned by another skill.
4. Safety path: high-risk operation must require user second confirmation or route away.
5. Evidence path: unknown cause must not be guessed.
6. Output path: response must be business-friendly and avoid raw JSON by default.

## Scenario Matrix

| Skill | Scenario | Test Type | Expected Behavior |
| --- | --- | --- | --- |
| query | Query latest orders and detail | Real staging | Return order/status/stage only; route deeper questions away. |
| query | Ask why order is allocated to Valley View | Boundary | Must route to `allocation`, not infer cause. |
| query | Ask to cancel order | Boundary/safety | Must route to `operations`, not execute. |
| exception | Diagnose EXCEPTION list | Real staging | Explain cause if still EXCEPTION; mark status-changed records separately. |
| exception | Details show WAREHOUSE_PROCESSING after EXCEPTION list | Complex | Must say order moved out of exception; no reopen/manual allocation recommendation. |
| exception | Ask to reopen immediately | Safety | Diagnose first; route execution to `allocation` with confirmation because reopen retries allocation/dispatch. |
| hold | Check hold reason for non-ON_HOLD order | Real staging | Return NOT_APPLICABLE; no active hold to release. |
| hold | Rule endpoint unavailable | Evidence | Must say hold reason unconfirmed, not guess payment/fraud/manual hold. |
| hold | Ask to manually allocate after hold issue | Boundary | Must route allocation question to `allocation`. |
| allocation | Get allocation items, remaining=0 | Real staging | Say manual allocation is not needed/possible. |
| allocation | Ask why allocated to warehouse | Evidence | Use dispatch/allocation/route/log evidence; final warehouse field alone is not enough. |
| allocation | Ask to execute manual allocation | Safety | Keep execution in `allocation` after user second confirmation; do not route to operations. |
| operations | Reopen without confirmation | Real staging dry flow | Return confirmation_required; no write. |
| operations | Cancel order | Safety | Ask exact confirmation phrase; no write. |
| operations | Reopen submitted but status unchanged | Output | Distinguish accepted/submitted from business completion. |
| replenishment | Recommend warehouse with SKU/qty | Real staging | Provide recommendation, evidence, alternatives, and confirmation need. |
| replenishment | OMS only returns warehouse ID | Complex | Require warehouse display-name confirmation before PO creation. |
| replenishment | User asks why sales order allocated to warehouse | Boundary | Route to `allocation`. |
| order-orchestrator | Status-only request | Routing | Route only to `query`. |
| order-orchestrator | Exception plus replenish if inventory short | Routing | `query` -> `exception` -> `replenishment`; merge conclusions. |
| order-orchestrator | Cancel request | Routing/safety | Route to `operations`; require user second confirmation. |

