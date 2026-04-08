# OpenLab

`OpenLab` 是一个独立的本地 intake 工具仓库，用来接收项目目录并生成首轮 inventory 与结构化分析结果。

它从 `Claude&GPTlocalinprove-wt-step-8-search-autoresearch-pilot` 中拆出，目的很直接：

- 让 Step 8 搜索实验继续保持单一职责
- 把“项目接入与首轮结构分析”变成单独能力

## 适合做什么

- 上传整个项目文件夹做首轮扫描
- 直接指定本机路径创建任务
- 为每个任务生成独立 workspace、日志和报告

## 快速开始

启动本地服务：

```powershell
pwsh -File tools/run-open-lab.ps1
```

默认地址：

- `http://127.0.0.1:8765`

直接对本机项目路径做 intake：

```powershell
python lab/open_lab.py intake-local --source-path "F:\01-Projects\SomeProject" --title "SomeProject" --goal "首轮结构分析"
```

清理任务：

```powershell
pwsh -File tools/lab-cleanup-task.ps1 -TaskId <task_id>
pwsh -File tools/lab-cleanup-task.ps1 -TaskId <task_id> -DropInput
```

## 当前输出

每个任务会生成独立目录，并产出这些核心文件：

- `task.json`
- `artifacts/inventory.json`
- `outputs/report.md`

## 目录结构

- `lab/`
  - 本地服务与 intake 逻辑
- `lab-data/`
  - 任务数据、输入、workspace、日志、报告
- `tools/`
  - 启动和清理脚本
- `docs/`
  - MVP 目标与架构说明

## 当前边界

这是一个 MVP，不是完整平台。当前已经覆盖：

- 开放入口
- 首轮结构分析
- 任务隔离

当前还没有覆盖：

- SSE 实时日志
- 正式数据库
- 自动 asset extraction
- playbook / insight 自动晋升

## 仓库关系

- `Claude&GPTlocalinprove`
  - 稳定 harness 主仓
- `Claude&GPTlocalinprove-wt-step-8-search-autoresearch-pilot`
  - 搜索实验仓库
- `OpenLab`
  - 独立 intake 与项目分析入口
