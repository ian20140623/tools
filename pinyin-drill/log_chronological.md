# pinyin-drill — 開發記錄

## 2026-04-18（六）

### 16:20 [MAC-MINI] 開案：Mac 拼音練習遊戲

**痛點**
- Mac 原生拼音簡拼遇裸母音第二字會失敗（方案 `fa` → 發，不是方案）— 要靠 apostrophe `f'an` 才對
- n/ng 前後鼻音常打錯（台灣口音盲點）

**研究 Mac 拼音功能**
- 全拼 / 簡拼 / 拆字（Shift-Space）/ 筆畫（u 前綴）
- `v` 代 `ü`、apostrophe 分音節歧義
- Option-Tab 聲調篩選、Option-Shift-L 找輸入碼
- 模糊音設定（日常開、練習時關）
- 簡拼關鍵限制：第二字裸母音開頭時 `fa`、`ta` 會被當單音節

**設計決策**
- 純英文輸入 + 字串比對（遊戲不碰 IME，練習前切 ABC）
- accepted 清單反映真實 IME 行為（curated）
- 時間當弱點訊號（對但慢也加權重出，不只看對錯）
- 題型分字/詞兩層

**範圍**
- 三類題：apostrophe 詞、n/ng 字、n/ng 詞
- 種子各 30-40 題，之後邊用邊加
- Python 3.14 標準庫（sqlite3 + json + time），無外部依賴

**今天做到**
- ROADMAP.md 加階段目標 D
- 建 tools/pinyin-drill/ 資料夾 + data/ 子目錄
- README + log 建好

### 17:00~19:00 [MAC-MINI] MVP 建置 + 第一輪迭代 + v0.1.0 凍結

**產出**
- `drill.py` — Python 3.14 純標準庫（sqlite3 + json + time + statistics + random + argparse）
- 三份 seed JSON：apostrophe 30 / nng-char 56 / nng-word 35 = 121 題
- `VERSION` = 0.1.0

**功能**
- 加權抽題（錯 ×2、慢 ×1.5、快對 ×0.7）
- per-category rolling median 做「慢」的閾值
- 三種判定結果：preferred / accepted / wrong
- 嚴格模式 `--strict`：只收 preferred（練全拼用）；預設寬鬆（accept 全 IME-valid，實戰模式）
- SQLite 持久化 + session 結束報告
- `--stats` 只看歷史不練習

**迭代中的決策**
1. **accepted 清單要收 jianpin**：初版 nng-word 只收全拼，用戶實測發現 `zf` for 政府 被誤判為錯 → 補 jianpin 到 33 items
2. **注音 feedback 嘗試與還原**：加過 zhuyin 顯示當鷹架，用戶指「多一層 translation 違反快速反射目標」→ 完全還原，JSON 的 zhuyin 欄位也清除。教訓：鷹架不該強制，opt-in 才對
3. **規則層 vs 資料層分離**：嚴格度從資料 schema 搬到 CLI flag（`--strict`）。同一份題庫兩種玩法：寬鬆收所有 IME-valid（實戰）、嚴格只收 preferred（練習）

**設計哲學達成**
- 肌肉記憶 > 規則記憶：drill 不解釋理由，只重複（符合 muscle memory training 原則）
- SRP：題庫 JSON 純資料、drill.py 純邏輯，判定規則在 CLI flag 層
- No Silent Workaround：無繞路；Explicit Intent：scope 明確

**v0.1.0 的定位修正**
本 session 同時討論輸入法架構，結論是長期轉注音（母語層、跨裝置、容錯）。pinyin-drill 從「主力工具」降為「備援 + 已完成的實驗」。v0.1.0 凍結為完整 MVP，未來可能：
- 純備援使用（如果注音切換不順再回補）
- 或拆題庫搬到 zhuyin-drill（不建議，typing.tw 已覆蓋）
- 或 deprecate（Mac 注音熟了之後）

**沒做（out of scope）**
- git commit + tag（交 lcp 流程）
- 多字詞題庫擴充
- `--zhuyin` opt-in flag（未來若需要鷹架再加）
- 立即重抽錯題（肌肉記憶 immediate correction 機制，留給 v0.1.1+）

## 2026-04-19（日）

### 13:01 [MAC-MINI] v0.1.1 加 drill_nng.py 聚焦變體

**情境**：用戶反饋「拼音有練還是有差」— 注音評估期間仍想補 n/ng 知識缺口。現有 `drill.py --category nng-char --strict` 能達成，但參數多，使用門檻高。

**做了什麼**
- 新增 `drill_nng.py` — 薄包裝，固定 `--category nng-char --strict`，只暴露 `--count` 和 `--stats`
- VERSION 0.1.0 → 0.1.1
- README 加「v0.1.1 聚焦」一行說明

**設計決策**
- 用 wrapper script 而非新 CLI 模式：
  - 保持 drill.py 核心不動（OCP：對修改關閉，對擴充開放）
  - 未來若有其他聚焦場景（apostrophe only、複合），同模式可擴
- 不複製題庫資料，drill_nng.py 仍讀 seed_nng_chars.json
- 不另開 stats.sqlite（共享當前目錄的統計，累計紀錄跨模式有效）

**驗證**
- 4/4 grade path smoke test pass（`心/生 × preferred/wrong`）
- `--stats` mode 能正常跑

**脈絡**
用戶 2026-04-18 晚上試超注音 28 天，本次開 session 表示想平行繼續練拼音 n/ng。不影響注音評估，兩條路並行。

**沒做**
- 不改 drill.py 主檔（避免污染 v0.1.0 的 smoke test 基線）
- 不做 drill_apostrophe.py（等真有需要再說）
