"""
競合CSVを Google Drive にアップロード（サービスアカウント使用）
──────────────────────────────────────────
fetch_competitor_prices.py で生成した sotai.csv / psa.csv / box.csv を、
指定したGoogle Driveフォルダにアップロード（既存なら上書き更新）する。

このフォルダをClaudeプロジェクトの「コンテキスト」に追加しておけば、
毎日自動で最新の他社価格データが反映される。

【事前準備】
1. Google Cloud Consoleでサービスアカウントを作成し、
   「Google Drive API」を有効化してJSON鍵をダウンロードする
   （own_price_sheet.py で使ったものと同じサービスアカウントを流用してOK）

2. アップロード先にしたいGoogle Driveのフォルダを作成し、
   その「共有」設定でサービスアカウントのメールアドレスを
   「編集者」として追加する
   （フォルダはClaudeで使うGoogleアカウント自身が所有 or
    そのアカウントがアクセスできるフォルダにすること）

3. フォルダを開いたときのURLから、フォルダIDを控えておく
   https://drive.google.com/drive/folders/【ここがフォルダID】

必要なライブラリ:
    pip install google-api-python-client google-auth
"""

import os
import glob

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
SOURCE_DIR = os.environ.get("OUTPUT_DIR", "data")


def _get_drive_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _find_existing_file(service, filename, folder_id):
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    res = service.files().list(q=query, fields="files(id, name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def upload_or_update(filepath, folder_id):
    service = _get_drive_service()
    filename = os.path.basename(filepath)
    media = MediaFileUpload(filepath, mimetype="text/csv")

    existing_id = _find_existing_file(service, filename, folder_id)
    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
        print(f"更新: {filename}")
    else:
        metadata = {"name": filename, "parents": [folder_id]}
        service.files().create(body=metadata, media_body=media, fields="id").execute()
        print(f"新規作成: {filename}")


def main():
    if not FOLDER_ID:
        raise RuntimeError("環境変数 GOOGLE_DRIVE_FOLDER_ID が設定されていません。")

    csv_files = glob.glob(os.path.join(SOURCE_DIR, "*.csv"))
    if not csv_files:
        print(f"{SOURCE_DIR} にCSVが見つかりませんでした。")
        return

    for path in csv_files:
        upload_or_update(path, FOLDER_ID)


if __name__ == "__main__":
    main()
