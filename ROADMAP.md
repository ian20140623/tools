# ROADMAP — tools

## 痛點

跨專案重複操作耗時，手動做容易出錯或遺漏。需要一組小工具來自動化這些日常瑣事。

## 理想功能

- 常用操作一鍵完成，不用記指令
- 工具跨機器可用，裝好就能跑
- 新工具有標準流程，不用每次從零想

## 階段目標

- [x] A. espanso — 專案名稱快速輸入（雙輸入法同步：Espanso + 無蝦米 liu.box）
- [x] B. liu-updater — liu.box 時間字根自動更新（年度 + 季度，臨近2季度原則）
- [ ] C. wifi-keepalive — iPhone 熱點 keep-alive + 斷線自動重連（PowerShell，僅 NB）

## Incubator

*還在想的工具點子，經過討論後移入階段目標。*

- **單一來源架構** — 新專案名直接寫進 liu.box 當 source of truth，Espanso yml 從 liu.box 轉出。撞名時通知 Ian 並在 liu.box 下方註記，不加新快鍵不干擾原有條目
- **Espanso + liu.box 同步腳本** — 自動化 Dropbox ↔ repo 備份流程，手動改 liu.box 後一鍵同步回 repo

## 現況

A、B 完成。C 建置中（腳本完成，待實測）。tools 基礎建設(README 規則、CLAUDE.md 流程、ROADMAP)已建立。liu.box 已備份進 repo。
