# espanso-projects — 開發記錄

## 2026-03-17（一）

### 12:00 [NB] 初始建立

- **起因**：在 Claude Code 聊天中引用其他專案名要打全名太麻煩
- **方案選擇**：評估過 VS Code snippets（只在編輯器內）、zoxide（只跳目錄）、AutoHotkey（Windows 限定腳本），最後選 Espanso（跨平台、YAML 設定、AI 好維護）
- **核心設計**：`gen_espanso.py` 掃 `ClaudeProjects/` 自動生成 triggers，不維護靜態列表
- **兩種 trigger**：首字母縮寫（`;ks`）+ 前 4 字母（`;know`）
- **撞名處理**：同一 trigger 對應多個專案時，生成 Espanso choice 選單讓用戶選
- **數字開頭**：`2026-disneysea` 跳過數字部分，用 `disn` 生成 trigger
- **子專案**：透過 `espanso_projects.json` 設定要掃的子資料夾（如 `trip-doc-generator/trips`）
- **開機自啟**：`start_espanso.bat` 先跑 gen 再啟動 Espanso，放 Windows Startup
- **tools/ 憲法**：建立 `tools/README.md`，8 條規則（資料夾隔離、README、log、env 記錄、scripts/scratch 等）
- **DT 待辦**：記在 `env.machines.md`，等回家裝
