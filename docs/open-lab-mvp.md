# Open Lab MVP

## 目标

把当前 worktree 从“分支实验室底座”扩成“总 lab 的开放入口 MVP”，至少支持两种 intake：

1. 浏览器上传整个项目文件夹
2. 直接填本机项目路径做首轮分析

## 入口

- 启动服务：`pwsh -File tools/run-open-lab.ps1`
- 默认地址：`http://127.0.0.1:8765`

## 当前能力

- 创建 `task_id`
- 为每个任务建立独立目录：
  - `lab-data/tasks/<task_id>/input`
  - `lab-data/tasks/<task_id>/workspace`
  - `lab-data/tasks/<task_id>/logs`
  - `lab-data/tasks/<task_id>/outputs`
  - `lab-data/tasks/<task_id>/artifacts`
- 对上传文件夹或本机路径做首轮 inventory 分析
- 输出：
  - `task.json`
  - `artifacts/inventory.json`
  - `outputs/report.md`

## 分析内容

- 文件总数、目录总数、总体积
- 主要扩展名
- 主要语言
- 关键文件命中
- 大文件清单
- 项目类型信号

## 清理

- 默认清理：`pwsh -File tools/lab-cleanup-task.ps1 -TaskId <task_id>`
- 连输入文件一并清理：`pwsh -File tools/lab-cleanup-task.ps1 -TaskId <task_id> -DropInput`

## 当前边界

- 这还是 MVP，不是完整产品平台
- 现在做的是“开放入口 + 首轮结构分析 + 任务隔离”
- 还没做：
  - SSE 实时日志
  - 正式数据库
  - 自动 asset extraction
  - playbook / insight 自动晋升

## 下一步

1. 把任务分析结果接到 `runs / insights / playbooks / policy-candidates`
2. 为 intake 后的项目生成 workflow 体检和 agent 体检
3. 把现有 `search-autoresearch` 分支实验室接到总 lab 路由器
