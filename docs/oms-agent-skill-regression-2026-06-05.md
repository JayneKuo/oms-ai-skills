# OMS Agent/Skill Regression Report

Date: 2026-06-05
Environment: staging

## Scope

Regression followed the launch runbook business order:

1. `query`
2. `allocation`
3. `hold`
4. `exception`
5. `replenishment`
6. write-operation gates for `query`, `allocation`, `hold`, `operations`, and `replenishment`

No real write operation was submitted during this regression. Write paths were validated through script-level confirmation gates.

## Read/Diagnosis Regression Results

| Flow | Command / case | Result | Verdict |
| --- | --- | --- | --- |
| `query` | `get_order_detail.py --order SO01392133` | Returned `WAREHOUSE_PROCESSING`, dispatch count `1`, next skill `allocation`. | Passed |
| `allocation` | `explain_warehouse_assignment.py --order SO01392133 --compare-warehouse "Valley View"` | Confirmed Valley View from dispatch explain logs. Candidate warehouses were Joliet, Valley View, Fontana; all had zero inventory for `BATESTSKU-1`; decisive rule routed insufficient inventory to highest-priority warehouse. | Passed |
| `allocation` | `get_allocation_items.py --order SO01392133` | Returned SKU `BATESTSKU-1`, total `2`, allocated `2`, remaining `0`. | Passed |
| `hold` | `hold_rules.py --action list --status ENABLED` | Returned enabled rule `batest0602`, priority `55`, permanent hold mode, channel/order-source scope. | Passed |
| `hold` | `match_hold_rules_to_orders.py --orders SO01376525 SO01376524` | Returned historical/disabled candidates only and explicitly labeled direct causality as unconfirmed. | Passed |
| `exception` | `diagnose_exception.py --order SO01373341` | Confirmed EXCEPTION cause as out of stock for SKU `DSPM-NL21-WOODLGH`; routed next step to replenishment before allocation-owned reopen retry. | Passed |
| `replenishment` | `suggest_purchase_order.py --sku BATESTSKU-1 --quantity 10` | Suggested first visible warehouse, returned alternatives, warned warehouse display name is not confirmed, and kept routing rules as context only. | Passed |

## Write Gate Regression Results

All focused write scripts now require explicit confirmation flags. Without the flag they return `CONFIRMATION_REQUIRED` and `_request.submittedToOms=false`.

| Write path | Required flag | Gate result |
| --- | --- | --- |
| `query/scripts/create_order.py` | `--confirm-create` | Not submitted without flag. |
| `allocation/scripts/manual_allocate.py` | `--confirm-allocation` | Not submitted without flag; still returns pre-allocation evidence. |
| `allocation/scripts/batch_allocation.py --action manual_allocate` | `--confirm-allocation` | Not submitted without flag. |
| `hold/scripts/release_hold.py` | `--confirm-release` | Not submitted without flag. |
| `hold/scripts/diagnose_hold.py --release` | `--confirm-release` | Diagnosis runs; release is not submitted without flag. |
| `operations/scripts/cancel_order.py` | `--confirm-cancel` | Not submitted without flag. |
| `allocation/scripts/reopen_order.py` | `--confirm-reopen` | Not submitted without flag. |
| `operations/scripts/batch_orders.py` | `--confirm-execute` | Not submitted without flag. |
| `replenishment/scripts/create_purchase_order.py` | `--confirm-create` | Not submitted without flag. |
| `replenishment/scripts/create_purchase_order_split.py` | `--confirm-create` | Not submitted without flag. |

## Fixes Applied During Regression

- Added script-level hard confirmation gates to all focused real-write scripts.
- Updated focused skill command examples to include confirmation flags for real writes.
- Rewrote `hold/scripts/release_hold.py` as clean UTF-8 and added a non-submit confirmation response.
- Updated `diagnose_hold.py --release` so release requires `--confirm-release`.

## Remaining Boundaries

- Hold exact rule causality remains limited when direct hold execution logs/records are unavailable. Candidate matching must remain labeled as candidate/historical.
- Replenishment warehouse recommendation still needs warehouse display-name confirmation when OMS returns only warehouse IDs.
- Legacy `skills/sales-order` remains a compatibility path and is not the launch entry point for split-agent workflows.

## Validation

- `python -m compileall -q skills`: passed.
- `npm.cmd test`: passed, 45 files / 81 tests.
