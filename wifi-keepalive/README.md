# wifi-keepalive

iPhone 個人熱點連 Windows 筆電，約 30-60 分鐘會自動斷線（iOS 省電機制已知問題）。此工具背景常駐，keep-alive ping 防斷線 + 斷線自動重連。 ^ck-83d978-0

## 檔案

| 檔案 | 說明 |
|------|------|
| scripts/wifi-keepalive.ps1 | 主程式：ping + 偵測 + 重連 + log |
| install.md | Task Scheduler 開機自啟設定 + 裝置管理員網卡設定 |
| logs/ | 斷線 CSV log（gitignore） |
| log_chronological.md | 開發記錄 |
^ck-f60e67-1

## 怎麼跑

```powershell ^ck-208ef7-2
# 手動執行
powershell -ExecutionPolicy Bypass -File scripts/wifi-keepalive.ps1 ^ck-67fe9b-3

# 開機自啟 → 見 install.md
``` ^ck-8d197c-4

## 設定

腳本頂部變數：

| 變數 | 預設 | 說明 |
|------|------|------|
| $SSIDs | @("Kyle's iPhone (2)") | iPhone 熱點 SSID，可放多個 |
| $PingIntervalSec | 10 | 每次檢查間隔（秒） |
| $PingTimeoutMs | 2000 | ping 逾時（毫秒） |
| $FailThreshold | 3 | 連續 ping 失敗幾次才判定斷線 |
| $LogDir | 腳本同層 ../logs | CSV log 路徑 |
^ck-99e803-5

## 依賴

無。PowerShell + netsh，Windows 內建。 ^ck-289569-6

## 使用環境

僅 NB（HP Dragonfly, Windows 11, Intel Wi-Fi 6 AX200 160MHz） ^ck-88e0c6-7
