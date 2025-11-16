# werkzeug_console_pin_bruteforce

このスクリプトは、ネットワーク上のターゲット（通常はFlaskアプリケーションのWerkzeugデバッグコンソール）の9桁のPINを総当たりで探索し、認証試行回数に上限（`"exhausted": true`）が設定されている場合に、**VMwareのゲストOSを強制的にリセット（再起動）**することで、試行回数カウンターのリセットを試みる自動化ツールです。

## ⚠️ 免責事項

このツールは、**セキュリティ研究**および**自己学習**を目的としています。本ツールの使用は、**必ず所有者から許可を得た環境**でのみ行ってください。不正なアクセスや悪用は厳しく禁じられています。本スリプトの使用によって生じたいかなる損害についても、作成者は一切の責任を負いません。

---

## 🚀 機能概要

* **PIN総当たり攻撃**: 9桁のPINを順番に試行します。
* **SECRET値の自動取得**: 最初のPOSTリクエストでデバッグコンソールから`SECRET`値を抽出し、後続の認証リクエストに使用します。
* **VMリセットによる制限回避**: レスポンスで`"exhausted": true`が返された場合、VMwareの`vmrun`ユーティリティを使用してVMを強制リセットし、試行回数カウンターのリセットを試みます。
* **ロギング機能**: すべての試行、エラー、VMの再起動イベントをコンソールとログファイル（`pin_bruteforce.log`）に記録します。
* **再起動後の継続**: VM再起動後、`SECRET`値が変更されている可能性を考慮して自動で再取得し、試行中のPINから再開します。

---

## 🔧 セットアップと依存関係

### 1. 依存関係のインストール

Pythonの`requests`ライブラリが必要です。

```bash
pip install requests
2. VMware vmrun の設定このスクリプトは、VMware Workstationに含まれる**vmrun.exe**ユーティリティを使用してVMを操作します。VMware WorkstationがホストOSにインストールされている必要があります。ターゲットVMの**.vmxファイルのフルパス**が必要です。⚙️ 設定手順スクリプト（例：pin_bruteforce.py）の以下のグローバル変数を、実行環境に合わせて編集してください。変数名説明設定例TARGET_URLターゲットデバッグコンソールのURL'http://192.168.126.130:3000/console'VMRUN_PATHvmrun.exeへのフルパス"C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmrun.exe"VMX_PATHターゲットVMの.vmxファイルへのフルパス"C:\\Users\\user\\Documents\\Virtual Machines\\MBSDCC2025\\MBSDCC2025.vmx"current_pin_num試行を開始する最初のPIN番号1 または中断した番号 (100000000など)MAX_PIN試行を終了する最大のPIN番号（9桁の最大値）999999999重要: VMRUN_PATHとVMX_PATHを正しく設定しないと、VM再起動機能は動作しません。▶️ 実行方法設定が完了したら、スクリプトを実行します。Bashpython pin_bruteforce.py
📋 ログの確認すべての動作はコンソールに表示されるとともに、pin_bruteforce.logファイルに記録されます。ログレベル内容CRITICALPIN認証に成功したとき。ERROR通信エラー、JSONエラー、パスエラーなど、処理を妨げる問題が発生したとき。WARNINGexhausted: Trueが返されたとき、またはvmrunがエラーコードを返したとき。INFO試行中のPIN、VM再起動の開始/完了、SECRET値の取得など、通常の進捗。ログファイルを監視することで、総当たり攻撃の進捗を追跡できます。Bash# Linux/macOSの場合
tail -f pin_bruteforce.log
