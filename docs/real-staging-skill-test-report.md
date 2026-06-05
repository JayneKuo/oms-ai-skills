# Real Staging Skill Test Report

Date: 2026-06-03

Environment: staging, loaded from `.env.example`.

Sensitive values such as username, password, and tokens are intentionally not repeated here.

## What Was Tested

This test used real staging OMS calls for read-only and non-mutating confirmation flows.

Mutating operations were not executed:

- cancel
- confirmed reopen
- manual allocation execution
- purchase order creation
- release hold execution

## Results

| Scenario | Path | Result | Time | Content Quality |
| --- | --- | --- | --- | --- |
| Query latest sales orders, page size 3 | TypeScript `sales-order:smoke` | Pass | 8149 ms | Correct, but output is structured JSON and needs business-language summarization. |
| Get detail for `SO01385247` | TypeScript `sales-order:smoke` | Pass | 5818 ms | Correct and concise. Should translate `WAREHOUSE_PROCESSING` for business users. |
| Diagnose exception list, page size 2 | TypeScript `sales-order:smoke` | Watch | 6684 ms | API query returned records whose detail status is now `WAREHOUSE_PROCESSING`; response marked them blocked. Needs clearer wording for stale/status-changed exception results. |
| Get routing rules | TypeScript `sales-order:smoke` | Pass | 7264 ms | Correct diagnosis that routing rules are context, not SKU-to-warehouse mapping. Raw routing JSON is too verbose for users. |
| Suggest PO for `BATESTSKU-1`, 100 EA | TypeScript `sales-order:smoke` | Pass | 7203 ms | Found one warehouse and a plan. User output should hide raw routing JSON and explain warehouse ID/name clearly. |
| Reopen without confirmation | TypeScript `sales-order:smoke` | Pass | 3019 ms | Good. It required confirmation and did not execute the write. |
| Query latest sales orders, page size 2 | Python `skills/query` | Pass after auth fix | 4577 ms | Real API call works. Raw API payload is too large for end users. |
| Get detail for `SO01385247` | Python `skills/query` | Pass after auth fix | 4274 ms | Real API call works and includes dispatch evidence such as warehouse `Valley View`. Needs summarization. |
| Get routing rules | Python `skills/replenishment` | Pass after auth fix | 4713 ms | Real API call works. Raw output should be summarized. |
| Get allocation items for `SO01385247` | Python `skills/allocation` | Pass after auth fix | 4231 ms | Strong result: `remaining=0`, so agent should say manual allocation is not needed/possible. |
| Check manual allocation for `SO01385247` | Python `skills/allocation` | Pass after auth fix | 4351 ms | API returned `ERROR.THE_STATUS_NOT_SUPPORT_ALLOCATED`; agent must translate this instead of exposing the code. |
| Get hold reason for `SO01376473` | Python `skills/hold` | Pass with caveat | 5693 ms | Rule endpoint returned 404 and script handled it gracefully. Order status is `WAREHOUSE_PROCESSING`, so user reply should say it is not currently ON_HOLD. |

## Fix Applied During Testing

The TypeScript runner authenticated successfully, but the split Python skills initially failed with HTTP 401.

Root cause: Python `oms_client.py` preferred `OMS_IAM_BASE_URL` for `/api/linker-oms/opc/iam/token`, while the working TypeScript token provider calls the token endpoint under `OMS_BASE_URL`.

Fix: all skill-local `oms_client.py` copies now return `OMS_BASE_URL` from `_iam_base_url()`.

Affected files:

- `skills/allocation/scripts/oms_client.py`
- `skills/exception/scripts/oms_client.py`
- `skills/hold/scripts/oms_client.py`
- `skills/operations/scripts/oms_client.py`
- `skills/query/scripts/oms_client.py`
- `skills/replenishment/scripts/oms_client.py`
- `skills/sales-order/scripts/oms_client.py`

## User Experience Findings

### Good

- Real staging authentication works.
- Read-only calls complete in about 4.2-8.1 seconds.
- Confirmation flow for reopen is safe and fast.
- Allocation evidence is strong enough to prevent bad manual allocation recommendations.
- Hold reason script handles unavailable rule endpoint without guessing.

### Needs Improvement Before Broad Launch

1. Raw JSON is too verbose for business users.
   The scripts and TypeScript agent return correct data, but user-facing agent replies must summarize and hide raw payloads by default.

2. Exception diagnosis should handle stale results.
   When the exception query returns orders that are no longer EXCEPTION in detail, the agent should say: "These orders appear to have moved out of EXCEPTION; current status is WAREHOUSE_PROCESSING." It should not mark them as blocked.

3. Warehouse recommendation should show readable warehouse names.
   PO recommendation currently produced warehouse ID `2005833934970490882` as both number and name. If no friendly name is available, say it is an ID and recommend confirming the warehouse display name before creating a PO.

4. Hold skill should first check current status.
   If the order is not currently ON_HOLD, tell the user there is no active hold to release, then explain that hold-rule evidence is not applicable unless historical logs are requested.

5. Windows PowerShell JSON examples need a safer pattern.
   Scripts requiring `--skus` JSON are fragile in PowerShell. Add alternative flags like `--sku BATESTSKU-1 --quantity 100`, or document a PowerShell-safe invocation.

## Launch Recommendation

Controlled launch is reasonable if `order-orchestrator` is the public entry point and all final replies are generated from the new guardrails.

Do not expose raw script output directly to users. The agent should always convert script output into:

1. Result
2. Reason/evidence
3. What is confirmed vs unconfirmed
4. Next step

## Remediation Update

Completed after the first real staging run:

1. Python skill authentication now matches the working TypeScript runner by using `OMS_BASE_URL` for the Linker OMS token endpoint.
2. Exception diagnosis now separates stale/status-changed results. Orders returned by an EXCEPTION list query but currently `WAREHOUSE_PROCESSING` are reported under `statusChanged`, not `blocked`.
3. Replenishment recommendation now includes `routingRuleSummary`, `warehouseDisplayName`, and `needsWarehouseNameConfirmation` when OMS only returns a warehouse ID.
4. `suggest_purchase_order.py` and `create_purchase_order.py` now support `--sku` plus `--quantity` as a PowerShell-friendly alternative to JSON `--skus`.
5. `get_hold_reason.py` now exits early when the latest order detail is not `ON_HOLD`, instead of calling the hold-rule endpoint and implying active hold diagnosis.

Retest results:

| Scenario | Result | Time |
| --- | --- | --- |
| Diagnose exception list with status-changed records | Pass; records moved to `statusChanged` | 9057 ms |
| Suggest PO with `--sku BATESTSKU-1 --quantity 100` | Pass; no JSON quoting issue and warehouse-name confirmation is explicit | 6206 ms |
| Get hold reason for non-ON_HOLD order | Pass; returns `NOT_APPLICABLE` and says no active hold exists | 4589 ms |

Post-remediation verification:

- `python -m compileall -q skills` passed.
- `npm.cmd test` passed: 45 test files, 81 tests.
