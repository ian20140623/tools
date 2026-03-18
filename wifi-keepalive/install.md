# wifi-keepalive 安裝指南

## 1. 修改 SSID

編輯 `scripts/wifi-keepalive.ps1` 頂部：

```powershell
$SSID = "你的 iPhone 熱點名稱"
```

確認 SSID 名稱：

```cmd
netsh wlan show profiles
```

## 2. Task Scheduler 開機自啟

1. 開啟 Task Scheduler（工作排程器）
2. 建立基本工作 → 名稱：`wifi-keepalive`
3. 觸發程序：**使用者登入時**
4. 動作：**啟動程式**
   - 程式：`powershell.exe`
   - 引數：`-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\Ian\OneDrive\ClaudeProjects\tools\wifi-keepalive\scripts\wifi-keepalive.ps1"`
5. 完成後勾選「開啟內容對話方塊」，進階設定：
   - **不論使用者是否登入都執行** → 不要勾（用登入時即可）
   - **僅在 AC 電源時執行** → 取消勾選（用電池也要跑）
   - **設定** 分頁 → **如果工作執行時間超過** → 取消勾選（永久執行）

## 3. 裝置管理員網卡設定

網卡：Intel(R) Wi-Fi 6 AX200 160MHz → 進階分頁

| 設定 | 原廠值 | 建議值 | 目的 |
|------|--------|--------|------|
| MIMO 省電模式 | 自動 SMPS | 無 SMPS / 停用 | 關閉省電，維持連線穩定 |
| U-APSD 支援 | 啟用（推測） | 停用 | 關閉省電協商 |
| 漫遊積極度 | 中（推測） | 最低 | 避免主動跳到別的網路 |
| 傳輸電源 | 5. 最高 | 不改 | 已是最佳 |

備註：電源管理分頁在此 HP 筆電不存在，無法從那邊關閉省電。

## 4. 觀察流程

1. **基線期**（目前設定 + script）— 跑 3-5 天，記錄斷線頻率
2. **逐項回歸原廠** — 一次只改回一個設定，再觀察 3-5 天
3. **比較** — 斷線頻率明顯變多 → 維持建議值；沒差 → 改回原廠
4. **目標** — 找到最小必要調整

數據來源：`logs/disconnect_yyyy-MM-dd.csv`
