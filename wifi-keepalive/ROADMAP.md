# ROADMAP — wifi-keepalive
^ck-c0c1f2-0

## 痛點

iPhone 個人熱點連 Windows 筆電，約 30-60 分鐘自動斷線（iOS 省電機制已知問題）。斷線後需手動重連，影響工作流。 ^ck-d99c33-1

## 理想功能

- 背景常駐，斷線秒回，不需人工介入
- 斷線 log 可量化分析，驗證網卡設定調整效果
- 資源極低，開機自啟，跑了不用管 ^ck-14e402-2

## 階段目標

- [ ] A. 核心功能 — keep-alive ping + 斷線自動重連 + CSV log ← 本輪
- [ ] B. 穩定運行 — 修正 SSID Unicode 比對、Task Scheduler 開機自啟、實測驗證
- [ ] C. 觀察分析 — 基線期數據收集，逐項回歸網卡設定，找最小必要調整 ^ck-5198a9-3

## 現況

A 腳本已寫完，發現 netsh 輸出 Unicode 撇號（U+2019）被轉成 `?`，SSID 比對失敗，修正中。 ^ck-424ef5-4
