# tmuxsync — 跨機共用 tmux 設定

跨機器一致的 tmux 設定。**手動同步**：每台機器自己抄 + reload，不做 SSH / symlink / 自動部署。
（名稱 tmuxsync = tmux 設定的跨機同步；目前同步動作是手動抄寫範本，非自動部署。）

## 內容

| 檔案 | 用途 |
|------|------|
| [tmux.shared.conf](tmux.shared.conf) | 共用設定範本（目前：prefix 改 `C-a`） |

## 怎麼套用到一台新機器

1. 打開該機器的 `~/.tmux.conf`
2. 把 `tmux.shared.conf` 裡的設定貼進去
3. reload：
   ```bash
   tmux source-file ~/.tmux.conf   # 沒開 tmux 的話下次開自動生效
   ```
4. 驗證：`tmux show -g prefix` 應顯示 `prefix C-a`

## 注意

- prefix 改 `C-a` 後，shell 的 `Ctrl-a`（跳行首）會被 tmux 攔截。要送字面 `Ctrl-a` 給 shell：**連按兩次 `C-a`**（`send-prefix`）。
- 各機 `~/.tmux.conf` 仍各自獨立（含各機固有設定如 mouse / OSC52），本範本只是「共用部分的抄寫來源」。

## 已套用機器

- ✅ Mac mini（2026-06-22）
- ✅ Air（2026-06-23）
- — NB（退役中 Windows，tmux 不適用，不納入）
