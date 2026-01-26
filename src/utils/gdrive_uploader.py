import os
import glob
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from src.utils.logger import get_logger

logger = get_logger(__name__)

def upload_to_gdrive(report_dir: str):
    """
    将生成的 PDF 报告上传到 Google Drive
    """
    client_id = os.environ.get("GDRIVE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN", "").strip()
    folder_id = os.environ.get("GDRIVE_FOLDER_ID", "").strip()

    if not all([client_id, client_secret, refresh_token, folder_id]):
        logger.warning("⚠️  未配置 Google Drive OAuth 信息，跳过上传。")
        return

    try:
        # 使用 Refresh Token 构建凭证
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        
        drive = build("drive", "v3", credentials=creds)

        # 校验文件夹
        try:
            folder_info = drive.files().get(fileId=folder_id, fields="id,name", supportsAllDrives=True).execute()
            logger.info(f"📁 目标文件夹: {folder_info.get('name', folder_id)}")
        except Exception as e:
            logger.error(f"❌ 无法访问 Google Drive 文件夹: {e}")
            return

        pdfs = sorted(glob.glob(os.path.join(report_dir, "*.pdf")))
        if not pdfs:
            logger.info("ℹ️  未找到待上传的 PDF 文件")
            return

        for path in pdfs:
            name = os.path.basename(path)
            meta = {"name": name, "parents": [folder_id]}
            media = MediaFileUpload(path, mimetype="application/pdf", resumable=True)
            try:
                f = drive.files().create(
                    body=meta,
                    media_body=media,
                    fields="id,name",
                    supportsAllDrives=True,
                ).execute()
                logger.info(f"✅ 上传成功: {name} -> {f.get('id')}")
            except HttpError as e:
                logger.error(f"❌ 上传失败: {name} (HTTP {e.resp.status})")
                
        logger.info(f"📊 共上传 {len(pdfs)} 个文件到 Google Drive")

    except Exception as e:
        logger.error(f"❌ Google Drive 上传过程发生异常: {e}")
