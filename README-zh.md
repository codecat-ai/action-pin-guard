# action-pin-guard

[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)


`action-pin-guard` 是一个只读的本地命令行工具，用来检查 GitHub Actions
工作流中的 `uses:` 引用，并标出没有固定到 40 位提交 SHA 的第三方 action。

扫描器只把 YAML 当作数据解析。它不会执行工作流、解析远程标签、调用 GitHub API
或修改文件。

## 问题与动机

标签和分支这类可变 action 引用可能在工作流审查之后发生变化。把第三方 action
固定到完整提交 SHA 可以提升可复现性，也让供应链审查更清晰。`action-pin-guard`
提供一个小型本地检查，方便维护者在启用更严格 CI 策略前先盘点风险。

## 功能

- 默认扫描 `.github/workflows`。
- 输出文件、行号、job、step、owner、repository、ref 和分类。
- 支持 `pinned-sha`、`tag`、`branch-or-other`、`local-action`、
  `docker-action`、`reusable-workflow` 分类。
- 发现未固定的外部 action 时返回退出码 `1`，除非使用 `--warn-only`。
- 提供稳定的 JSON 输出，便于 CI 处理。
- 可以为策略违规输出 GitHub Actions warning annotation，同时保持 stdout 上的
  JSON 可解析。
- 默认允许本地 action，并支持 owner 白名单。

## 本地使用

本项目尚未发布到包仓库。请从本地克隆使用。

```bash
git clone https://github.com/codecat-ai/action-pin-guard.git
cd action-pin-guard
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

在克隆目录中运行：

```bash
action-pin-guard check
```

也可以作为 Python 模块运行：

```bash
python -m action_pin_guard check .github/workflows
```

## 常用命令

```bash
action-pin-guard check
action-pin-guard check --json
action-pin-guard check --warn-only
action-pin-guard check --allow-owner my-org
action-pin-guard check --deny-docker
action-pin-guard check --github-annotations
action-pin-guard check --json --github-annotations
```

## 配置

- `--allow-owner OWNER` 允许内部或已审查过的 action owner 即使没有完整 SHA 也通过。
- `--warn-only` 在团队迁移现有工作流时保持提示模式，不让命令失败。
- `--deny-docker` 把 `docker://` action 引用视为违规。
- `--github-annotations` 只为策略违规向 stderr 写入一行 GitHub Actions
  `::warning`。固定到 SHA 的引用、允许的 owner、允许的本地 action、允许的
  Docker 引用不会产生 annotation；与 `--deny-docker` 一起使用时 Docker 引用会
  被标记。

## GitHub Actions 示例

在 workflow 中从源码 checkout 使用：

```yaml
steps:
  - uses: actions/checkout@v4
  - run: python -m pip install -e ".[dev]"
  - run: action-pin-guard check --github-annotations
```

## 路线图

- 用于共享策略的可选配置文件。
- 更详细的修复建议。
- 面向 CI 集成的 SARIF 输出。

## 贡献

欢迎提交 issue 和小型 pull request。请保持扫描器只读；变更行为前先写测试；并运行下面的开发检查。本项目在 AI 辅助下维护，但所有变更都会通过测试和 CI 验证后再合并。

## 开发

```bash
pytest
ruff check .
python -m build
```

## 许可证

本项目使用 MIT License。详情见 [LICENSE](LICENSE)。
