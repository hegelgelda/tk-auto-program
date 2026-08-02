# 他社買取データ 定時取得ワークフロー
#
# 【セットアップ手順】
# 1. このファイルを対象リポジトリの .github/workflows/fetch_competitor_prices.yml として保存
# 2. fetch_competitor_prices.py を同じリポジトリのルートに置く
# 3. 下記 cron を必要に応じて調整（デフォルトは日本時間 13:00）
# 4. リポジトリにpushすれば、GitHub Actionsが自動的に有効になります
#
# 実行結果（sotai.csv / psa.csv / box.csv）は data/ フォルダにコミットされます。
# リポジトリがPublicなので、以下の固定URLで常に最新版を外部から参照できます：
#   https://raw.githubusercontent.com/GITHUB_ORG/GITHUB_REPO/main/data/sotai.csv
#   https://raw.githubusercontent.com/GITHUB_ORG/GITHUB_REPO/main/data/psa.csv
#   https://raw.githubusercontent.com/GITHUB_ORG/GITHUB_REPO/main/data/box.csv
# （GITHUB_ORG / GITHUB_REPO は実際のユーザー名・リポジトリ名に置き換えてください）

name: 他社買取データ取得

on:
  schedule:
    # UTC基準。日本時間(JST=UTC+9)の13:00に実行するため UTC 4:00 を指定
    - cron: "0 4 * * *"
  workflow_dispatch: {}  # Actionsタブから手動実行するためのトリガー

jobs:
  fetch:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # 取得結果をリポジトリにコミットするため

    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 必要なライブラリをインストール
        run: pip install requests pandas

      - name: データ取得スクリプトを実行
        env:
          OUTPUT_DIR: data
        run: python fetch_competitor_prices.py

      - name: 取得結果をコミット
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/*.csv
          git diff --cached --quiet || git commit -m "他社買取データ更新 $(date -u +'%Y-%m-%d')"
          git push
