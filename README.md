# tools — 跨專案共用小工具

放在這裡的工具服務所有 ClaudeProjects 專案，不屬於任何單一專案。 ^ck-1c69ad-0

## 建新工具的規則

1. **一個工具一個資料夾** — 不要散在 tools/ 根目錄
2. **每個工具要有 README.md** — 說明用途、檔案、依賴、怎麼跑
3. **每個工具要有 log_chronological.md** — 記錄開發過程、設計決策、迭代變更（格式同 `shared/LOG_GUIDE.md`）
4. **裝了就記** — 每台機器安裝後，在 `env.machines.md` 記錄版本與日期，確保雙機同步
5. **開機自啟** — 如果工具需要常駐，提供啟動腳本並加入 Windows Startup
6. **跨機器可用** — 腳本放 OneDrive 同步，路徑用相對路徑或環境變數，不寫死絕對路徑
7. **scripts/ + scripts/scratch/** — 每個工具自備，臨時腳本和實驗放 scratch/（命名規範同 `shared/CLAUDE.md` Scratch 規則）
8. **進 git + GitHub** — 版本控制，跨機器同步靠 git pull ^ck-ef4960-1

## 現有工具

| 資料夾 | 說明 |
|--------|------|
| [espanso/](espanso/) | 專案名稱快速輸入（Espanso + 無蝦米雙輸入法同步） |
| [liu-updater/](liu-updater/) | liu.box 時間字根自動更新（年度 + 季度） |
| [wifi-keepalive/](wifi-keepalive/) | iPhone 熱點 keep-alive + 斷線自動重連（PowerShell） |
| [pinyin-drill/](pinyin-drill/) | Mac 拼音練習遊戲（apostrophe 反射 + n/ng 辨識，弱點自動加強） |
^ck-507d2c-2
