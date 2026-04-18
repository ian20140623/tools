# pinyin-drill

Mac 拼音練習遊戲 — 針對個人弱點自動加強。

## 用途

強化 Mac 原生拼音輸入法的兩個常見弱點：

1. **簡拼 + apostrophe 反射** — 第二字是裸母音（a/e/o 開頭）時必須用 `'` 分隔。例：方案 → `f'an`，不是 `fa`
2. **n/ng 前後鼻音辨識** — 台灣口音盲點。生/深、京/金、興/新

## 設計原則

- **純英文輸入**：遊戲只當字串比對器，IME 完全不碰。練習前請先切到 ABC 英文輸入法。
- **accepted 清單反映真實 IME 行為**：題庫只列 Mac 拼音 IME 真能產出該字的打法，不接受 IME 不吃的字串。
- **時間當弱點訊號**：不只看對錯。對但慢 → 自動加權重出。

## 檔案

- `drill.py` — 主程式
- `data/seed_nng_chars.json` — n/ng 單字題庫
- `data/seed_nng_words.json` — n/ng 詞題庫
- `data/seed_apostrophe.json` — apostrophe 反射詞題庫
- `stats.sqlite` — runtime 產生，紀錄每題 {hanzi, category, time_ms, correct, attempt_form}

## 依賴

Python 3.14+ 標準庫（sqlite3 / json / time / random），無外部依賴。

## 怎麼跑

```bash
# 自動模式（弱點優先）
python drill.py

# 指定類別
python drill.py --category apostrophe --count 20
python drill.py --category nng-char
python drill.py --category nng-word
```

## 判定邏輯

- 輸入 ∈ `accepted` → ✅ 對
- 輸入 = `preferred` → ✅✨ 滿分（最佳打法）
- 輸入 ∈ `accepted` 但 ≠ `preferred` → 對，提示更快打法
- 輸入 ∈ `trap` → ❌ 錯，標記為典型陷阱
- 其他 → ❌ 錯

## 題庫 schema

```json
{
  "hanzi": "方案",
  "category": "apostrophe",
  "accepted": ["fangan", "fang'an", "f'an", "fang'a", "f'a"],
  "preferred": "f'an",
  "tags": ["vowel-2nd", "fang-an"]
}
```

n/ng 題額外有 `trap` 欄位記常見錯法。

## 自適應權重

| 結果 | 下輪權重 |
|---|---|
| 錯 | ×2 |
| 對但慢（> per-category rolling median × 1.5） | ×1.5 |
| 對且快 | ×0.7 |
| 連續 3 次快對 | 移出熱池，偶爾回抽 |
