"""
他社買取データ 定時取得スクリプト（分割・差分出力対応版）
─────────────────────────────────────
mocha0908.github.io/TCK-kaitori/data.json から sotai / psa / box の
3カテゴリを取得し、以下の3種類のファイルを保存する。

1. data/<カテゴリ>.csv
     全列入りの完全版（アーカイブ用・Git履歴用）。従来と同じ。

2. data/compact/<カテゴリ>_part1.csv, _part2.csv, ...
     Claude等の外部ツールが1回で読み切れるサイズ（800行ずつ、約50〜65KB）に
     分割した軽量版。列は name / rarity / price_a / price_a_minus / price_rush のみ
     （imgなどの長い列を除外してサイズを約半分に削減）。

3. data/<カテゴリ>_changes.csv
     前回実行時の完全版CSVと比較した差分。価格が変わった行・新規追加行・
     削除行だけを記録する。日々の値動き確認はこのファイルを見るだけでよい。

GitHub Actions から毎日実行される想定（fetch_competitor_prices.yml 参照）。
"""

import os
import csv
import requests
import pandas as pd

URL = "https://mocha0908.github.io/TCK-kaitori/data.json"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data")
COMPACT_DIR = os.path.join(OUTPUT_DIR, "compact")

CATEGORIES = ["sotai", "psa", "box"]
COMPACT_COLS = ["name", "rarity", "price_a", "price_a_minus", "price_rush"]
PRICE_COLS = ["price_a", "price_a_minus", "price_rush"]
CHUNK_ROWS = 800


def load_previous(category):
    """前回実行時の完全版CSVを読み込む（初回は空）。name列をキーにした辞書で返す"""
    path = os.path.join(OUTPUT_DIR, f"{category}.csv")
    if not os.path.exists(path):
        return {}
    prev = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            prev[row.get("name", "")] = row
    return prev


def write_changes(category, prev, current_df):
    """前回と今回を比較し、価格変動・新規・削除だけをCSVに書き出す"""
    changes = []
    current_names = set()

    for _, row in current_df.iterrows():
        name = str(row.get("name", ""))
        current_names.add(name)
        p = prev.get(name)
        if p is None:
            changes.append({
                "name": name, "change": "新規",
                **{f"old_{c}": "" for c in PRICE_COLS},
                **{f"new_{c}": row.get(c, "") for c in PRICE_COLS},
            })
        else:
            diffs = [c for c in PRICE_COLS if str(p.get(c, "")) != str(row.get(c, ""))]
            if diffs:
                changes.append({
                    "name": name, "change": "価格変動",
                    **{f"old_{c}": p.get(c, "") for c in PRICE_COLS},
                    **{f"new_{c}": row.get(c, "") for c in PRICE_COLS},
                })

    for name, p in prev.items():
        if name not in current_names:
            changes.append({
                "name": name, "change": "削除",
                **{f"old_{c}": p.get(c, "") for c in PRICE_COLS},
                **{f"new_{c}": "" for c in PRICE_COLS},
            })

    path = os.path.join(OUTPUT_DIR, f"{category}_changes.csv")
    fieldnames = ["name", "change"] + [f"old_{c}" for c in PRICE_COLS] + [f"new_{c}" for c in PRICE_COLS]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(changes)
    print(f"{category}_changes.csv: {len(changes)}件の変化")


def write_compact_chunks(category, df):
    """外部ツールが読み切れるサイズに分割した軽量版を書き出す"""
    cols = [c for c in COMPACT_COLS if c in df.columns]
    compact = df[cols]
    n_parts = 0
    for i in range(0, len(compact), CHUNK_ROWS):
        n_parts += 1
        part = compact.iloc[i:i + CHUNK_ROWS]
        path = os.path.join(COMPACT_DIR, f"{category}_part{n_parts}.csv")
        part.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"{category}: 分割版 {n_parts}ファイル")

    # 古い余分なパートが残らないよう削除（前回より件数が減った場合に対応）
    k = n_parts + 1
    while True:
        stale = os.path.join(COMPACT_DIR, f"{category}_part{k}.csv")
        if os.path.exists(stale):
            os.remove(stale)
            k += 1
        else:
            break


def fetch_and_save():
    res = requests.get(URL, headers={"Cache-Control": "no-cache"}, timeout=30)
    res.raise_for_status()
    data = res.json()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COMPACT_DIR, exist_ok=True)

    for category in CATEGORIES:
        df = pd.DataFrame(data.get(category, []))
        print(f"{category}: {len(df)}件")

        # 1) 差分（上書き前に前回分を読む）
        prev = load_previous(category)
        write_changes(category, prev, df)

        # 2) 完全版
        df.to_csv(os.path.join(OUTPUT_DIR, f"{category}.csv"), index=False, encoding="utf-8-sig")

        # 3) 分割軽量版
        write_compact_chunks(category, df)

    print("保存完了:", OUTPUT_DIR)


if __name__ == "__main__":
    fetch_and_save()
