# action-pin-guard

[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)


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
- ポリシー違反に対して GitHub Actions の warning annotation を出力でき、
  stdout の JSON は解析可能なまま保てます。
- ローカル action は既定で許可し、owner の許可リストも指定できます。
- 共有ポリシー用に任意の JSON または TOML 設定ファイルを利用できます。

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
action-pin-guard check --config .action-pin-guard.json
action-pin-guard check --github-annotations
action-pin-guard check --json --github-annotations
```

## 設定

- `--allow-owner OWNER` は、内部またはレビュー済みの action owner を完全な SHA なしでも許可します。
- `--warn-only` は、既存ワークフローの移行中にコマンドを助言モードのままにします。
- `--deny-docker` は `docker://` action 参照を違反として扱います。
- `--config FILE` は `.json` または `.toml` ファイルから共有ポリシーを読み込みます。
- `--github-annotations` は、ポリシー違反ごとに GitHub Actions の `::warning`
  を 1 行ずつ stderr に出力します。SHA に固定された参照、許可された owner、
  許可されたローカル action、許可された Docker 参照には annotation を出しません。
  `--deny-docker` と組み合わせると Docker 参照も対象になります。

`.action-pin-guard.json` の例：

```json
{
  "allow_owners": ["my-org", "trusted-actions"],
  "deny_docker": true,
  "warn_only": false
}
```

`.action-pin-guard.toml` の例：

```toml
allow_owners = ["my-org", "trusted-actions"]
deny_docker = true
warn_only = false
```

対応するキーは `allow_owners`、`deny_docker`、`warn_only` です。JSON は常に
利用できます。TOML は Python 3.11 の `tomllib` が利用できる場合に対応します。
ファイル拡張子でパーサーを選ぶため、設定ファイルは `.json` または `.toml` で
終わる必要があります。

コマンドラインオプションが指定された場合は、設定ファイルの値より優先されます。
`--allow-owner` は設定内の `allow_owners` と置き換えずに結合されます。

## GitHub Actions 例

workflow 内ではソース checkout から利用します。

```yaml
steps:
  - uses: actions/checkout@v4
  - run: python -m pip install -e ".[dev]"
  - run: action-pin-guard check --github-annotations
```

## ロードマップ

- チームが移行状況を継続的に追跡するためのベースラインレポート。
- より詳しい修正ヒント。
- CI 連携向けの SARIF 出力。

## コントリビュート

issue や小さな pull request を歓迎します。スキャナーは読み取り専用のままにしてください。動作変更の前にテストを書き、下記の開発チェックを実行してください。本プロジェクトは AI 支援でメンテナンスされていますが、変更はマージ前にテストと CI で検証されます。

## 開発

```bash
pytest
ruff check .
ruff format --check .
python -m build
```

## ライセンス

このプロジェクトは MIT License で公開されています。詳しくは [LICENSE](LICENSE)
を参照してください。
