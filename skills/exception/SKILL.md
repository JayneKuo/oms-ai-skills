---
name: exception
description: 诊断 OMS 销售订单 EXCEPTION 状态。用户问异常原因、为什么卡住、怎么解决、哪些异常订单需要处理时使用。必须给出原因、解决方案和下一步。
---

# Exception Skill

## Runtime Guardrails

- Use this skill when the user asks why a sales order is in EXCEPTION, how to resolve it, or which exception orders need action.
- Always explain cause, solution, and next step. Never answer with only "the order is EXCEPTION".
- Base causes on real evidence: order detail, diagnosis fields, available actions, recommended next step, inventory summary, allocation evidence, dispatch logs, or explicit API errors.
- If evidence is missing, say what is confirmed and what is still unconfirmed. Do not invent inventory, routing, warehouse, or rule causes.
- Do not execute reopen, cancel, manual allocation, or replenishment creation here. Route confirmed actions to `operations`, `allocation`, or `replenishment`.
- Prefer `diagnose_exception.py` over raw `query_orders.py` / `get_order_detail.py` when the user asks for cause, solution, or a batch action list.
- EXCEPTION list rows can be stale. Always verify current detail status before recommending reopen, allocation, or replenishment.
- If `reserve1` or another detail field explicitly says a product is out of stock, treat that as confirmed cause and route next step to `replenishment`; reopen should happen only after inventory/replenishment is handled and the business confirms retry.
- If detail status is no longer `EXCEPTION`, tell the user it moved out of exception and do not recommend exception actions.

## User Reply Shape

1. Result: the order is exceptional and whether the cause is confirmed.
2. Reason: evidence-backed cause, or a clear "not enough evidence yet".
3. Solution: recommended business action.
4. Next step: what the user should confirm or which skill/action should continue.

负责销售订单 EXCEPTION 诊断。

## 能力范围

- 查询 EXCEPTION 订单
- 查询订单详情
- 从真实返回中提取异常原因
- 判断是否需要补货、分仓、reopen 或人工处理
- 输出解决方案和下一步

## 证据规则

优先使用真实接口返回：

- `diagnosis`
- `availableActions`
- `recommendedNextStep`
- `inventorySummary`
- 订单详情里的明确错误信息
- dispatch/log 证据

如果没有明确原因，必须说明当前证据不足，不能猜。

## 执行顺序

1. 查询 EXCEPTION 订单或指定订单详情。
2. 从详情/诊断字段提取原因。
3. 判断解决路径：补货、分仓、reopen、人工处理。
4. 用业务语言输出结果、原因、解决方案、下一步。

## 脚本

```bash
python scripts/query_orders.py --status EXCEPTION --size 20
python scripts/get_order_detail.py --order SO00361770
python scripts/diagnose_exception.py --order SO00361770
python scripts/diagnose_exception.py --from-list --size 10
python scripts/diagnose_exception.py --orders SO001 SO002
```

## 用户回复模板

```text
这张订单当前处于异常状态（staging）。

原因：[基于真实接口/日志提炼的异常原因]。

解决方案：[当前建议处理方式]。

下一步：[需要用户确认什么，或我可以继续做什么]。
```

## 禁止项

- 禁止只说“订单是 EXCEPTION”
- 禁止没有证据就猜库存、路由或仓库原因
- 禁止只给字段，不给解决方案
