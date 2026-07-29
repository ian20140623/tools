# tmux — 開發記錄

### 2026-06-22 [Mac mini] 開案 — prefix 改 C-a，跨機手動同步

**痛點**：tmux 預設 prefix `C-b` 不順手，想全機統一改 `C-a`。

**方案決定**：選「簡單版 + 手動改」。
- 不做 SSH 一鍵推、不做 symlink、不做 deploy 腳本（討論過但 Sir 要簡單就好）。
- repo 放一份 `tmux.shared.conf` 當「抄寫範本」，每台機器自己貼進 `~/.tmux.conf` + reload。
- 各機 `~/.tmux.conf` 仍各自獨立（保留各機固有設定如 mouse / OSC52），範本只管共用部分。

**設定**（3 行）：
```
unbind C-b
set -g prefix C-a
bind C-a send-prefix
```

**取捨記錄**：prefix 改 `C-a` 後 shell 的 `Ctrl-a`（跳行首）被 tmux 攔截，要送字面 `Ctrl-a` 需連按兩次（send-prefix）。Sir 已知此摩擦仍選 `C-a`。

**已套用**：Mac mini ✅（`tmux show -g prefix` 驗證為 `prefix C-a`）。Air / NB 待手動套。

### 2026-06-29 [Air] 加一鍵切換 `bind -n C-o choose-tree`

**痛點**：原本切 session/window 是 `prefix(C-a)` → `w`，常「按半天沒反應」。

**根因**：失敗的不是 `C-a`（帶 Ctrl 修飾鍵，輸入法不攔），是後面那個**裸字母鍵 `w`**——中文輸入法還開著時被吃進注音/拼音組字區，tmux 收不到 → 靜默失敗。任何 `prefix + 字母` 都中這招。

**解法**：用 `bind -n`（不用 prefix）綁單一 Ctrl 組合鍵直達，一次解兩件事：(1) 從 6/9 鍵變一鍵；(2) Ctrl 組合鍵不被輸入法攔，中文開著也通。Sir 從 C-o / C-Space / F9 選 **`C-o`**（零設定、好按、輸入法免疫；代價：tmux 內蓋掉 shell/vim 的 `C-o`，幾乎無感）。

**設定**（加 1 行）：`bind -n C-o choose-tree -Zw`（沿用原 `prefix w` 行為）。

**驗證**：Air live `~/.tmux.conf` 加同行 → `tmux source-file` reload → `list-keys -T root` 確認 `C-o → choose-tree -Zw` 已註冊。VS Code 終端若攔 Ctrl 鍵再議。

### 2026-06-29 [Air] 更正：C-o 撞 Claude Code，改 `C-\`

**問題**：C-o 上線後 Sir 回報「沒用」+「Claude Code 本來就用很多 Ctrl+o」。

**兩個根因**：
1. **Claude Code 佔用 Ctrl+o** — Sir 在 tmux pane 裡也跑 claude，`bind -n C-o` 會把 Ctrl+o 從 claude 手上搶走，不能用。要留給 claude。
2. **「沒用」很可能是測錯地方** — tmux 綁定只在 tmux pane 內有效。Sir 多半在「VS Code 的 Claude Code 視窗」（非 tmux pane，`TMUX` 為空）按的 → tmux 管不到 → 鍵直接給 claude，看起來像「claude 在用 Ctrl+o」。教訓記下：tmux 鍵要在**真 tmux pane** 內測。

**改鍵**：Sir 從 prefix→Ctrl+w（2 鍵 bulletproof）/ F9 / `C-\` 選 **`C-\`**（真單鍵、claude 與 mac 版 VS Code 都沒佔、Ctrl 系免疫輸入法）。

**設定眉角**：tmux.conf 裡反斜線要寫**兩個** `bind -n C-\\ choose-tree -Zw`，`list-keys` 顯示為 `C-\\`。先在 live server 用 `tmux bind-key -n 'C-\'` 試出能註冊、再 scratch conf 驗 `C-\\` 寫法、最後寫進 `~/.tmux.conf` + 範本，reload 後 `list-keys` 確認生效（解掉測試綁定後單獨 source conf 仍出現 = conf 真有效）。

## 2026-07-29（三）

### 14:36 [Air] 切換鍵改為 prefix → Ctrl+w

- **why**：無 prefix 的 `Ctrl-\` 在 VS Code 內建終端會先被 VS Code 攔截，按鍵到不了 tmux；原方案無法涵蓋 Air 的實際使用環境。
- **決定**：改用 `Ctrl-a` 放開後再按 `Ctrl-w`。prefix 能可靠進入 tmux，第二鍵保留 Ctrl 修飾，避免中文輸入法吃掉裸字母 `w`；也不占用 Claude Code 的 `Ctrl-o`。
- **reload 相容性**：範本先 `unbind -n C-\\`，再註冊新綁定；否則已運行 server source 新設定後，舊的全域 `Ctrl-\` 仍會殘留。
- **取捨**：從單鍵退回兩段按鍵，但換得 VS Code、原生終端與 SSH 共用同一套操作。範本仍維持手動同步，不新增部署機制。
