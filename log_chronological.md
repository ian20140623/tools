# tools — 開發記錄

## 2026-03-17（一）

### 12:00 [NB] 初始建立 + espanso-projects 工具

- 建立 tools repo，定義 8 條建新工具的規則(README.md)
- 完成第一個工具 espanso(專案名稱快速輸入)
- 在 env.machines.md 記錄 Espanso 安裝，DT 待辦也記了

### 12:50 [NB] 定義新工具流程 + 基礎建設

- 討論新開工具的標準流程：先討論(痛點 → 方案比較 → 選定) → 再建置 → commit
- 建立 tools/CLAUDE.md：環境需求、新工具三階段流程、env.machines.md 更新時機
- 建立 tools/ROADMAP.md：用 Incubator 區放未成熟的想法，成熟後移入階段目標
- 建立 tools/log_chronological.md：tools 根目錄的開發記錄
- env.machines.md 更新規則：有新外部依賴才記，純用既有環境不用動

### 13:23 [NB] espanso 大幅升級：後綴觸發 + 雙輸入法同步

- espanso-projects 改名為 espanso
- trigger 從前綴 `;esp` 改為後綴 `esp;`（跟無蝦米打法一致）
- 經多輪迭代：縮寫+多長度 → 最短2字母 → 最終簡化為一律前4字母（短key會干擾無蝦米）
- gen_espanso.py 同時寫入 Espanso yml 和無蝦米 liu.box，兩個輸入法模式都能快速輸入專案名
- 撞名規則：各管各的（無蝦米保留手動中文條目，Espanso 全部生成）
- liu.box 備份進 repo，與 Dropbox 雙向同步
