# Exception Skill Validation Report

Validation date: 2026-06-04

Scope: `skills/exception` only.

## Real Staging Cases

| Order | Latest status | Evidence | Diagnosis |
| --- | --- | --- | --- |
| `SO01373341` | `EXCEPTION` | `reserve1`: product `DSPM-NL21-WOODLGH` out of stock; allocated `0`; remaining `1`; no dispatch | Confirmed out-of-stock exception. Route to replenishment first; reopen only after stock is handled and business confirms retry. |
| `SO01373322` | `EXCEPTION` | `reserve1`: product `DSPM-NL21-WOODDK` out of stock; allocated `0`; remaining `1`; no dispatch | Confirmed out-of-stock exception. Route to replenishment first. |
| `SO01392133` | `WAREHOUSE_PROCESSING` | Detail status no longer `EXCEPTION`; dispatch exists; remaining `0` | Stale/non-exception boundary. Do not recommend exception actions. |
| `SO00000000` | not found | Detail API returned `Get Order Data Error` | Not diagnosable; ask user to confirm order/environment. |

## Fixes Applied

- Added `skills/exception/scripts/diagnose_exception.py`.
- Diagnosis now verifies latest detail status before recommending actions.
- Out-of-stock cause is extracted from `reserve1` and reported as confirmed evidence.
- Batch diagnosis supports explicit order lists and latest EXCEPTION list rows with bounded concurrency.
- Output includes per-order `state`, `category`, `causeConfirmed`, `solution`, `nextStep`, and `userFacingSummary`.
- Agent and skill prompts now require `diagnose_exception.py` for cause/solution workflows.

## Ability Boundary

Exception can independently complete:

- Query latest EXCEPTION list.
- Diagnose one or more orders.
- Detect stale list rows whose detail status changed.
- Confirm out-of-stock exceptions from detail evidence.
- Separate shortage follow-up (`replenishment`) from retry/reopen follow-up (`allocation`).

Exception must not:

- Execute reopen/cancel/manual allocation/PO creation.
- Recommend reopen for non-EXCEPTION latest statuses.
- Guess inventory, routing, or warehouse causes without evidence.
- Treat a list row as truth without detail verification.

## Batch Behavior

`diagnose_exception.py --orders ... --max-workers 4` was tested against four mixed cases and returned in about 5.5 seconds:

- 2 confirmed EXCEPTION out-of-stock orders.
- 1 status-changed order.
- 1 not-found order.

One failed/not-found order does not block other results.
