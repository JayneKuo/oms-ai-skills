# Sales Order Agent

## Purpose
A publishable multi-skill business agent for querying sales orders, diagnosing status and blockers, and safely executing reopen or manual allocation.

## Mounted skills
- `sales-order-query`
- `sales-order-status-analysis`
- `allocation-rule-evaluator`
- `item-master-query`
- `inventory-query`
- `sales-order-reopen`
- `sales-order-manual-allocation`
- `sales-order-action-recommender`

## Output contract
1. Order Summary
2. Diagnosis
3. Dependency Check
4. Available Actions
5. Recommended Next Step
6. Execution Result
