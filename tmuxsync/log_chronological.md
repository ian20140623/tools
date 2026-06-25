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
