# OpenLab

`OpenLab` 是从 `Claude&GPTlocalinprove-wt-step-8-search-autoresearch-pilot` 中拆出的独立项目。

用途：

- 接收整个项目文件夹上传
- 或直接指定本机项目路径
- 生成首轮项目 inventory 和结构化分析结果

当前目录结构：

- `docs/`
- `lab/`
- `lab-data/`
- `tools/`

常用启动方式：

```powershell
pwsh -File tools/run-open-lab.ps1
```

默认地址：

- `http://127.0.0.1:8765`

常用清理方式：

```powershell
pwsh -File tools/lab-cleanup-task.ps1 -TaskId <task_id>
```

说明：

- 这个目录在 2026-04-08 从 Step 8 搜索实验 worktree 中独立出来，目的是让搜索实验继续保持单一职责。
- 历史 intake 数据保留在 `lab-data/tasks/`。
