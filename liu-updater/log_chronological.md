# Log — liu-updater

## 2026-03-17（週二）

### 13:31 [NB] 初版完成
- 痛點：liu.box 裡的時間字根（LLY/LY/TY/NY/NNY/TM）以前手動更新，容易忘
- 做法：Python 腳本讀 liu.box → 用當前日期算正確值 → 寫回 Dropbox + repo 備份
- 一次性清理：刪掉過時的 `TD; TD-SCDMA` 條目
- 順便刪了 TD（太久沒人提了）
