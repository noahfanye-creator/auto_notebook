import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# 权限范围：只需上传和管理由该应用创建的文件
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_refresh_token():
    """
    引导用户进行 OAuth2 授权并获取 Refresh Token
    """
    print("=== Google Drive OAuth 授权工具 ===")
    print("1. 请确保你已在 Google Cloud Console 创建了 '桌面应用' 类型的 OAuth 2.0 客户端 ID")
    print("2. 下载客户端配置 JSON 文件 (client_secret_xxx.json)")
    
    client_secret_path = input("\n请输入客户端 JSON 文件的路径 (或直接拖入): ").strip().strip("'").strip('"')
    
    if not os.path.exists(client_secret_path):
        print(f"错误: 找不到文件 {client_secret_path}")
        return

    try:
        # 创建授权流
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        
        # 启动本地服务器进行授权
        # 这会自动打开浏览器
        creds = flow.run_local_server(port=0)
        
        print("\n" + "="*50)
        print("✅ 授权成功！")
        print("="*50)
        print(f"GDRIVE_CLIENT_ID: {creds.client_id}")
        print(f"GDRIVE_CLIENT_SECRET: {creds.client_secret}")
        print(f"GDRIVE_REFRESH_TOKEN: {creds.refresh_token}")
        print("="*50)
        print("\n请将以上三个值分别填入 GitHub 仓库的 Secrets 中。")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    get_refresh_token()
