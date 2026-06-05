# Sales Order MCP Tools

## query_sales_orders
按关键词、状态分页查询订单列表。

| 参数 | 类型 | 说明 |
|------|------|------|
| pageNo | number | 页码，默认 1 |
| pageSize | number | 每页数量，默认 20 |
| keyword | string? | 关键词 |
| statuses | string[]? | 状态过滤，如 `["EXCEPTION", "ON_HOLD"]` |

---

## get_sales_order_detail
获取单个订单完整详情，含自动诊断结果。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |

返回：`diagnosis`、`availableActions`、`recommendedNextStep`、`inventorySummary`（如有）

---

## release_hold
尝试释放 ON_HOLD 订单。失败时说明原因（已全部分配 / 业务规则锁定）。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |

---

## check_manual_allocation
检查订单是否可以手动分配。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |

返回：`data: true/false`

---

## get_manual_allocation_items
获取订单中可手动分配的商品行，含 `remaining`（未分配数量）。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |

---

## manual_allocate
提交手动分配请求。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |
| mode | "SKU"\|"ORDER" | 分配模式，默认 SKU |
| warehouseList | array | 仓库列表，每项含 `warehouseCode`、`warehouseName`、`skuList` |

---

## suggest_purchase_order
根据库存和路由规则推荐补货方案，供用户确认后执行。

| 参数 | 类型 | 说明 |
|------|------|------|
| items | array | SKU 列表，每项含 `sku`、`quantity` |

返回：`availableWarehouses`、`routingRules`（上下文）、`suggestedPlan`

---

## create_purchase_order
创建补货采购单（单仓）。

| 参数 | 类型 | 说明 |
|------|------|------|
| targetWarehouseNo | string | 目标仓库编号 |
| items | array | SKU 列表，每项含 `sku`、`quantity` |

---

## get_routing_rules
读取当前商户的路由规则列表。规则是调度策略开关，不含仓库映射。

无参数。

---

## reopen_sales_order
重新开启 EXCEPTION 状态的订单。

| 参数 | 类型 | 说明 |
|------|------|------|
| orderNo | string | 订单号 |
