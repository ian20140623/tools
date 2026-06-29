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
