# Sales Order Agent / Skill Output Design

## Goal

Redefine the sales-order agent and skill output requirements so replies are optimized for business operations users. The agent must not merely surface OMS/WMS fields. It must convert real evidence into business-ready conclusions.

The guiding rule is:

> Users make decisions, not inferences. The agent must tell them the result, the reason, the solution, and the next step.

## Target User

Default audience: business operations users.

Implications:
- Prefer business language over technical fields.
- Show only a small set of identifying fields.
- Do not require users to understand OMS/WMS internals.
- Do not force users to infer meaning from statuses, booleans, or raw payloads.

## Output Objective

Every order-related reply should minimize user thinking effort.

Unless the user explicitly asks for technical details, the agent should:
1. State the business result first.
2. Explain the reason in business language.
3. Give a concrete solution or recommended path.
4. Tell the user the next step.

## Default Output Structure

Standard structure:
1. Result
2. Reason
3. Solution
4. Next step

Allowed simplifications:
- Success replies may use: Result → Explanation → Next step.
- High-risk confirmation replies may use: Risk → Confirmation details → Exact confirmation phrase.
- Async replies may use: Submitted state → What is still unknown → Recheck step.

## Evidence-First Rule

The agent must prefer real evidence over inference.

Evidence sources include:
- OMS detail API fields such as diagnosis, availableActions, recommendedNextStep, inventorySummary.
- Dispatch records.
- Allocation item details.
- Route/routing evidence.
- Sales-order warehouse assignment or split logs.
- Confirmed API response semantics.

If evidence is missing, the agent must say what is confirmed and what is not yet confirmed. It must not convert a guess into a fact.

## Sales Order Warehouse Assignment Rules

This is a high-priority scenario.

When a user asks where a sales order was assigned and why, the agent must try to answer:
1. Which warehouse the order was assigned to.
2. Whether it was system-assigned or user-directed.
3. Why this warehouse was chosen.
4. Whether the user needs to intervene.

### Hard rule

The reason for sales-order warehouse assignment must come from real evidence, not agent inference.

Preferred evidence order:
1. Split/assignment success logs.
2. Dispatch records.
3. Route/routing evidence.
4. Order-detail evidence that explicitly supports the conclusion.

### Prohibited behavior

The agent must not explain why a sales order went to a warehouse based only on:
- warehouseName
- accountingCode
- ALLOCATED / WAREHOUSE_PROCESSING / similar statuses
- general heuristics

Those fields prove outcome, not cause.

### No-evidence fallback

If the agent can confirm the warehouse result but not the reason, it must say so clearly and offer to check the underlying logs.

## EXCEPTION Order Rules

EXCEPTION orders must always include both cause and solution.

The agent must not stop at "this order is in EXCEPTION".

It must answer:
1. What the exception is.
2. Why it happened.
3. What solution or action the system suggests.
4. What should happen next.

### Cause/source rule

Cause and solution must primarily come from real API/detail evidence such as:
- diagnosis
- availableActions
- recommendedNextStep
- inventorySummary
- explicit detail errors
- related dispatch/log evidence

### Prohibited behavior

Do not output only a status.
Do not say "please check" without extracting the actual cause or available handling path when the interface already contains it.
Do not speculate about inventory, routing, or warehouse causes if the interface provides a different explicit explanation.

## ON_HOLD Rules

For ON_HOLD orders, the agent must separate:
1. hold-state problems
2. allocation/inventory problems

Required flow:
1. Confirm hold status.
2. Attempt release when appropriate.
3. If release fails, inspect allocation state.
4. Tell the user whether the blocker is still hold-related or allocation-related.

If all items are already fully allocated, the agent must explicitly tell the user that manual allocation is not the next step and that the current blocker is the hold itself.

## Replenishment / Purchase Order Recommendation Rules

When recommending a replenishment warehouse, the agent must tell the user:
1. Which warehouse is recommended.
2. Why that warehouse is recommended.
3. Whether there are alternatives.
4. Whether the user needs to confirm before proceeding.

The reason must come from evidence such as:
- available warehouse results
- routing-rule context
- fulfillment/WMS availability
- rank/priority
- user-specified constraints

The agent must not recommend a warehouse with an unexplained "best guess" statement.

## Success Reply Rules

For successful actions, the agent must not stop at success.

It must explain what the success means in business terms. Examples:
- order created successfully → whether it has already entered warehouse processing
- purchase order created successfully → whether it has already been dispatched to warehouse handling
- hold released successfully → whether the order has re-entered allocation or fulfillment flow

## High-Risk Operation Rules

Applies to:
- cancel
- reopen
- batch release hold / batch reopen
- force allocate
- other irreversible or high-impact writes

Default rule: do not execute before confirmation.

The confirmation prompt must clearly state:
- environment
- operation
- target object(s)
- risk
- exact confirmation phrase

## Async Result Rules

If an interface returns a submitted-but-not-final state, the agent must clearly distinguish:
1. interface call accepted
2. business state actually changed

The agent must never describe an accepted request as a completed business result.

Examples:
- cancel ongoing → submitted, still processing
- reopen called but status unchanged → call made, effect not yet confirmed

## List Query Rules

For EXCEPTION / ON_HOLD / queue-like list queries, the agent must not simply dump IDs.

It should tell the user:
- what category was queried
- what the list implies
- what the recommended next narrowing or follow-up step is

Default output should show representative items only, unless the user asks for full lists.

## Field Visibility Rules

### Default fields to keep
- order number
- purchase order number
- sku / quantity
- warehouse
- current business-readable status
- environment

### Default fields to hide
- raw booleans like data=true/false
- successRespDTOS / failRespDTOS / ongoingRespDTOS
- raw dispatch remarks
- raw routing structures
- large JSON payloads
- low-level field dumps

Technical evidence can be shown only when:
1. user explicitly asks for it
2. evidence is needed to justify a conclusion
3. the agent must explain why it cannot conclude more

Even then, business conclusion must come first.

## Status Translation Rules

Statuses must be translated into business language for default output.

Examples:
- ALLOCATED → entered allocation stage
- WAREHOUSE_PROCESSING → entered warehouse processing flow
- DISPATCHED → submitted to warehouse handling
- EXCEPTION → still blocked in an exception state
- ON_HOLD → currently held and cannot continue normal flow
- ongoing → request accepted and still processing

## Required Templates

### Success
Result
- key identifiers
- business-readable current state
Explanation
Next step

### Blocked
What cannot proceed
Reason
Solution
Next step

### Choice required
What needs confirmation
Options
Recommendation with evidence-based reason
Exact reply instruction

### High-risk confirmation
Risk warning
Environment / action / targets
Exact confirmation phrase

### Async
What has been submitted
What is still not confirmed
Why it cannot yet be called successful
Recheck step

## Absolute Prohibitions

The agent must not:
1. report statuses without business conclusions
2. report results without reasons
3. report reasons without a handling path
4. force users to infer next steps from fields
5. present guesses as facts
6. infer warehouse assignment cause from end-state fields alone
7. present asynchronous acceptance as business completion
8. dump technical payloads by default
9. leave EXCEPTION orders without cause and solution
10. leave users to think through next steps themselves

## Suggested Eval Criteria

All user-facing output checks should include:
- conclusion comes first
- business language is used
- reason is explicitly stated
- solution is explicitly stated when applicable
- next step is explicit
- user does not need to infer meaning from raw fields

Warehouse-assignment-specific checks:
- warehouse result stated
- warehouse reason stated
- reason backed by logs/dispatch/route evidence
- intervention need stated

EXCEPTION-specific checks:
- explicit cause
- explicit solution
- cause and solution grounded in real interface returns

Async-specific checks:
- submitted vs completed distinction made
- no false success language

## Summary Rule

> The sales-order agent must use real evidence to directly tell business operations users the result, the reason, the solution, and the next step. It must not leave status interpretation, warehouse attribution, or exception handling logic for the user to infer.