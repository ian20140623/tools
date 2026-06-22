# cco — 手機一鍵開 repo session

從手機（或任何 SSH 端）用**一個短指令**在指定 repo 開好一個 tmux session，自動以 `claude "/open-session"` 開場，attach 後即可遠端遙控。解決「人在手機上，不想在小螢幕打一長串 `tmux new -s … -c …` + 起 claude + 跑 open-session」。

## 用途

| 指令 | 行為 |
|------|------|
| `cco` | 列出執行中的 tmux session + 可用 repo 清單 |
| `cco <repo>` | 在 `~/Projects/<repo>` 開/接名為 `<repo>` 的 session，新建時自動跑 open-session |
| `cco <repo> <name>` | 同上但自訂 session 名（同一 repo 開多個 session 時用） |
| `cco -o <repo> [name]` | **只開不 attach**：建好 session + 跑 open-session 就回報退出（給 iOS 捷徑 / app 內 RC 接手用） |
| `cco -k <name>` | 收掉指定 session |

- **已存在同名 session → 直接 attach**，不重開、不重跑 open-session（idempotent）。
- **沒有 TTY 時自動只開不 attach**（如 iOS 捷徑、非互動 `ssh mini 'cco …'`）——等同 `-o`，不會卡在 attach。
- 有 TTY 時：已在 tmux 內 → `switch-client`；否則 `attach`（`exec` 讓 `ssh -t` 直接接管 TTY）。

## 典型用法：開了交給 app 內 RC 操控

主要情境是「只負責開」——session 建好、claude 起來、open-session 跑完，實際操控由手機 app 裡的 Remote Control 接手。所以不需要 attach：

- iOS **捷徑 App** → 「透過 SSH 執行指令」action，指令 `~/Projects/tools/cc/scripts/cc -o tools`（非互動 shell PATH 不含 homebrew，用絕對路徑）。放主畫面 / Siri，點一下就開好。
- 非互動 SSH 也行：`ssh mini 'cco -o tools'`（互動登入 shell 才有 homebrew PATH；純 `ssh host cmd` 用絕對路徑較保險）。

## 檔案

- `scripts/cc` — 主腳本（bash）。透過 symlink `cco` 對外。

## 依賴

- `tmux`（3.x，實測 3.6b）
- `claude` CLI 在 PATH
- repo 都在 `~/Projects/` 底下

## 安裝（每台機器）

```bash
ln -sf ~/Projects/tools/cc/scripts/cc /opt/homebrew/bin/cco
```

`/opt/homebrew/bin` 免 sudo 可寫，且在互動 shell PATH 第一順位。命名刻意避開 `cc`（系統 C 編譯器 clang）。

## 手機端怎麼用（批次、最少打字）

核心已經是「一個短詞」：`cco tools`、`cco ks`、`cco command-center`。再往零打字推：

- **Termius**：把常用 repo 各存成一個 Snippet（`cco tools` / `cco ks` …），開 mini host 後點一下即跑。
- **Blink Shell**：建 host alias `mini`，需要時 `ssh -t mini` 進互動 shell 打短詞；或設 host 啟動指令直接 `cco <repo>`。
- **Apple Shortcuts / 自動化**：`ssh` action 跑 `cco <repo> <name>`（非互動 shell PATH 不含 homebrew 時，用絕對路徑 `~/Projects/tools/cc/scripts/cc`）。

## 設計決策

- **為何 symlink 到 homebrew 而非 /usr/local/bin**：後者 root-owned 需 sudo；前者免權限、互動 shell 一定吃得到。
- **為何 `=name` 只用在 has-session / kill-session**：`=` 前綴強制 session 精確比對（避免 prefix 誤射）；但 tmux 對 **pane target**（send-keys / capture / attach / switch）不接受 `=`，那些一律用 plain `$name`（此時 exact session 已存在，tmux 比對優先 exact，無誤射風險）。
- **為何訊息裡變數要 `${repo}` 框起來**：全形標點（如 `（`）緊貼 `$repo` 會被 bash 吃進變數名 → unbound variable。
