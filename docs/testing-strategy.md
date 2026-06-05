# Testing Strategy

## Environment
- Use staging only.
- OMS base URL: `https://omsv2-staging.item.com`
- IAM base URL: `https://id-staging.item.com`
- Tenant: `LT`
- Merchant: `LAN0000002`

## Test layers
1. Unit tests for shared foundation and Sales Order Agent skills.
2. Narrow contract tests against selected sales-order-related OpenAPI slices.
3. Manual staging validation for Sales Order Agent.
4. Documentation-consistency tests for Product Agent and Purchase Order Agent.
