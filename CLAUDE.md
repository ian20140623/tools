# CLAUDE.md — tools

> 共用指引見 [`../shared/CLAUDE.md`](../shared/CLAUDE.md) ^ck-d33d9c-0


## 核心原則
SRP / Information Hiding / OCP / No Silent Workaround(遇阻停下報告不繞路) / Explicit Intent(做之前先宣告 scope)。詳見 [shared/ARCHITECTURE_PRINCIPLES.md](../shared/ARCHITECTURE_PRINCIPLES.md)。

## 專案定位

跨專案共用小工具集合。每個工具服務所有 `C:\Projects\` 下的專案，不屬於任何單一專案。

## 環境需求

- Python 3.14+
- Node.js v24+
- Git
- 其他工具依各子工具需求，見 `env.machines.md` ^ck-d33d9c-2

## 新工具流程
^ck-d33d9c-3 ^ck-7ebbe5-3

### Phase 1: 討論

動手之前一定先討論，確保不重造輪子：

1. **痛點描述** — 什麼事情做起來痛？
2. **方案比較** — 列出可能的做法，比較優缺點
3. **選定方案** — 確認要用什麼技術/工具
4. **記入 ROADMAP** — 加到 `ROADMAP.md` 的 Incubator 或階段目標 ^ck-d33d9c-4

### Phase 2: 建置

確認要做之後：

1. 建立資料夾：`tools/<工具名>/`
2. 建立必要檔案：
   - `README.md` — 用途、檔案、依賴、怎麼跑
   - `log_chronological.md` — 開發記錄
   - `scripts/` — 腳本目錄
3. 如果有新的外部依賴(需要 install 的)，更新 `env.machines.md`
4. 更新 `tools/README.md` 的「現有工具」表格
5. 更新 `ROADMAP.md`（從 Incubator 移到階段目標，或標記完成） ^ck-d33d9c-5

### Phase 3: Commit

所有相關檔案放同一個 commit：
- 工具本身(資料夾、README、log、腳本)
- `tools/README.md`(更新表格)
- `ROADMAP.md`(更新狀態)
- `env.machines.md`(如果有新依賴) ^ck-d33d9c-6

## 建工具的規則

見 [README.md](README.md) 的「建新工具的規則」。 ^ck-d33d9c-7

## env.machines.md 更新時機

- **要更新**：工具引入了新的外部依賴(需要 `winget install` / `pip install` / 裝新 runtime)
- **不用更新**：純用既有環境就能跑(Python 標準庫、已安裝的 npm 套件等) ^ck-d33d9c-8
