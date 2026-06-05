# Phase 1 Agent Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refocus the OMS AI SKILLS workspace so Sales Order Agent becomes the only production-usable phase-1 implementation while Product Agent and Purchase Order Agent are reduced to accurate, explicit documentation artifacts with capability and release status tracking.

**Architecture:** Keep the existing shared OMS runtime/auth foundation, add explicit agent-definition and capability-status documentation, then discover and implement the Sales Order Agent as a multi-skill business agent that supports query, diagnosis, dependency checks, and safe execution. Product Agent and Purchase Order Agent remain documentation-defined agents that share the same publishing model, output standard, and status model without claiming implementation completeness.

**Tech Stack:** TypeScript, Node.js, Vitest, existing OMS staging runtime, markdown planning docs

---

## File structure

### Existing files to modify
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/agent-matrix.md` — replace module-level table with publishable agent definitions and phase-1 scope emphasis
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/capability-status.md` — replace vague status text with explicit capability matrices and release-readiness sections
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/api-scope.md` — narrow implementation API scope to Sales Order Agent and document discovery-only status for Product/PO
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/architecture.md` — rewrite architecture around shared foundation plus multi-skill agent publishing model
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/agent-interaction.md` — document how agent prompt, skills, and foundation cooperate
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/implementation-phases.md` — reorder work so Sales Order Agent implementation comes first and Product/PO stay documentation-only
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/testing-strategy.md` — focus validation on Sales Order Agent and documentation consistency for Product/PO
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/README.md` — make the top-level phase-1 scope match the redesigned plan
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/core/capabilities.ts` — replace legacy capability ownership list with Sales Order Agent-aligned capabilities only if still used by tests/runtime
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/reference/wave1-endpoints.ts` — replace old wave-1 endpoints with a sales-order-first reference slice only if still used by tests/runtime
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/reference/wave1-endpoints.test.ts` — align the reference test with the new sales-order-first scope

### Existing files to read during implementation
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/agents/base/agent-contract.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/agents/base/agent-registry.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/agents/router/intent-router.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/dispatch/dispatch-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/dispatch/dispatch-log-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/cli/dispatch-smoke-entrypoint.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/cli/dispatch-log-smoke-entrypoint.ts`
- `C:/Users/Jayne/Desktop/Skills/docs/oms-agent/oms-v3.openapi.json`
- `C:/Users/Jayne/Desktop/Skills/docs/oms-agent/07-测试环境配置.md`

### New files to create
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/sales-order-agent.md` — authoritative Sales Order Agent definition, skill list, action policy, output contract
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/product-agent.md` — Product Agent documentation-only definition and capability matrix
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/purchase-order-agent.md` — Purchase Order Agent documentation-only definition and capability matrix
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/foundation.md` — explicit description of the shared foundation (底座) and what is not a skill
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/release-readiness.md` — release-readiness format and current status for all three agents
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/sales-order-api-discovery.md` — discovered sales-order-adjacent APIs and dependency families for implementation
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/capability-status-doc.test.ts` — verifies status-level vocabulary and phase-1 focus in docs
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/agent-scope-doc.test.ts` — verifies Sales Order Agent is implementation-first and Product/PO are documentation-only

### Potential new implementation files after discovery
Only create these if the discovery task proves the endpoints exist and are phase-1 critical:
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/sales-order/sales-order-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/sales-order/allocation-rule-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/sales-order/item-master-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/sales-order/inventory-service.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/agents/sales-order/sales-order-agent.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/services/sales-order-service.test.ts`
- `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/agents/sales-order-agent.test.ts`

---

### Task 1: Rewrite phase-1 scope docs

**Files:**
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/README.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/agent-matrix.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/implementation-phases.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/architecture.md`
- Test: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/agent-scope-doc.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

const root = 'C:/Users/Jayne/Desktop/OMS AI SKILLS'

function read(relativePath: string) {
  return readFileSync(`${root}/${relativePath}`, 'utf8')
}

describe('phase-1 scope docs', () => {
  it('describe Sales Order Agent as the only implementation-first phase-1 agent', () => {
    const readme = read('README.md')
    const matrix = read('docs/agent-matrix.md')
    const phases = read('docs/implementation-phases.md')
    const architecture = read('docs/architecture.md')

    expect(readme).toContain('Sales Order Agent')
    expect(readme).toContain('Product Agent')
    expect(readme).toContain('Purchase Order Agent')

    expect(matrix).toContain('Sales Order Agent')
    expect(matrix).toContain('Product Agent')
    expect(matrix).toContain('Purchase Order Agent')
    expect(matrix).toContain('implementation-first')

    expect(phases).toContain('Sales Order Agent')
    expect(phases).toContain('documentation-only')

    expect(architecture).toContain('shared foundation')
    expect(architecture).toContain('multi-skill')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/agent-scope-doc.test.ts`
Expected: FAIL because the new doc test file does not exist yet and/or current docs do not contain the required phase-1 wording.

- [ ] **Step 3: Write minimal implementation**

Create `tests/unit/docs/agent-scope-doc.test.ts` with the test above.

Update `README.md` to this content:

```md
# OMS AI SKILLS

Standalone workspace for rebuilding OMS business agents and shared runtime from a clean architecture.

## Approved planning inputs
- `docs/oms-agent/oms-v3.openapi.json`
- `docs/oms-agent/OMS本体知识文件.json`
- `docs/oms-agent/07-测试环境配置.md`

## Phase 1 scope
- Shared OMS foundation
- Sales Order Agent as the implementation-first phase-1 deliverable
- Product Agent as a documentation-only phase-1 agent
- Purchase Order Agent as a documentation-only phase-1 agent
```

Update `docs/agent-matrix.md` to this content:

```md
# Agent Matrix

| Agent | Purpose | Publish Model | Phase 1 Status |
|---|---|---|---|
| Sales Order Agent | Query, diagnose, and act on sales orders | Multi-skill business agent | Implementation-first |
| Product Agent | Query, create, sync, and diagnose products | Multi-skill business agent | Documentation-only |
| Purchase Order Agent | Query, create, push, and diagnose purchase orders | Multi-skill business agent | Documentation-only |
```

Update `docs/implementation-phases.md` to this content:

```md
# Implementation Phases

## Phase 0
Bootstrap project structure and planning docs.

## Phase 1
Keep and harden the shared foundation:
- env
- OMS context
- token provider
- request builder
- OMS client
- shared result formatting and action policy

## Phase 2
Implement Sales Order Agent:
- sales-order API discovery
- sales-order service wrappers
- sales-order skills
- sales-order validation in staging

## Phase 3
Document Product Agent:
- agent definition
- skill inventory
- capability matrix
- release-readiness section

## Phase 4
Document Purchase Order Agent:
- agent definition
- skill inventory
- capability matrix
- release-readiness section
```

Update `docs/architecture.md` to this content:

```md
# Architecture

## Goal
Build a standalone OMS agent workspace where a shared foundation supports multiple publishable multi-skill agents, with Sales Order Agent as the only implementation-first phase-1 deliverable.

## Layers
1. Reference layer: approved OMS source artifacts only.
2. Foundation layer: auth, OMS client, request shaping, error normalization, output formatting, action policy.
3. Service layer: thin wrappers for business endpoint families.
4. Skill layer: focused business capabilities mounted under agents.
5. Agent layer: publishable business agents with prompts, descriptions, and output contracts.
6. Runner layer: local CLI entry and staging validation.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/agent-scope-doc.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add README.md docs/agent-matrix.md docs/implementation-phases.md docs/architecture.md tests/unit/docs/agent-scope-doc.test.ts
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "docs: refocus phase one on sales order agent"
```

### Task 2: Add explicit foundation and release-readiness docs

**Files:**
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/foundation.md`
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/release-readiness.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/agent-interaction.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/testing-strategy.md`
- Test: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/capability-status-doc.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

const root = 'C:/Users/Jayne/Desktop/OMS AI SKILLS'

function read(relativePath: string) {
  return readFileSync(`${root}/${relativePath}`, 'utf8')
}

describe('capability-status documentation', () => {
  it('uses explicit status levels and release-readiness sections', () => {
    const foundation = read('docs/foundation.md')
    const release = read('docs/release-readiness.md')
    const interaction = read('docs/agent-interaction.md')
    const testing = read('docs/testing-strategy.md')

    expect(foundation).toContain('not a separately published skill')
    expect(release).toContain('Planned')
    expect(release).toContain('Discovered')
    expect(release).toContain('Implemented')
    expect(release).toContain('Validated')
    expect(release).toContain('Production-ready')
    expect(release).toContain('Sales Order Agent')
    expect(release).toContain('Product Agent')
    expect(release).toContain('Purchase Order Agent')
    expect(interaction).toContain('agent prompt')
    expect(interaction).toContain('skill')
    expect(testing).toContain('Sales Order Agent')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/capability-status-doc.test.ts`
Expected: FAIL because the file and new docs do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `tests/unit/docs/capability-status-doc.test.ts` with the test above.

Create `docs/foundation.md`:

```md
# Foundation

The foundation (底座) is the shared OMS runtime and publishing-support layer used by every agent.

## What the foundation includes
- auth and user-context access
- tenant and merchant context
- OMS client and request shaping
- error normalization
- output formatting helpers
- action confirmation policy
- shared capability/release metadata support

## What the foundation is not
- not a separately published agent
- not a separately published skill
- not a user-facing business module
```

Create `docs/release-readiness.md`:

```md
# Release Readiness

## Status levels
- Planned
- Discovered
- Implemented
- Validated
- Production-ready

## Sales Order Agent
- Overall status: In development
- Target: Production-ready
- Scope: implementation-first

## Product Agent
- Overall status: Documentation-only
- Target: Planned
- Scope: no phase-1 implementation claim

## Purchase Order Agent
- Overall status: Documentation-only
- Target: Planned
- Scope: no phase-1 implementation claim
```

Update `docs/agent-interaction.md` to:

```md
# Agent Interaction

## Interaction model
1. The user talks to an agent.
2. The agent prompt decides which skill to use.
3. The selected skill uses the shared foundation and business services.
4. The agent returns a standardized business-facing result.

## Phase-1 focus
- Sales Order Agent uses multiple skills for query, diagnosis, dependency checks, and actions.
- Product Agent is documentation-defined only in phase 1.
- Purchase Order Agent is documentation-defined only in phase 1.
```

Update `docs/testing-strategy.md` to:

```md
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/capability-status-doc.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add docs/foundation.md docs/release-readiness.md docs/agent-interaction.md docs/testing-strategy.md tests/unit/docs/capability-status-doc.test.ts
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "docs: define shared foundation and release readiness"
```

### Task 3: Add agent-specific definition docs

**Files:**
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/sales-order-agent.md`
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/product-agent.md`
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/purchase-order-agent.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/capability-status.md`
- Test: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/agent-scope-doc.test.ts`

- [ ] **Step 1: Write the failing test**

Append this test to `tests/unit/docs/agent-scope-doc.test.ts`:

```ts
it('defines each agent with skills and output sections', () => {
  const sales = read('docs/sales-order-agent.md')
  const product = read('docs/product-agent.md')
  const purchase = read('docs/purchase-order-agent.md')
  const capability = read('docs/capability-status.md')

  expect(sales).toContain('sales-order-query')
  expect(sales).toContain('sales-order-reopen')
  expect(sales).toContain('Order Summary')
  expect(sales).toContain('Recommended Next Step')

  expect(product).toContain('product-query')
  expect(product).toContain('product-sync-channel')

  expect(purchase).toContain('purchase-order-query')
  expect(purchase).toContain('purchase-order-push-warehouse')

  expect(capability).toContain('Sales Order Agent')
  expect(capability).toContain('Product Agent')
  expect(capability).toContain('Purchase Order Agent')
  expect(capability).toContain('| Capability | Depends On | Status | Evidence | Gap | Target |')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/agent-scope-doc.test.ts`
Expected: FAIL because the agent definition docs and capability matrix do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `docs/sales-order-agent.md`:

```md
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
```

Create `docs/product-agent.md`:

```md
# Product Agent

## Purpose
A publishable multi-skill business agent for querying, creating, syncing, and diagnosing product workflows.

## Mounted skills
- `product-query`
- `product-create`
- `product-sync-channel`
- `product-diagnosis`

## Phase 1 note
Documentation-only in phase 1.
```

Create `docs/purchase-order-agent.md`:

```md
# Purchase Order Agent

## Purpose
A publishable multi-skill business agent for querying, creating, pushing, and diagnosing purchase-order workflows.

## Mounted skills
- `purchase-order-query`
- `purchase-order-create`
- `purchase-order-push-warehouse`
- `purchase-order-diagnosis`

## Phase 1 note
Documentation-only in phase 1.
```

Replace `docs/capability-status.md` with:

```md
# Capability Status

## Sales Order Agent
| Capability | Depends On | Status | Evidence | Gap | Target |
|---|---|---|---|---|---|
| Query sales orders | Sales-order API family | Planned | Phase-1 redesign approved | API discovery not completed | Discovered |
| Diagnose status and blockers | Order detail + analysis rules | Planned | Output contract defined | Analysis logic not implemented | Implemented |
| Reopen sales order | Reopen action API | Planned | Action included in scope | Eligibility rules not discovered | Validated |
| Manual allocation | Allocation API + dependency checks | Planned | Action included in scope | Rule/item/inventory discovery not completed | Validated |

## Product Agent
| Capability | Depends On | Status | Evidence | Gap | Target |
|---|---|---|---|---|---|
| Query products | Product API family | Planned | Agent doc written | API discovery not completed | Discovered |
| Create products | Product create API | Planned | Agent doc written | API discovery not completed | Discovered |
| Sync to channel product | Sync API family | Planned | Agent doc written | API discovery not completed | Discovered |

## Purchase Order Agent
| Capability | Depends On | Status | Evidence | Gap | Target |
|---|---|---|---|---|---|
| Query purchase orders | Purchase-order API family | Planned | Agent doc written | API discovery not completed | Discovered |
| Create purchase orders | PO create API | Planned | Agent doc written | API discovery not completed | Discovered |
| Push purchase orders to warehouse | Warehouse push API family | Planned | Agent doc written | API discovery not completed | Discovered |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/agent-scope-doc.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add docs/sales-order-agent.md docs/product-agent.md docs/purchase-order-agent.md docs/capability-status.md tests/unit/docs/agent-scope-doc.test.ts
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "docs: add agent definitions and capability matrices"
```

### Task 4: Discover sales-order-adjacent APIs needed for real implementation

**Files:**
- Create: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/sales-order-api-discovery.md`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/docs/api-scope.md`
- Test: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/docs/capability-status-doc.test.ts`

- [ ] **Step 1: Write the failing test**

Append this test to `tests/unit/docs/capability-status-doc.test.ts`:

```ts
it('documents the discovery requirement for sales-order dependencies', () => {
  const apiScope = read('docs/api-scope.md')
  const discovery = read('docs/sales-order-api-discovery.md')

  expect(apiScope).toContain('Sales Order Agent implementation scope')
  expect(apiScope).toContain('allocation rules')
  expect(apiScope).toContain('item master')
  expect(apiScope).toContain('inventory')

  expect(discovery).toContain('sales-order-query')
  expect(discovery).toContain('sales-order-reopen')
  expect(discovery).toContain('sales-order-manual-allocation')
  expect(discovery).toContain('allocation-rule-evaluator')
  expect(discovery).toContain('item-master-query')
  expect(discovery).toContain('inventory-query')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/capability-status-doc.test.ts`
Expected: FAIL because the discovery doc does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `docs/sales-order-api-discovery.md`:

```md
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

## Discovery rules
- Only endpoints proven in the approved OMS source inputs are allowed into implementation scope.
- Do not carry forward shipping or mapping workflows.
- Record endpoint path, request shape, response shape, and why the endpoint is needed.
```

Replace `docs/api-scope.md` with:

```md
# API Scope

## Phase 1 shared foundation endpoints
- `POST /iam/token`
- `GET /iam/user-info`

## Sales Order Agent implementation scope
- sales-order list/detail endpoint family
- reopen action endpoint family
- manual allocation endpoint family
- allocation rules endpoint family
- item master endpoint family
- inventory endpoint family

## Product Agent documentation-only scope
- product endpoint discovery only

## Purchase Order Agent documentation-only scope
- purchase-order endpoint discovery only
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/docs/capability-status-doc.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add docs/sales-order-api-discovery.md docs/api-scope.md tests/unit/docs/capability-status-doc.test.ts
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "docs: define sales order api discovery scope"
```

### Task 5: Align runtime reference artifacts with the new scope

**Files:**
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/core/capabilities.ts`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/reference/wave1-endpoints.ts`
- Modify: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/reference/wave1-endpoints.test.ts`
- Test: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/reference/wave1-endpoints.test.ts`

- [ ] **Step 1: Write the failing test**

Replace `tests/unit/reference/wave1-endpoints.test.ts` with:

```ts
import { describe, expect, it } from 'vitest'
import { WAVE1_ENDPOINTS } from '../../../src/reference/wave1-endpoints'
import { CAPABILITY_ENDPOINTS } from '../../../src/core/capabilities'

describe('wave1 endpoints', () => {
  it('tracks only shared auth plus sales-order-first implementation scope', () => {
    expect(WAVE1_ENDPOINTS).toEqual([
      'POST /iam/token',
      'GET /iam/user-info',
      'sales-order list/detail endpoint family',
      'reopen action endpoint family',
      'manual allocation endpoint family',
      'allocation rules endpoint family',
      'item master endpoint family',
      'inventory endpoint family'
    ])

    expect(CAPABILITY_ENDPOINTS['sales-order']).toEqual([
      'sales-order-query',
      'sales-order-status-analysis',
      'allocation-rule-evaluator',
      'item-master-query',
      'inventory-query',
      'sales-order-reopen',
      'sales-order-manual-allocation',
      'sales-order-action-recommender'
    ])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/reference/wave1-endpoints.test.ts`
Expected: FAIL because the current endpoint and capability references still reflect the previous scope.

- [ ] **Step 3: Write minimal implementation**

Replace `src/reference/wave1-endpoints.ts` with:

```ts
export const WAVE1_ENDPOINTS = [
  'POST /iam/token',
  'GET /iam/user-info',
  'sales-order list/detail endpoint family',
  'reopen action endpoint family',
  'manual allocation endpoint family',
  'allocation rules endpoint family',
  'item master endpoint family',
  'inventory endpoint family'
] as const
```

Replace `src/core/capabilities.ts` with:

```ts
export const CAPABILITY_ENDPOINTS = {
  'sales-order': [
    'sales-order-query',
    'sales-order-status-analysis',
    'allocation-rule-evaluator',
    'item-master-query',
    'inventory-query',
    'sales-order-reopen',
    'sales-order-manual-allocation',
    'sales-order-action-recommender'
  ],
  product: [
    'product-query',
    'product-create',
    'product-sync-channel',
    'product-diagnosis'
  ],
  'purchase-order': [
    'purchase-order-query',
    'purchase-order-create',
    'purchase-order-push-warehouse',
    'purchase-order-diagnosis'
  ]
} as const
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "C:/Users/Jayne/Desktop/OMS AI SKILLS" run test:unit -- tests/unit/reference/wave1-endpoints.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add src/core/capabilities.ts src/reference/wave1-endpoints.ts tests/unit/reference/wave1-endpoints.test.ts
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "refactor: align capability references to sales order scope"
```

### Task 6: Implement sales-order discovery support in code

**Files:**
- Read/Modify depending on findings: `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/dispatch/dispatch-service.ts`
- Create if APIs are confirmed: `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/services/sales-order/sales-order-service.ts`
- Create if APIs are confirmed: `C:/Users/Jayne/Desktop/OMS AI SKILLS/src/agents/sales-order/sales-order-agent.ts`
- Create if APIs are confirmed: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/services/sales-order-service.test.ts`
- Create if APIs are confirmed: `C:/Users/Jayne/Desktop/OMS AI SKILLS/tests/unit/agents/sales-order-agent.test.ts`

- [ ] **Step 1: Write the failing test**

After discovery confirms exact APIs, write focused tests that encode the first real skill boundary. For example, if the list/detail API is confirmed, create:

```ts
import { describe, expect, it } from 'vitest'
import { createSalesOrderService } from '../../../src/services/sales-order/sales-order-service'

describe('createSalesOrderService', () => {
  it('queries sales order detail through the confirmed OMS path', async () => {
    let captured: { path?: string; query?: unknown } = {}

    const service = createSalesOrderService({
      get: async (path, query) => {
        captured = { path, query }
        return { data: { orderNo: 'SO-1' } }
      },
      post: async () => ({})
    })

    await service.getSalesOrderDetail({ orderNo: 'SO-1' })

    expect(captured).toEqual({
      path: '/CONFIRMED/PATH/HERE',
      query: { orderNo: 'SO-1' }
    })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run the single new test file.
Expected: FAIL because the service does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement only the smallest confirmed service/agent surface discovered in `docs/sales-order-api-discovery.md`. Do not create speculative methods. Keep one service method and one agent path at first.

- [ ] **Step 4: Run test to verify it passes**

Run the focused service/agent tests and the relevant existing unit tests.
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" add src/services/sales-order src/agents/sales-order tests/unit/services/sales-order-service.test.ts tests/unit/agents/sales-order-agent.test.ts docs/sales-order-api-discovery.md
git -C "C:/Users/Jayne/Desktop/OMS AI SKILLS" commit -m "feat: start sales order agent implementation"
```

---

## Self-review
- Spec coverage: the plan covers shared foundation docs, publishable agent definitions, capability/release status visibility, sales-order-first API discovery, and the first real Sales Order Agent implementation slice.
- Placeholder scan: the only intentionally open area is Task 6, where the exact endpoint path depends on discovery. This is allowed because the plan explicitly makes discovery the prerequisite and instructs the implementer to write the failing test only after confirming exact APIs.
- Type consistency: `sales-order-query`, `sales-order-status-analysis`, `allocation-rule-evaluator`, `item-master-query`, `inventory-query`, `sales-order-reopen`, `sales-order-manual-allocation`, and `sales-order-action-recommender` are used consistently across docs, capability references, and planned implementation.
