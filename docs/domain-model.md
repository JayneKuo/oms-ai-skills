# Domain Model

This workspace uses the approved OMS ontology as its vocabulary baseline.

## Core business concepts for Phase 1
- `Linker OMS` — the system boundary
- `Order Processing Center` — the primary order-processing project boundary
- `Product` — the core product/catalog entity family for the product module
- `Sales Order` — the core transactional order unit for the sales-order module
- `Purchase Order` — the replenishment/procurement order unit for the purchase-order module
- `Order Line Item` — SKU-level order detail shared across order workflows

## Phase 1 mapping into code
- Auth concerns map to shared runtime auth, token provider, and IAM service
- Product concerns map to `product-agent` and product service wrappers
- Sales order concerns map to `sales-order-agent` and sales-order service wrappers
- Purchase order concerns map to `purchase-order-agent` and purchase-order service wrappers
- Shared request context maps to OMS env/context, request builder, and OMS client
