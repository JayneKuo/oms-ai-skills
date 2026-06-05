# Phase 1 Agent Redesign Design

## Goal
Refocus phase 1 so the only implementation-grade deliverable is a production-usable Sales Order Agent, while Product Agent and Purchase Order Agent are defined completely at the documentation level with explicit capability matrices, release-readiness rules, and shared runtime dependencies.

## Scope
### In scope for implementation
- Shared OMS runtime/auth foundation reused by all agents
- Sales Order Agent architecture, skills, output contract, capability matrix, release-readiness rules
- Sales-order-first implementation sequencing
- Product Agent documentation
- Purchase Order Agent documentation

### Out of scope for phase 1 implementation
- Shipping/mapping workflows
- Dispatch-log as a standalone agent/module
- Shipment/routing families
- Full Product Agent execution chain
- Full Purchase Order Agent execution chain

## Publishing model
The release target is an agent website where:
- one agent can mount multiple skills
- all three business agents share one OMS runtime foundation
- users interact with agents, not raw services or runtime pieces

## Shared foundation (底座)
The shared foundation is not a separately published agent or skill. It is a common runtime and policy layer used by every agent skill.

### Foundation responsibilities
1. Auth and context
   - acquire token
   - reuse tenant/merchant/user context
   - normalize user-info access
2. OMS request layer
   - shared OMS client
   - standard headers and payload shaping
   - response normalization
   - error translation
3. Analysis support
   - status explanation helpers
   - dependency-check result shapes
   - recommendation/result formatting
4. Publishing support
   - agent metadata model
   - skill metadata model
   - capability status model
   - release-readiness model
   - confirmation-required action policy

## Agent lineup
### 1. Sales Order Agent
Phase-1 primary deliverable. This agent must be independently publishable and usable by end users.

#### Purpose
Help users inspect sales orders, understand state and exceptions, evaluate dependencies for next actions, and execute reopen or manual allocation safely.

#### Mounted skills
- `sales-order-query`
- `sales-order-status-analysis`
- `allocation-rule-evaluator`
- `item-master-query`
- `inventory-query`
- `sales-order-reopen`
- `sales-order-manual-allocation`
- `sales-order-action-recommender`

#### Capability groups
##### Query
- query sales order list
- query sales order detail
- query line items
- query current status
- query related allocation/fulfillment information
- query allocation rules
- query item master data
- query inventory

##### Analysis
- explain current order state
- detect whether the order is abnormal
- identify likely root cause
- determine whether reopen is allowed
- determine whether manual allocation is allowed
- determine whether allocation blockers come from rules, item master, or inventory
- recommend next action and sequence

##### Actions
- reopen sales order
- manually allocate sales order

#### Action policy
- queries and analysis run without confirmation
- `reopen` requires confirmation
- `manual allocation` requires confirmation

#### Output standard
Every final Sales Order Agent response must contain:
1. `Order Summary`
2. `Diagnosis`
3. `Dependency Check`
4. `Available Actions`
5. `Recommended Next Step`
6. `Execution Result` (only when an action was run)

#### Phase-1 success criteria
The agent is not considered phase-1 complete unless a user can:
- inspect a target order
- understand current status and abnormal reason
- see rule/item-master/inventory dependency checks
- receive a recommendation
- execute reopen when eligible
- execute manual allocation when eligible
- receive a structured business-facing result instead of raw JSON

### 2. Product Agent
Documentation-only in phase 1.

#### Purpose
Query products, create products, sync products to channel product, and explain sync/publish blockers.

#### Mounted skills
- `product-query`
- `product-create`
- `product-sync-channel`
- `product-diagnosis`

#### Capability groups
##### Query
- query product list
- query product detail
- query product status
- query channel-product linkage
- query sync/publish result

##### Actions
- create product
- update key product attributes
- sync to channel product
- retry sync

##### Analysis
- explain sync failure
- explain missing required data
- explain channel-specific blocking factors
- recommend next step

#### Output standard
1. `Product Summary`
2. `Current Status`
3. `Sync / Publish Diagnosis`
4. `Blocking Factors`
5. `Available Actions`
6. `Recommended Next Step`
7. `Execution Result`

### 3. Purchase Order Agent
Documentation-only in phase 1.

#### Purpose
Query purchase orders, create purchase orders, push them to warehouses, and explain push failures or workflow blockers.

#### Mounted skills
- `purchase-order-query`
- `purchase-order-create`
- `purchase-order-push-warehouse`
- `purchase-order-diagnosis`

#### Capability groups
##### Query
- query PO list
- query PO detail
- query PO status
- query PO lines
- query warehouse-push status

##### Actions
- create PO
- push PO to warehouse
- retry warehouse push

##### Analysis
- explain push failure
- explain missing prerequisites
- explain current workflow blockers
- recommend next step

#### Output standard
1. `PO Summary`
2. `Current Status`
3. `Warehouse Push Diagnosis`
4. `Blocking Factors`
5. `Available Actions`
6. `Recommended Next Step`
7. `Execution Result`

## Capability-status model
Every agent capability must be tracked using the same explicit levels:
- `Planned`
- `Discovered`
- `Implemented`
- `Validated`
- `Production-ready`

Each capability row must also record:
- dependency surface
- evidence
- current gap
- target next state

## Release-readiness model
Each agent must have a release summary containing:
- current overall status (`In development`, `Release candidate`, `Production-ready`)
- usable user scenarios
- unsupported scenarios
- known risks
- confirmation-required actions

## Recommended implementation order
1. Keep and extend shared runtime foundation
2. Replace vague phase-1 planning docs with agent-definition and capability-status docs
3. Discover the exact sales-order-related APIs needed for query, analysis inputs, reopen, manual allocation, rule lookup, item master lookup, and inventory lookup
4. Implement Sales Order Agent skill-by-skill with TDD
5. Validate Sales Order Agent against staging
6. Leave Product/Purchase Order at complete design-doc status plus capability matrices

## Risks
- sales-order dependencies may span multiple endpoint families, not only sales-order endpoints
- reopen/manual allocation may require stricter confirmation and eligibility checks than initial planning assumed
- item master or inventory data may live outside the most obvious endpoint family and must be discovered before promising implementation

## Final design decision
Phase 1 is successful only if the published scope is unmistakable:
- Sales Order Agent is the only implementation-first deliverable
- Product Agent and Purchase Order Agent are documentation-complete but not sold as fully usable business agents yet
- every agent has visible capability and release status so progress cannot become ambiguous again
