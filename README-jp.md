# action-pin-guard

[English](README.md) | [中文](README-zh.md) | [日本語](README-jp.md)


`action-pin-guard` は、GitHub Actions ワークフロー内の `uses:` 参照を調べる
読み取り専用のローカル CLI です。40 文字のコミット SHA に固定されていない
外部 action を見つけます。

スキャナーは YAML をデータとして解析します。ワークフローの実行、リモートタグの
解決、GitHub API の呼び出し、ファイル編集は行いません。

## 課題と動機

タグやブランチのような可変 action 参照は、ワークフローのレビュー後に変わる可能性があります。第三者 action を完全なコミット SHA に固定すると、再現性が高まり、サプライチェーンレビューもしやすくなります。`action-pin-guard` は、より厳格な CI ポリシーを有効にする前にリスクを把握するための小さなローカルチェックです。

## 機能

- 既定で `.github/workflows` をスキャンします。
- ファイル、行、job、step、owner、repository、ref、分類を出力します。
- `pinned-sha`、`tag`、`branch-or-other`、`local-action`、
  `docker-action`、`reusable-workflow` に分類します。
- 固定されていない外部 action が見つかると終了コード `1` を返します。
  `--warn-only` を使うと失敗扱いにしません。
- CI で扱いやすい安定した JSON 出力を提供します。
- ローカル action は既定で許可し、owner の許可リストも指定できます。

## ローカル利用

このプロジェクトはパッケージレジストリに公開されていません。ローカル clone から
利用してください。

```bash
git clone https://github.com/codecat-ai/action-pin-guard.git
cd action-pin-guard
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

clone したディレクトリで実行します。

```bash
action-pin-guard check
```

Python モジュールとしても実行できます。

```bash
python -m action_pin_guard check .github/workflows
```

## よく使うコマンド

```bash
action-pin-guard check
action-pin-guard check --json
action-pin-guard check --warn-only
action-pin-guard check --allow-owner my-org
action-pin-guard check --deny-docker
```

## 設定

- `--allow-owner OWNER` は、内部またはレビュー済みの action owner を完全な SHA なしでも許可します。
- `--warn-only` は、既存ワークフローの移行中にコマンドを助言モードのままにします。
- `--deny-docker` は `docker://` action 参照を違反として扱います。

## ロードマップ

- 共有ポリシー用の任意設定ファイル。
- より詳しい修正ヒント。
- CI 連携向けの SARIF または annotation 出力。

## コントリビュート

issue や小さな pull request を歓迎します。スキャナーは読み取り専用のままにしてください。動作変更の前にテストを書き、下記の開発チェックを実行してください。本プロジェクトは AI 支援でメンテナンスされていますが、変更はマージ前にテストと CI で検証されます。

## 開発

```bash
pytest
ruff check .
python -m build
```

## ライセンス

このプロジェクトは MIT License で公開されています。詳しくは [LICENSE](LICENSE)
を参照してください。
