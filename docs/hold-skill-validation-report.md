# Hold Skill Validation Report

Validation date: 2026-06-04

Scope: `skills/hold` only.

## Real Staging Cases

| Order | Scenario | Result |
| --- | --- | --- |
| `SO01376525` | Active ON_HOLD diagnosis | Confirmed latest status `ON_HOLD`; `ORDER_HOLD_OR` endpoint returned 404, so direct hold execution reason is unconfirmed; SKU `ccc` remaining `1`. |
| `SO01376524` | Real release hold | Release returned `code=0,data=true`; post-check status became `ALLOCATED`; release confirmed. |
| `SO01392133` | Non-hold release boundary | Latest status `WAREHOUSE_PROCESSING`; `diagnose_hold.py --release` did not submit release and returned `not_submitted`. |
| `SO00000000` | Missing order boundary | Returned not found/inaccessible; no hold diagnosis guessed. |

## Hold Rule Management Validation

| Scenario | Real result |
| --- | --- |
| List hold rules | `hold_rules.py --action list --size 10` returned 4 staging rules. |
| Inspect enabled rule | Rule `2062019635310088193` is `AI test`, status `ENABLED`, hold mode `PERMANENT`, priority `55`, order source `IMPORTED`. |
| Active count by rule | `hold_rules.py --action active-count --id 2062019635310088193` returned `0`. |
| Natural-language draft | Text `创建一个hold规则 name: AI imported hold，hold imported orders permanently priority 55 disabled` produced a disabled permanent imported-order rule draft and did not submit to OMS. |
| Natural-language create without confirmation | `hold_rules.py --action create ...` returned `state=dry_run`, `submittedToOms=false`; no rule was created. |
| Match explicit orders to rules | `match_hold_rules_to_orders.py --orders SO01376525 SO01376524` returned candidate/historical matches. `SO01376525` is `ON_HOLD` and SKU `CCC` matched disabled/historical rule `ccc3の2`; exact causality remains unconfirmed without direct execution logs. |
| Match ON_HOLD page to rules | `match_hold_rules_to_orders.py --size 5` found 5 ON_HOLD orders with historical candidate rules, but no active-rule candidates. |

## Fixes Applied

- Added `skills/hold/scripts/diagnose_hold.py`.
- Added `skills/hold/scripts/hold_rules.py` for rule list/get/active-count/draft/create.
- Added `skills/hold/scripts/match_hold_rules_to_orders.py` for bounded rule-to-order candidate matching.
- Release now has a safe wrapper with detail precheck, hold-rule evidence lookup, allocation remaining check, optional release, and post-release detail check.
- Non-ON_HOLD orders are blocked before release submission.
- Release success requires `code=0,data=true` and post-check status not `ON_HOLD`.
- Prompt/docs now require evidence boundaries and no guessing when `ORDER_HOLD_OR` or direct hold records are unavailable.
- Rule creation defaults to dry-run and requires `--confirm-create` for submission.

## Ability Boundary

Hold can independently complete:

- Confirm active ON_HOLD status.
- Explain when hold reason is unconfirmed due to missing rule/log evidence.
- Distinguish hold blockers from allocation blockers through remaining quantity.
- Release hold after user second confirmation and verify latest status.
- Batch diagnose mixed hold/non-hold/not-found orders with bounded concurrency.
- Query hold rules and inspect a rule by id.
- Query active hold count for a rule.
- Draft hold rules from natural language.
- Create hold rules only after user second confirmation.
- Map ON_HOLD orders to candidate active or historical rules using rule config and order fields.

Hold must not:

- Guess payment/fraud/manual-hold reasons without rule/log evidence.
- Treat `code=0,data=false` as release success.
- Submit release for non-ON_HOLD latest statuses.
- Diagnose allocation cause; hand off allocation-specific questions to `allocation`.
- Claim exact rule causality from candidate matching alone.
- Create enabled hold rules without explicit user confirmation.

## User-Facing Example

```text
订单 SO01376525 当前确实是 ON_HOLD。规则配置匹配上看，它的 SKU `CCC` 与历史候选规则 `ccc3の2` 命中，但该规则当前是 DISABLED，所以这只能解释为候选/历史线索，不能直接证明就是这条规则把订单 hold 住。当前 staging 没有暴露可用的 hold record/list 接口，ORDER_HOLD_OR 也返回 404，因此精确原因还需要订单事件日志或 hold 执行日志确认。
```
