"""
他社買取データ 定時取得スクリプト
─────────────────────────
mocha0908.github.io/TCK-kaitori/data.json から sotai / psa / box の
3カテゴリを取得し、それぞれCSVに保存する。

Colab版から、Colab固有の処理（files.download等）を除いただけの内容。
GitHub Actions等の自動実行環境でそのまま動く。

出力先: OUTPUT_DIR で指定したフォルダに
  sotai.csv, psa.csv, box.csv
を上書き保存する。
"""

import os
import requests
import pandas as pd

URL = "https://mocha0908.github.io/TCK-kaitori/data.json"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", ".")  # GitHub Actions側で変更可能


def fetch_and_save():
    res = requests.get(URL, headers={"Cache-Control": "no-cache"}, timeout=30)
    res.raise_for_status()
    data = res.json()

    df_sotai = pd.DataFrame(data.get("sotai", []))
    df_psa = pd.DataFrame(data.get("psa", []))
    df_box = pd.DataFrame(data.get("box", []))

    print("sotai:", len(df_sotai), "件")
    print("psa  :", len(df_psa), "件")
    print("box  :", len(df_box), "件")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_sotai.to_csv(os.path.join(OUTPUT_DIR, "sotai.csv"), index=False, encoding="utf-8-sig")
    df_psa.to_csv(os.path.join(OUTPUT_DIR, "psa.csv"), index=False, encoding="utf-8-sig")
    df_box.to_csv(os.path.join(OUTPUT_DIR, "box.csv"), index=False, encoding="utf-8-sig")

    print("保存完了:", OUTPUT_DIR)


if __name__ == "__main__":
    fetch_and_save()
