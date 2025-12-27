
RAG Validation System
=====================

LLM / RAG 出力に対して ルールベース検証 を行う軽量バリデーションモジュールです。
pytest によるテスト駆動で安全に拡張できます。

----------------------------------------
目的（責務）
----------------------------------------

- LLM 出力が最低限の品質ルールを満たしているか検証
- 技術ドメイン別（I2C / SPI / UART / WiFi）の検証
- ドキュメント文章向けルール検証
- 本番環境で副作用ゼロで利用可能

----------------------------------------
ディレクトリ構成
----------------------------------------

rag/
 ├─ rag_validate.py        コアロジック
 ├─ validate.py            外部公開 API
 ├─ data/
 │   └─ rules/
 │       └─ rules.yaml
 ├─ tests/
 │   ├─ test_validate.py
 │   └─ test_detect_rule_key.py
 └─ logs/
     └─ validation_errors.jsonl

----------------------------------------
使い方
----------------------------------------

detect_rule_key(question)
VALIDATE_MAP[rule_key](answer_text)

----------------------------------------
運用モード
----------------------------------------

開発・通常本番
- 環境変数なし
- ログ出力なし
- 副作用ゼロ

本番トラブル対応
$env:RAG_VALIDATION_LOG="1"

ログ出力先
logs/validation_errors.jsonl

ログ無効化
Remove-Item Env:\RAG_VALIDATION_LOG

----------------------------------------
設計方針
----------------------------------------

- ログ ON/OFF は検証結果に影響しない
- pytest 結果は常に同一
- 本番安全設計

----------------------------------------
CLI JSON 出力仕様（固定）
----------------------------------------

--json オプション指定時、以下の JSON を必ず出力する。

[成功]
{
  "status": "ok",
  "rule": "<rule_key>",
  "errors": []
}

[検証 NG]
{
  "status": "ng",
  "rule": "<rule_key>",
  "errors": [
    "<error message>",
    ...
  ]
}

[CLI エラー]
{
  "status": "error",
  "message": "<reason>"
}

設計ポリシー
- status は必須
- JSON 構造は後方互換を破らない
- 追加は key のみ（既存 key の意味変更は禁止）
----------------------------------------
CLI 出力制御オプション
----------------------------------------

CLI では用途に応じて出力を制御できる。

[通常モード]
$ python -m rag input.txt
[OK] validation passed

[--quiet]
成功時は何も出力しない（exit code のみで判定可能）

$ python -m rag input.txt --quiet

[--verbose]
補助情報を表示する

$ python -m rag input.txt --verbose
[INFO] detected rule: <rule_key>
[OK] validation passed

[--json]
JSON 形式で結果を出力する（最優先）

$ python -m rag input.txt --json
{"status":"ok","rule":"<rule_key>","errors":[]}

----------------------------------------
CLI 出力制御ルール
----------------------------------------

- --json が最優先
- --quiet と --verbose は同時指定不可
- exit code は出力形式に依存せず固定
- ログ出力（RAG_VALIDATION_LOG）とは独立

exit code:
- 0 : OK
- 1 : 検証 NG
- 2 : CLI エラー
