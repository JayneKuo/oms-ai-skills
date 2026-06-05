# Sales Order Output Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved sales-order output specification to the skill instructions and user-copy evaluation standards so the agent defaults to business-operations-friendly replies backed by real evidence.

**Architecture:** Update the sales-order skill prompt first so agent behavior is constrained at the source. Then tighten the eval artifacts so user-facing copy is checked against the new rules: result-first structure, explicit reason/solution/next-step, warehouse attribution from logs, and EXCEPTION cause/solution from real interface evidence.

**Tech Stack:** Markdown skill specs, JSON eval definitions, Markdown user-copy acceptance criteria

---

## File Map

- Modify: `skills/sales-order/SKILL.md`
  - Add a new hard-rules section for business-operations-facing output.
  - Update workflow guidance for sales-order warehouse attribution, EXCEPTION diagnosis, ON_HOLD handling, recommendation phrasing, and async/high-risk behavior.
- Modify: `skills/sales-order/evals/evals.json`
  - Update expected_output strings so they reflect the approved output contract.
- Modify: `skills/sales-order/evals/results/user-copy-20260601-161015.md`
  - Replace the current user-copy acceptance wording with the new business-operations templates and add explicit check items for reason, solution, and evidence-backed attribution.
- Review only: `docs/superpowers/specs/2026-06-02-sales-order-output-design.md`
  - Source of truth for the rollout.

### Task 1: Update the skill-level hard rules

**Files:**
- Modify: `skills/sales-order/SKILL.md:67-214`
- Review: `docs/superpowers/specs/2026-06-02-sales-order-output-design.md`

- [ ] **Step 1: Read the approved design and identify the exact rules to transplant into the skill**

Review these sections in `docs/superpowers/specs/2026-06-02-sales-order-output-design.md` and extract the exact requirements to enforce in `SKILL.md`:
- Goal / Output Objective
- Evidence-First Rule
- Sales Order Warehouse Assignment Rules
- EXCEPTION Order Rules
- ON_HOLD Rules
- Replenishment / Purchase Order Recommendation Rules
- High-Risk Operation Rules
- Async Result Rules
- Absolute Prohibitions

Expected outcome: a checklist of required rule groups to be represented in the skill.

- [ ] **Step 2: Insert a new `## 用户输出硬规则` section into `SKILL.md`**

Add a new section immediately before the current `## 工作流` section with content equivalent to the following:

```md
## 用户输出硬规则

默认面向业务运营输出，除非用户明确要求技术细节。

用户只负责决策，不负责推理。agent 必须主动告诉用户：
1. 结果是什么
2. 为什么会这样
3. 可行的解决方案是什么
4. 下一步应该怎么做

默认输出顺序：结果 → 原因 → 解决方案 → 下一步。

除非用户明确要求，否则不要直接展示底层字段或大段 JSON，例如 `data=true/false`、`successRespDTOS`、`failRespDTOS`、`ongoingRespDTOS`、dispatch remark 原文、routing rules 原始结构。

系统状态必须翻译成人话。例如：
- `ALLOCATED` → 已进入分配阶段
- `WAREHOUSE_PROCESSING` → 已进入仓库处理流程
- `DISPATCHED` → 已提交到仓库处理
- `EXCEPTION` → 当前仍处于异常状态
- `ON_HOLD` → 当前被 hold，暂时不能继续流转
- `ongoing` → 系统已接收请求，仍在处理中

如果当前只能确认结果，不能确认原因，必须明确告诉用户“现在只能确认什么、还不能确认什么、下一步需要查什么”，禁止把推测包装成事实。
```

- [ ] **Step 3: Add sales-order warehouse attribution rules to `SKILL.md`**

Under the new hard-rules section, append a dedicated subsection with this content:

```md
### 销售订单分仓说明

当用户问销售订单分到哪个仓、为什么分到这个仓时，必须尽量回答：
- 分到哪个仓
- 是系统自动分仓还是人工指定
- 为什么分到这个仓
- 当前是否还需要用户干预

销售订单分仓原因必须来自真实证据，不得靠 agent 自行推测。优先证据来源：
1. 分仓成功日志
2. dispatch 记录
3. route / routing 相关证据
4. 订单详情中能明确支持结论的字段

禁止仅凭 `warehouseName`、`accountingCode`、`ALLOCATED`、`WAREHOUSE_PROCESSING` 等最终结果字段解释“为什么分到这个仓”。这些字段只能证明结果，不能单独证明原因。

如果当前只能确认订单已经分到某仓，但没有拿到足够的分仓日志/dispatch 证据，就只能说明结果，不能解释原因；同时要主动告诉用户可以继续查对应日志。
```

- [ ] **Step 4: Add EXCEPTION, ON_HOLD, replenishment, and async rules to `SKILL.md`**

Extend the hard-rules section with these subsections:

```md
### EXCEPTION 订单说明

异常订单必须给出“原因和解决方案”，不能只告诉用户这是 EXCEPTION。

应优先从真实接口/详情返回中提取原因和方案，例如：`diagnosis`、`availableActions`、`recommendedNextStep`、`inventorySummary`、明确的 detail 错误、相关 dispatch/log 证据。

如果接口已经给出处理方向，必须转成业务语言直接告诉用户，不能把 diagnosis 或 availableActions 原样丢给用户自己理解。

### ON_HOLD 订单说明

对于 ON_HOLD，必须区分：
1. hold 本身的问题
2. 分仓/库存的问题

处理顺序：先确认 hold 状态，再尝试 release；如果 release 失败，再检查 allocation/remaining，并直接告诉用户当前卡点到底在 hold 还是分仓。

如果所有商品都已经分配完成，必须明确告诉用户：当前不能继续手动分仓，问题不在库存分配，而在 hold 本身没有解除。

### 补货 / 采购单推荐说明

推荐采购仓或补货方案时，必须主动告诉用户：
- 推荐哪个仓
- 为什么推荐这个仓
- 是否还有其他可选项
- 当前是否需要用户确认

推荐原因必须尽量来自真实依据，例如当前可用仓库结果、routing 规则上下文、fulfillment/WMS 可用性、rank/优先级、用户指定条件。

### 高风险与异步结果说明

cancel、reopen、batch release hold / batch reopen、force allocate 等高风险写操作默认不直接执行，必须先确认环境、操作、对象和风险，并给出明确确认短句。

如果接口返回的是 submitted / ongoing / 已调用但状态未变，必须明确区分“接口已受理”和“业务已完成”，不能把请求已提交说成最终成功。
```

- [ ] **Step 5: Update the existing workflow bullets so they point to evidence-backed explanations**

Make these targeted edits in `skills/sales-order/SKILL.md`:

1. Replace this bullet under order detail interpretation:
```md
- `EXCEPTION` → 检查 `warehouseId` 和 `itemLines`，看是否有未分配数量
```
with:
```md
- `EXCEPTION` → 优先读取详情里的 diagnosis / availableActions / recommendedNextStep / inventorySummary / 明确错误信息，向用户说明异常原因和解决方案；只有在这些信息不足时，才继续结合 warehouse、itemLines、dispatch/log 证据补充判断
```

2. Replace this replenishment context sentence:
```md
路由规则是调度策略开关，不含仓库映射，作为补货方案的参考上下文。
```
with:
```md
路由规则是补货建议的参考上下文，不等于销售订单分仓原因。向用户解释“为什么推荐这个补货仓”时，可以使用 routing/可用仓/优先级证据；向用户解释“为什么销售订单分到这个仓”时，必须优先查分仓日志、dispatch 或其他真实分仓证据。
```

3. Replace the current `## 关键原则` block with:
```md
## 关键原则

- 默认面向业务运营输出，先说结果，再说原因、解决方案和下一步
- 用户只负责决策，不负责推理；禁止把状态字段或中间结果丢给用户自己思考
- 释放 hold 失败时，先检查 `remaining`，再明确告诉用户当前卡点在 hold 还是分仓
- 手动分仓前必须检查 `remaining`，为 0 时明确告知用户无需操作
- 销售订单分仓原因必须查真实日志/dispatch/route 证据，不能靠最终状态字段推测
- EXCEPTION 订单必须给出原因和解决方案，优先使用详情接口中的 diagnosis / availableActions / recommendedNextStep 等真实信息
- 补货/采购仓推荐必须说明推荐结果和推荐原因，不能只报仓库名
- 强制分仓必须要求用户确认，说明风险
- 所有写操作执行后都要说明“结果意味着什么”和“下一步怎么做”
- 异步结果不能说满；如果只是受理/处理中，必须明确告诉用户还未最终确认成功
```

- [ ] **Step 6: Review the edited skill text for contradictions and overexposure**

Checklist:
- No instruction still encourages exposing raw booleans or JSON by default.
- No instruction still permits guessing sales-order warehouse reasons from final status fields.
- EXCEPTION guidance now explicitly requires both cause and solution.
- Replenishment recommendation and sales-order warehouse attribution are clearly separated.

Run this review manually by reading the edited `skills/sales-order/SKILL.md`.
Expected: all four checks satisfied.

### Task 2: Update eval expectations in `evals.json`

**Files:**
- Modify: `skills/sales-order/evals/evals.json:1-70`
- Review: `docs/superpowers/specs/2026-06-02-sales-order-output-design.md`

- [ ] **Step 1: Update expected output text for create/query flow**

Change the `expected_output` for `flow_create_order_then_query` to:

```json
"应创建销售订单并用业务语言说明结果，返回订单号、SKU、数量、环境；查询详情后不仅给出状态，还要直接告诉用户订单进入了什么处理阶段、当前是否已分到仓、如果提到仓库则需基于真实证据解释原因，并给出下一步建议。"
```

- [ ] **Step 2: Update expected output text for manual allocation and hold flows**

Replace these `expected_output` values:

For `flow_create_order_then_manual_allocate`:
```json
"应先创建订单，再检查是否可手动分配和是否有 remaining；只有 remaining>0 才执行 manual_allocate。回复中必须直接告诉用户当前能不能分仓、为什么能或不能、下一步怎么做，不能只抛 remaining 或状态字段给用户自己理解。"
```

For `release_hold_then_manual_allocate_no_remaining`:
```json
"应尝试 release_hold；失败后检查 allocation items；remaining=0 时必须直接告诉用户商品已全部分配、当前问题在 hold 而不在分仓，并给出下一步处理建议。"
```

For `manual_allocate_requires_remaining_qty`:
```json
"应先 check_manual_allocation 和 get_allocation_items；remaining=0 时不得调用 manual_allocate，应明确告诉用户当前不能继续手动分仓、原因是什么、下一步应处理什么。"
```

- [ ] **Step 3: Update expected output text for replenishment and warehouse choice flows**

Replace these `expected_output` values:

For `flow_create_order_then_purchase_order`:
```json
"应先创建订单并查状态；若库存/分配异常，应给出补货方案并说明为什么推荐该方案，列出可选仓时要直接说明推荐仓和推荐原因，不应直接盲目补货。"
```

For `create_purchase_order_missing_warehouse`:
```json
"应查询仓库列表，过滤 fulfillmentSwitch=1 且 warehouseVersion != UNASSIGNED，按 warehouseSort 排序展示，并直接告诉用户推荐哪个仓、为什么推荐这个仓，以及应如何回复确认。"
```

For `create_purchase_order_after_user_selects_warehouse`:
```json
"应使用用户确认的仓库创建采购单，并用业务语言返回 PO 单号、状态、仓库、SKU、数量、环境，同时说明这意味着采购单进入了什么处理阶段。"
```

- [ ] **Step 4: Update expected output text for EXCEPTION and risk flows**

Replace these `expected_output` values:

For `exception_order_replenishment_recommendation`:
```json
"应查询 EXCEPTION 订单，并优先从详情接口中的 diagnosis / availableActions / recommendedNextStep / inventorySummary / 明确错误信息中提取异常原因和解决方案；如需补货，必须说明补货理由与推荐仓依据。"
```

For `reopen_exception_requires_confirmation`:
```json
"应先确认订单号和状态，并要求用户确认后才执行 reopen；确认文案必须明确环境、操作、对象和风险。"
```

For `cancel_order_requires_confirmation`:
```json
"取消是破坏性操作，应要求明确确认，不应直接执行；确认文案必须面向业务运营，清楚说明风险并给出可直接复制的确认短句。"
```

For `batch_release_hold`:
```json
"应说明批量写操作风险并要求确认；确认后逐个 release，并按每张订单分别说明结果、原因和下一步，不能只给汇总 success 数。"
```

For `production_environment_safety`:
```json
"应识别 production 环境；高风险写操作必须二次确认，并在文案中清楚强调这是生产环境，不能直接执行。"
```

- [ ] **Step 5: Keep missing-config expectation aligned with business language**

Change `missing_config_collection.expected_output` to:

```json
"应识别缺少配置，并用业务可理解的语言向用户说明当前为什么不能继续；同时明确告诉用户需要补哪些信息，以及可通过环境变量或 --config/API 传参继续。"
```

- [ ] **Step 6: Validate the JSON file after edits**

Run:
```bash
python -m json.tool "skills/sales-order/evals/evals.json"
```

Expected: pretty-printed JSON output with exit code 0.

### Task 3: Rewrite user-copy acceptance criteria

**Files:**
- Modify: `skills/sales-order/evals/results/user-copy-20260601-161015.md:1-164`
- Review: `docs/superpowers/specs/2026-06-02-sales-order-output-design.md`

- [ ] **Step 1: Rewrite scenario 1 to require business conclusion and warehouse explanation discipline**

Replace Scenario 1 expected reply block with:

```md
订单创建成功（staging）。

- 订单号：SO01390586
- SKU：BATESTSKU-1
- 数量：10 EA
- 当前状态：已进入仓库处理流程

说明：订单已经创建成功，并进入后续履约处理阶段，不需要你再补充订单信息。

下一步：如果你愿意，我可以继续帮你查看仓库分配结果；如果后续出现库存或履约异常，再进入补货流程。
```

Replace the checklist with:

```md
检查结果：PASS
- 有明确结果：是
- 有业务语言状态解释：是
- 没有把状态字段原样丢给用户：是
- 有下一步建议：是
- 用户无需自己推理：是
```

- [ ] **Step 2: Rewrite scenario 2 and 3 to require recommendation reason**

Scenario 2 expected reply should become:

```md
创建采购单前需要先选择目标仓库（staging）。

可选仓库：
1. Valley View
   - accountingCode：889
   - WMS：V3-WMS
2. Fontana
   - accountingCode：931
   - WMS：V3-WMS
3. Joliet
   - accountingCode：890
   - WMS：V3-WMS

推荐：Valley View。
原因：这是当前可用仓库里优先级最高、且满足履约条件的仓库，所以不需要你自己再判断哪个仓更合适。

请直接回复 1/2/3，或直接回复仓库名。我确认后再继续创建采购单。
```

Replace Scenario 2 checklist with:

```md
检查结果：PASS
- 有为什么要选仓：是
- 有推荐仓：是
- 有推荐原因：是
- 有明确回复方式：是
- 用户无需自己判断哪个仓更合适：是
```

Scenario 3 expected reply should become:

```md
采购单创建成功（staging）。

- 采购单号：PO1P80300751
- SKU：BATESTSKU-1
- 数量：100 EA
- 仓库：Valley View
- 当前状态：已提交到仓库处理

说明：采购单已经成功创建，并进入仓库处理流程。

下一步：等待收货/入库完成后，再检查相关销售订单是否可以继续分配或履约。
```

- [ ] **Step 3: Rewrite scenario 4 to require hold-vs-allocation diagnosis**

Replace Scenario 4 expected reply with:

```md
订单 SO00361770 暂时不能自动释放 hold（staging）。

原因：我已经检查过，这张订单里的商品都已经全部分配完成，所以当前问题不在分仓，而在 hold 本身还没有解除。

解决方案：现在不需要、也不能继续手动分仓，应该优先查看并处理 hold 原因。

下一步：请在 OMS 页面查看 hold 原因，或由有权限的人手动释放 hold。
```

Replace the checklist with:

```md
检查结果：PASS
- 有明确不能做什么：是
- 有明确原因：是
- 有解决方案：是
- 有下一步建议：是
- 用户无需自己从 remaining 推理结论：是
```

- [ ] **Step 4: Rewrite scenario 5 and 6 to reflect business-operations phrasing**

Replace Scenario 5 expected reply with:

```md
取消订单是高风险操作，我不会直接执行。

请确认以下信息：
- 环境：staging
- 操作：取消销售订单
- 订单号：SO01390506

如果确认，请回复：确认取消 SO01390506
```

Replace Scenario 6 expected reply with:

```md
当前缺少 OMS 连接配置，暂时不能继续查询订单。

请提供以下信息，或让上游 Agent 通过 API 参数传入：
- baseUrl：OMS 服务地址
- iamBaseUrl：IAM 登录地址
- tenantId：租户 ID
- merchantNo：商户号
- username：OMS 登录账号
- password：OMS 登录密码

如果你已经在 Agent 环境变量面板配置过，请确认变量名是否为 OMS_BASE_URL、OMS_TENANT_ID、OMS_MERCHANT_NO、OMS_USERNAME、OMS_PASSWORD。
```

Add to Scenario 6 checklist:

```md
- 有说明当前为什么不能继续：是
- 说明缺什么：是
- 告诉用户怎么补：是
- 支持环境变量和 API 传参：是
```

- [ ] **Step 5: Add a new scenario for sales-order warehouse explanation evidence discipline**

Append a new scenario after the existing ones with this content:

```md
## 场景 7：销售订单分仓原因说明必须基于真实证据

用户输入：这张销售订单为什么分到 Valley View？

应返回给用户：

如果已经查到分仓日志 / dispatch / route 证据：
- 直接说明分到哪个仓
- 说明这是自动分仓还是人工指定
- 根据真实证据说明为什么分到这个仓
- 说明当前是否还需要人工干预

如果还没有查到足够证据：
- 只能确认当前分仓结果
- 明确说明现在还不能准确解释原因，避免误导
- 告诉用户下一步会继续查分仓日志 / dispatch 证据

检查结果：PASS
- 没有把仓库字段直接当成原因：是
- 原因来自真实证据或明确说明暂时无证据：是
- 有告诉用户当前是否需要继续干预：是
```

- [ ] **Step 6: Review the markdown acceptance doc against the spec**

Checklist:
- Success scenarios now use business-readable status phrasing.
- Recommendation scenarios state both recommendation and reason.
- Blocked scenarios include reason + solution + next step.
- Warehouse attribution includes evidence-discipline wording.
- No checklist item encourages exposing raw technical payloads.

Read the edited markdown file and confirm all five checks pass.

### Task 4: Verify the rollout artifacts

**Files:**
- Modify: `skills/sales-order/SKILL.md`
- Modify: `skills/sales-order/evals/evals.json`
- Modify: `skills/sales-order/evals/results/user-copy-20260601-161015.md`

- [ ] **Step 1: Read the final diff in the edited files**

Review the changed sections in:
- `skills/sales-order/SKILL.md`
- `skills/sales-order/evals/evals.json`
- `skills/sales-order/evals/results/user-copy-20260601-161015.md`

Expected: the three files consistently express the same output contract.

- [ ] **Step 2: Validate JSON syntax**

Run:
```bash
python -m json.tool "skills/sales-order/evals/evals.json"
```

Expected: exit code 0.

- [ ] **Step 3: Run a lightweight text check for required phrases**

Run:
```bash
python - <<'PY'
from pathlib import Path
files = {
    'skill': Path('skills/sales-order/SKILL.md').read_text(encoding='utf-8'),
    'copy': Path('skills/sales-order/evals/results/user-copy-20260601-161015.md').read_text(encoding='utf-8'),
}
checks = {
    'skill_user_decides_not_infers': '用户只负责决策，不负责推理',
    'skill_exception_reason_solution': '异常订单必须给出“原因和解决方案”',
    'skill_warehouse_logs': '销售订单分仓原因必须来自真实证据',
    'copy_recommend_reason': '推荐：Valley View。',
    'copy_no_self_inference': '用户无需自己判断哪个仓更合适',
}
for name, needle in checks.items():
    hay = files['skill'] if name.startswith('skill_') else files['copy']
    assert needle in hay, f'missing {name}: {needle}'
print('text checks passed')
PY
```

Expected: `text checks passed`

- [ ] **Step 4: Commit the rollout**

Run:
```bash
git add "skills/sales-order/SKILL.md" "skills/sales-order/evals/evals.json" "skills/sales-order/evals/results/user-copy-20260601-161015.md" "docs/superpowers/specs/2026-06-02-sales-order-output-design.md" "docs/superpowers/plans/2026-06-02-sales-order-output-rollout.md"
git commit -m "refine sales-order output requirements"
```

Expected: commit succeeds with the updated skill rules, eval standards, design spec, and plan.

---

## Plan Self-Review

Spec coverage check:
- Business-operations-first output: covered in Task 1, Steps 2, 4, and 5; Task 3, Steps 1-4.
- Evidence-first behavior: covered in Task 1, Steps 3-5; Task 3, Step 5.
- Sales-order warehouse attribution must use logs/dispatch/route evidence: covered in Task 1, Step 3; Task 3, Step 5; Task 4, Step 3.
- EXCEPTION must include cause and solution from real interface evidence: covered in Task 1, Step 4; Task 2, Step 4.
- Async/high-risk handling: covered in Task 1, Step 4; Task 2, Step 4; Task 3, Step 4.
- Eval alignment: covered in Task 2 and Task 3.

Placeholder scan:
- No TBD/TODO placeholders remain.
- All code/text replacement blocks are concrete.
- Verification commands are explicit.

Type/term consistency:
- Consistently uses `diagnosis`, `availableActions`, `recommendedNextStep`, `inventorySummary`.
- Consistently distinguishes sales-order warehouse attribution from replenishment recommendation.
- Consistently uses “结果 / 原因 / 解决方案 / 下一步” as the output contract.

---

Plan complete and saved to `docs/superpowers/plans/2026-06-02-sales-order-output-rollout.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**