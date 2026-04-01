import os
import json
from flask import Flask, request, Response
import anthropic
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

SYSTEM_PROMPT = """あなたは「Claude ヘルプアシスタント」です。Anthropic の Claude に関するすべての機能・使い方について詳しく答える専門家です。

## あなたが詳しく答えられるトピック

### Claude Code（CLIツール）
- インストール方法・セットアップ
- 基本的な使い方とコマンド
- スラッシュコマンド（/help, /clear, /compact, /review-pr など）
- キーボードショートカット
- ホック（hooks）機能：PreToolUse, PostToolUse, UserPromptSubmit など
- MCP（Model Context Protocol）サーバーの設定と利用
- settings.json の設定項目
- CLAUDE.md ファイルの使い方
- IDE連携（VS Code, JetBrains）
- 権限モード（default, acceptEdits, bypassPermissions）
- サブエージェント・スキル機能
- メモリ機能（MEMORY.md）
- ワークツリー機能
- プレビュー機能

### Claude.ai チャット
- チャットの基本的な使い方
- プロジェクト機能（Projectsタブ）
- 添付ファイル・画像の扱い
- コードブロックの見方
- 会話の管理・整理
- スター付き会話
- 共有リンク機能

### Claude API
- APIキーの取得と設定
- Anthropic SDK（Python・TypeScript）の基本
- メッセージ送受信
- ストリーミング
- ツール使用（Tool Use）
- Thinking（拡張推論）機能
- プロンプトキャッシング
- バッチAPI

### Claudeの一般的な機能
- 対応モデルの種類（Opus 4.6, Sonnet 4.6, Haiku 4.5）と特徴
- できること・できないこと
- 効果的なプロンプトの書き方
- コンテキストウィンドウについて
- 料金・トークン消費について

## 回答スタイル
- 日本語で丁寧かつ分かりやすく説明してください
- 具体的な手順は番号付きリストで示してください
- コマンドやコードは必ずコードブロックで示してください
- 不明点は正直に「確認が必要です」と伝え、公式ドキュメントの参照を勧めてください
- 初心者にも分かるよう、専門用語には簡単な補足を付けてください"""


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY が設定されていません。"}, 500

    client = anthropic.Anthropic(api_key=api_key)

    def generate():
        try:
            with client.messages.stream(
                model="claude-opus-4-5",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'type': 'error', 'text': 'APIキーが無効です。'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
