# 实验室 Agent 项目审计与目标架构

## 一、我看到的项目现状

### 1. 已有能力
这个项目并不是“空壳”，而是已经有一套很强的 **研究协议 + 搜索实验 + 评测回放** 内核：

- 主仓：`Claude&GPTlocalinprove`
  - `tools/search-harness/research.ps1`：生成严格研究卡 / 搜索协议卡
  - `tools/search-harness/run.ps1`：执行 / score / readiness / list
  - `tools/search-harness/score.mjs`：评分与 readiness 判定
  - `tools/llm-wrapper.ps1`：统一封装 codex / cline / claude 调用
  - `tools/tavily-search.js`：repo-local 搜索入口
- 实验仓：`Claude&GPTlocalinprove-wt-step-8-search-autoresearch-pilot`
  - `experiments/search-autoresearch/run-baseline.mjs`
  - `experiments/search-autoresearch/run-baseline.ps1`
  - `experiments/search-autoresearch/autoresearch/run-once.ps1`
  - `experiments/search-autoresearch/autoresearch/run-replay-loop.ps1`
  - `experiments/search-autoresearch/autoresearch/results.tsv`
  - `experiments/search-autoresearch/asset-candidates.md`

### 2. 当前项目的本质定位
它现在更像：

- 一个 **研究执行内核**
- 一个 **搜索实验室**
- 一个 **协议与评测系统**
- 一个 **研究 prompt / research card 生成器**

而不是：

- 一个普通人可用的产品
- 一个有前端入口的实验室平台
- 一个有任务隔离和资产沉淀闭环的系统

## 二、当前架构的优点

### 强项 1：实验层和稳定层已经有意识分离
主仓负责稳定层，worktree 负责 Step 8 实验层。这说明你的系统已经有“实验 -> 验证 -> 回灌”的雏形。

### 强项 2：不是纯聊天，而是有协议
`modes/*.json`、`strictRules`、`evidenceFields`、`stopConditions` 说明你已经开始把“研究行为”结构化，而不是只依赖一段 prompt。

### 强项 3：有评分、readiness、ledger
`score.mjs`、`readiness.default.json`、`results.tsv`、`run-replay-loop.ps1` 说明你已经在做“实验结果可比较、可复现、可回放”。

### 强项 4：有资产候选意识
`asset-candidates.md` 已经是资产沉淀的第一步，只是现在还是手工、半结构化。

### 强项 5：有多宿主适配思路
`llm-wrapper.ps1` 已经把 `codex / cline / claude` 做了统一包装，这是未来做 provider 抽象层的好起点。

## 三、当前项目的关键缺陷

### P0：没有正式产品壳
目前没有看到真实前端，也没有看到 Web API / 服务端入口。项目仍然依赖命令行 + 脚本 + 本地目录。

### P0：没有任务隔离模型
当前运行是“实验脚本跑一次 baseline / replay / search mode”，但不是“用户提交一个课题 -> 创建 task_id -> 独立 workspace -> 产出报告 -> 资产回灌”。

### P0：没有资产沉淀数据库
现在沉淀主要落在：

- `.codex-output/...`
- `runs/...`
- `results.tsv`
- `asset-candidates.md`

这说明资产存在，但没有统一 schema，没有数据库，没有统一检索口，没有“复用历史经验”的主通道。

### P0：搜索底座没有抽象成正式适配层
现在主搜索入口还是 `tools/tavily-search.js`，它更像“一个具体实现”，不是通用的 `SearchAdapter`。

### P0：结果回写实验室机制还是人工/半人工
目前 `promote / hold / reject` 的思路已经有了，但还没有真正形成：

- 运行结果 -> 自动抽取经验
- 经验 -> 自动形成可复用 playbook
- playbook -> 自动影响下一轮任务
- 机制变更 -> 进入候选区 -> 经验证后升版

### P1：高度依赖本地 Windows 路径和本地 CLI 环境
项目中可见大量本地绝对路径与本机假设，例如：

- `F:\01-Projects\...`
- `C:\Users\67115\.cline`
- `C:\Windows\System32\WindowsPowerShell\...`

这会导致：

- 难迁移
- 难部署
- 难复现
- 难做容器化

### P1：依赖声明不完整
主仓 `package.json` 只有脚本，没有明确依赖与 lockfile。说明当前运行成功很依赖“你本机已经装好了什么”。

### P1：provider 可用性不稳定，真实依赖单一
从 handoff 可见：

- `cline` 是主力
- `codex` / `claude` 在 Step 8 全流程上并不稳定

这意味着你虽然有多 provider 抽象，但真实运行上仍是“单点依赖”。

### P1：实验 ledger 已经开始膨胀
Step 8 的 replay 和 ledger 很多，说明实验很活跃；但如果没有后续归档与抽取层，会越来越难读，最后会反过来污染主线。

### P1：没有对外 API contract
即使你已经有 `research.ps1`、`run.ps1`，它们仍然是脚本，不是正式 API。

### P0 安全问题：压缩包里包含明文密钥
压缩包中的 `.mcp.json` 包含明文 `TAVILY_API_KEY`。哪怕这个文件在 `.gitignore` 中，**只要打包或共享过，就当密钥已经泄露**。应立即轮换，并改为环境变量或 secret manager。

## 四、我给你的“最终形态”

你的项目最终不应该只是“研究脚本集合”，而应该是一个 **实验室 Agent 平台**。

### 最终形态一句话

**上传资料 -> 创建独立研究任务 -> 调用搜索/agent 执行 -> 可视化过程 -> 输出报告 -> 自动沉淀资产 -> 提炼通用解法 -> 回灌实验室机制。**

## 五、目标架构（推荐）

### 1. 前端层（普通人可用）
建议至少有这些页面：

- 任务列表页
- 新建研究任务页
- 任务详情页
- 结果页
- 资产库页
- 机制/策略页（先简化）

前端功能：

- 上传文件
- 输入研究目标
- 选择研究模式
- 启动任务
- 看进度 / 日志 / 当前步骤
- 查看最终报告
- 查看资产抽取结果
- 检索历史经验

### 2. API / 编排层
建议做成正式后端服务，负责：

- 创建任务
- 上传文件
- 启动任务
- 查询任务状态
- 推送进度事件
- 获取结果
- 资产入库
- 检索历史资产
- 触发机制评估

### 3. 运行编排层（核心）
这是你的大脑中枢，负责：

- 给每个任务分配 `task_id`
- 创建独立 workspace
- 调度搜索适配器
- 调度 LLM provider
- 调度评分/验证模块
- 收集日志和中间产物
- 统一写入数据库和文件资产

### 4. 搜索适配层
把现在“脚本式搜索底座”改造成统一接口：

- `TavilySearchAdapter`
- `DedicatedSearchAdapter`
- `WebSearchAdapter`
- `AssetLibrarySearchAdapter`

统一接口建议：

```ts
search(query, options) => {
  results: [
    {
      title,
      url,
      snippet,
      source,
      score,
      metadata
    }
  ],
  raw,
  diagnostics
}
```

### 5. 研究执行层
从你现在的脚本抽象成 pipeline：

- ingest（摄入文件）
- retrieve（检索）
- plan（拆研究子问题）
- execute（逐步研究）
- evaluate（评分 / readiness / verdict）
- synthesize（生成报告）
- extract_assets（抽资产）
- propose_policy_update（提出机制优化候选）

### 6. 资产沉淀层
这是你项目真正会越来越值钱的地方。

建议拆成 4 类资产：

#### A. Run Asset
每次任务原始产物：
- 输入文件
- 搜索结果
- 中间 JSON
- 最终报告
- 日志
- 指标

#### B. Insight Asset
从任务中抽出来的“结论型资产”：
- 问题类型
- 根因
- 有效策略
- 无效策略
- 适用条件
- 置信度

#### C. Playbook Asset
面向复用的通用解法：
- 触发条件
- 推荐步骤
- 推荐查询模板
- 推荐评估标准
- 不适用边界

#### D. Policy Candidate
实验室机制优化候选：
- 改了什么
- 基线是什么
- 对比结果是什么
- 成本变化是什么
- verdict 是 promote / hold / reject

## 六、建议的数据模型

### tasks
- id
- title
- goal
- mode
- status
- created_at
- started_at
- ended_at
- created_by

### task_files
- id
- task_id
- file_name
- mime_type
- path
- checksum

### runs
- id
- task_id
- provider
- profile
- pipeline_version
- workspace_path
- score_summary_json
- readiness_verdict
- started_at
- ended_at

### artifacts
- id
- run_id
- type
- path
- summary
- metadata_json

### insights
- id
- run_id
- problem_type
- root_cause
- effective_solution
- ineffective_solution
- confidence
- evidence_refs_json

### playbooks
- id
- title
- trigger_conditions
- steps_markdown
- query_templates_json
- evaluation_rules_json
- source_run_ids_json
- status
- version

### policy_candidates
- id
- name
- scope
- baseline_ref
- after_ref
- delta_json
- verdict
- promoted_version

## 七、任务目录建议

```text
lab-data/
  tasks/
    task_20260326_001/
      input/
      workspace/
      logs/
      outputs/
      artifacts/
      task.json
      run.json
  assets/
    reports/
    insights/
    playbooks/
    policy-candidates/
  indexes/
    sqlite/
    vector/
```

## 八、推荐 API

### 任务
- `POST /api/tasks`
- `POST /api/tasks/{taskId}/files`
- `POST /api/tasks/{taskId}/start`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/events`
- `GET /api/tasks/{taskId}/result`

### 资产
- `POST /api/runs/{runId}/extract-assets`
- `GET /api/assets`
- `GET /api/assets/{assetId}`
- `GET /api/playbooks/search?q=...`
- `GET /api/insights/search?q=...`

### 搜索适配器
- `POST /api/search/preview`
- `GET /api/search/adapters`
- `POST /api/search/adapters/test`

### 机制优化
- `GET /api/policy-candidates`
- `POST /api/policy-candidates/{id}/promote`
- `POST /api/policy-candidates/{id}/reject`

## 九、MVP 实施顺序

### 第 1 阶段：把“脚本集合”包成可用产品
目标：先让普通人能用。

必须做：
- 前端上传文件
- 创建任务
- 独立 workspace
- 后端调用现有脚本
- 实时日志 / 状态
- 结果页

### 第 2 阶段：把结果沉淀成资产
必须做：
- SQLite
- artifacts 表
- insights 表
- playbooks 表
- 自动从 run 结果中抽结构化资产

### 第 3 阶段：把资产反哺下一次任务
必须做：
- 新任务启动前先检索历史 playbook / insight
- 把历史经验注入研究上下文
- 让 agent 先复用，再新搜

### 第 4 阶段：把机制优化闭环化
必须做：
- 把当前 `promote / hold / reject` 自动化入库
- 形成 policy candidate 审核页
- 区分实验层与稳定层

## 十、我建议的技术路线

### 路线原则
- 不重写现有搜索实验核心
- 先包裹，再替换
- 保持实验层可继续跑
- 把稳定层正式服务化

### 推荐实现

#### 方案 A（最贴近你现状，推荐）
- 前端：Next.js 或 React
- 后端：Node.js + Fastify/Express
- 数据库：SQLite
- 任务执行：child_process 调用你现有 `.ps1 / .mjs / .js`
- 事件推送：SSE
- 文件存储：本地文件夹

为什么推荐：
- 你现有核心就是 Node + PowerShell
- 改造成本最低
- 最快做出“能用的实验室界面”

#### 方案 B（更适合长期 AI 编排）
- 前端：React
- 后端：FastAPI
- Worker：Celery / RQ / subprocess
- 适配层：调用现有 Node/PowerShell

为什么不建议你现在先上：
- 会引入第二套主 runtime
- 对你当前项目不是最低摩擦路线

## 十一、你现在最应该先改的 10 件事

1. 立刻轮换明文 Tavily key，并改成环境变量。
2. 新建正式后端服务，不要再把脚本当入口本身。
3. 给每个任务引入 `task_id + workspace`。
4. 把 `research.ps1 / run.ps1 / run-once.ps1` 包成 adapter，而不是直接暴露给用户。
5. 建 SQLite，把 `tasks / runs / artifacts / insights / playbooks / policy_candidates` 建起来。
6. 做一个最小前端：任务创建、任务详情、结果查看。
7. 把现有 `.codex-output` 与 `experiments/.../runs` 视为内部运行层，不再让用户直接面对它们。
8. 把 `asset-candidates.md` 升级成结构化资产抽取流程。
9. 清理绝对路径，改成配置化路径与环境变量。
10. 加上最小健康检查与回归验证，让 API 层能知道底层脚本是否能跑。

## 十二、你这个项目最适合的最终命名方式

不要再把它只叫“脚本仓库”或“搜索实验仓”。

更准确的定义应该是：

**Research Lab Agent Platform**

或者中文：

**可视化研究实验室平台**

它的组成是：

- 稳定研究执行层
- 搜索适配层
- 评分与回放层
- 资产沉淀层
- 机制优化层
- 前端任务工作台

## 十三、下一步我最建议你继续提供的东西

如果你的“专用搜索底座”并不只是现在看到的 Tavily/脚本层，那么下一次最好再补下面任意一种：

1. 搜索底座单独 zip
2. 搜索 API 文档
3. 一个最小调用样例
4. 请求/返回 JSON 示例
5. 鉴权方式
6. 索引的数据源说明

我拿到后，就可以把它正式接入上面的 `SearchAdapter` 设计，而不是只停留在 Tavily 这一层。
