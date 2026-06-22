# log — cco

### 13:30 [MAC-MINI] cco v0.1.0 開案 — 手機一鍵開 repo session

**痛點**：人在手機上想用 SSH 進 mini 開工，但不想在小螢幕手打 `tmux new -s <name> -c ~/Projects/<repo>` + 起 `claude` + 跑 open-session 一長串。要的是「批次執行」——一個短指令全包。

**方案**：bash 腳本 `cc`（對外 symlink `cco`），`cco <repo> [name]`：

- 不存在 → `tmux new-session -d` 在 repo 目錄 + `send-keys 'claude "/open-session"'`，再 attach
- 已存在 → 直接 attach（idempotent，不重跑 open-session）
- `cco` 無參數 → 列執行中 session + 可用 repo；`cco -k <name>` → kill

**踩到的坑（實測修掉）**：
1. **`cc` 撞名** = 系統 C 編譯器 clang。改名 `cco`（claude-code-open）。
2. **全形括號吃變數**：`"… @ $repo（自動…"` 的 `（` 緊貼 `$repo` 被 bash 當變數名 → `repo�: unbound variable`。修：`${repo}` 框起來。
3. **`=name` 用在 pane target 失敗**：`send-keys -t "=name"` 報 `can't find pane`。tmux 的 `=`（精確比對）只吃 session target（has-session / kill-session）；pane target（send-keys / capture / attach / switch）要 plain `$name`。

**安裝**：symlink → `/opt/homebrew/bin/cco`（免 sudo、互動 shell PATH 第一順位）。`/usr/local/bin` 要 sudo 故不用。

**驗證**：新建+自動 open-session（capture-pane 看到 claude 起來跑 open_session.py）✓、重跑 attach 不重建 ✓、`-k` kill ✓、無參數總覽 ✓、爛 repo 擋掉 ✓。

**手機端**：核心已是一個短詞 `cco <repo>`。零打字靠 SSH app 的 snippet（Termius）/ host 啟動指令（Blink）/ Apple Shortcuts ssh action。待 Sir 定哪個 app 再給確切 snippet。

### 13:50 [MAC-MINI] cco：加「只開不 attach」模式 — 配合 app 內 RC 操控

**情境校準**：Sir 釐清「可以這樣開就好，因為 RC 就可以在 app 裡面操作了」——主路徑是**只負責開** session（claude + open-session 跑起來），實際操控交給手機 app 內的 Remote Control，不需要 cco 去 attach。

**改動**：
- 加 `-o` / `--open` 旗標：建好 session 就回報退出、不 attach。
- **自動偵測 TTY**：`[ ! -t 1 ]`（iOS 捷徑、非互動 `ssh host cmd`）時自動只開不 attach，不會卡在 `tmux attach` 等不到終端機。有 TTY 才 attach/switch。
- `repo="${1:?用法…}"` 防 `-o` 後缺 repo 爆 unbound。

**又踩一次全形括號坑**：新增的就緒訊息 `"… $name（未 attach…"` 又被 `（` 吃掉變數 → line 75 unbound。修 `${name}`。事後 `grep -P '\$\{?\w+\}?[^\x00-\x7F]'` 全檔掃過確認無裸接非 ASCII。

**驗證**：非互動觸發 → 開好 claude+open-session、回報就緒、exit 0、不卡 ✓；`-o` 既有 session → 報就緒 ✓；kill ✓。
