# Sales Order API Discovery

## Skill-to-dependency map
- `sales-order-query` — requires sales-order list/detail APIs
- `sales-order-status-analysis` — requires sales-order detail plus status-bearing fields
- `sales-order-reopen` — requires reopen action API and eligibility rules
- `sales-order-manual-allocation` — requires manual-allocation action API and target-warehouse inputs
- `allocation-rule-evaluator` — requires allocation-rule lookup APIs
- `item-master-query` — requires item-master lookup APIs
- `inventory-query` — requires inventory lookup APIs
- `sales-order-action-recommender` — requires outputs from the other skills

## First confirmed implementation slice

### 1. Sales order list query
- OpenAPI endpoint: `GET /rpc-api/sales-order/page`
- Live staging gateway proven: `GET /api/linker-oms/opc/app-api/sale-order/page`
- Why needed: primary entry for `sales-order-query`
- Required request inputs proven in live staging:
  - query: `pageNo`, `pageSize`, `merchantNo`
  - optional query examples: `keyword`, `statuses`
  - headers: `Authorization`, `x-tenant-id`, `USER`
- Live response shape observed: `{"code":0,"data":{"list":[...]}}`

### 2. Sales order detail query
- OpenAPI endpoint: `GET /rpc-api/sales-order/{orderNo}`
- Live staging gateway proven: `GET /api/linker-oms/opc/app-api/sale-order/{orderNo}`
- Why needed: detail lookup for `sales-order-query` and status diagnosis
- Required request inputs proven in live staging:
  - path: `orderNo`
  - headers: `Authorization`, `x-tenant-id`, `USER`
- Live response shape observed: `{"code":0,"data":{"orderNo":"..."}}`

### 3. Sales order reopen action
- OpenAPI endpoint: `POST /app-api/sale-order/reopen/{orderNo}`
- Live staging gateway candidate: `POST /api/linker-oms/opc/app-api/sale-order/reopen/{orderNo}`
- Why needed: first confirmed order action for `sales-order-reopen`
- Required request inputs inferred from the working query/detail gateway:
  - path: `orderNo`
  - headers: `Authorization`, `x-tenant-id`, `USER`
- Validation status: path updated to match the proven `opc/app-api/sale-order/*` gateway family. The agent and smoke runner now require user second confirmation before calling reopen. Live execution against a real order is still intentionally not performed yet.

### Deferred after first slice
- `POST /dispatch/sales-order` remains a confirmed downstream action path for allocation/manual split workflows, but it is not the first implementation slice.
- Allocation rules, item master, and inventory endpoints remain discovery targets before manual allocation implementation.

## Discovery rules
- Only endpoints proven in the approved OMS source inputs are allowed into implementation scope.
- Do not carry forward shipping or mapping workflows.
- Record endpoint path, request shape, response shape, and why the endpoint is needed.
