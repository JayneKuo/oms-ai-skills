---
name: hold
description: Diagnose and manage OMS sales-order ON_HOLD workflows. Use when the user asks why an order is on hold, which hold rule may have matched, what hold rules exist, which orders are affected by rules, whether a hold can be released, or asks to draft/create a hold rule from natural language.
---

# Hold Skill

## Runtime Guardrails

- Use this skill for ON_HOLD diagnosis, hold-rule lookup, rule-to-order evidence, release-hold assessment, and hold-rule draft/create workflows.
- Read-only hold diagnosis/rule lookup may run directly. Dry-run/draft rule generation may run directly. Real release hold and real hold-rule create/enable/update must require user second confirmation before execution.
- Every answer must separate confirmed evidence from inferred candidates.
- Never guess hold reasons. Prefer order detail, ORDER_HOLD_OR rule execution, matched rules/actions/logs, order event logs, hold records, and rule active-count.
- If direct rule/log evidence is unavailable, say the order is confirmed ON_HOLD but exact rule causality is not confirmed.
- Candidate matching from order fields and rule config is allowed, but it must be labeled as candidate/historical, not direct causality.
- Do not submit release hold when latest detail status is not `ON_HOLD`; report `not_submitted` and explain there is no active hold.
- A release can be called successful only when OMS returns `code=0,data=true` and the post-check status is no longer `ON_HOLD`.
- Rule creation defaults to dry-run. Only submit with `--confirm-create` after the user has reviewed rule name, status, scope, priority, and risk.
- Warn before creating an ENABLED rule because it may immediately hold matching future orders.

## Core Workflows

### Diagnose An Order

Default script:

```bash
python scripts/diagnose_hold.py --order SO00361770
python scripts/diagnose_hold.py --order SO00361770 --release
python scripts/diagnose_hold.py --orders SO001 SO002
```

Required output:

1. Current status: whether the order is actually `ON_HOLD`.
2. Evidence: matched rule/log if available; otherwise state evidence gap.
3. Blocker: hold blocker versus allocation/remaining blocker.
4. Action: release, review, rule investigation, or handoff.
5. Post-check: if a release was executed, re-read status before claiming success.

### Query Hold Rules

Use `hold_rules.py`:

```bash
python scripts/hold_rules.py --action list
python scripts/hold_rules.py --action list --status ENABLED
python scripts/hold_rules.py --action get --id 2062019635310088193
python scripts/hold_rules.py --action active-count --id 2062019635310088193
```

User-facing output should summarize:

- Rule name, status, hold mode, priority.
- Main scope such as SKU, channel, order source, risk level, warehouse, or date range.
- Active hold count when the user asks "how many orders are affected".
- Any evidence boundary, for example "active-count gives count by rule, not the full order list".

### Find Orders Affected By Rules

Use `match_hold_rules_to_orders.py`:

```bash
python scripts/match_hold_rules_to_orders.py --size 20
python scripts/match_hold_rules_to_orders.py --orders SO01376525 SO01376524
```

Important boundary:

- The available OpenAPI exposes active-count by rule but not a direct hold-record list endpoint.
- This script maps orders to candidate rules by matching order fields against rule config.
- Return `active_rule_candidate` when the rule is currently enabled.
- Return `disabled_or_historical_rule_candidate` when the current rule is disabled and can only explain historical holds if it was enabled when the order was held.
- Do not say "this order was definitely held by rule X" unless a direct hold execution log, hold record, or order event proves it.

### Draft Or Create Hold Rules From Natural Language

Use `hold_rules.py`:

```bash
python scripts/hold_rules.py --action draft --text "创建一个hold规则 name: Imported hold，hold imported orders permanently priority 55 disabled"
python scripts/hold_rules.py --action create --text "创建一个hold规则 name: Imported hold，hold imported orders permanently priority 55 disabled"
python scripts/hold_rules.py --action create --text "..." --confirm-create
```

Behavior:

- `draft` never submits to OMS.
- `create` without `--confirm-create` is still dry-run.
- `create --confirm-create` submits to `/api/linker-oms/opc/app-api/hold-rule-data/create`.
- Natural language can infer rule name, enabled/disabled status, hold mode, priority, SKUs, order source, risk levels, and hold duration when present.
- If the natural language is ambiguous, produce a draft and ask for the missing fields instead of guessing.

## Script Inventory

```bash
python scripts/get_order_detail.py --order SO00361770
python scripts/get_hold_reason.py --order SO00361770
python scripts/release_hold.py --order SO00361770
python scripts/get_allocation_items.py --order SO00361770
python scripts/diagnose_hold.py --order SO00361770
python scripts/hold_rules.py --action list
python scripts/hold_rules.py --action get --id RULE_ID
python scripts/hold_rules.py --action active-count --id RULE_ID
python scripts/hold_rules.py --action draft --text "..."
python scripts/hold_rules.py --action create --text "..."
python scripts/match_hold_rules_to_orders.py --orders SO001 SO002
python scripts/match_hold_rules_to_orders.py --size 20
```

## User Reply Shape

```text
Result: [current hold/rule/action result]
Reason: [confirmed evidence, or candidate evidence with boundary]
Solution: [release/review/create rule/adjust rule/handoff]
Next step: [exact action or confirmation needed]
```

For release or hold-rule write requests before execution, reply first:

```text
This is a real OMS hold action, so I will not execute it yet.
Environment: [staging/production]
Operation: [release hold / create hold rule / enable rule / update rule]
Targets: [order no or rule name/id and scope]
Risk: [orders may leave hold, or future matching orders may be held automatically]
To proceed, reply exactly: [confirmation phrase]
```

## Forbidden

- Do not provide raw credentials, tokens, or full raw payloads by default.
- Do not claim exact rule causality from candidate matching alone.
- Do not release a non-ON_HOLD order.
- Do not treat `data=false` as release success.
- Do not create an enabled rule without user second confirmation.
- Do not use allocation scripts to perform hold-rule management.
