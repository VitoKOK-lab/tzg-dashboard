# 🎯 TZG 儀表板 - 快速開始（恢復版）

## 📌 您需要知道的最重要的3件事

### 1️⃣ 項目是什麼

TZG 儀表板是一個 **自動化的月度營業報告系統**，可以：
- 📊 生成日報表（`dashboard_latest.html`） - 每日營收、訂單、業務分析
- 📈 生成月報表（`monthly_review.html`） - 月度完整業務分析（9頁）
- 🔄 自動從 Shopline API 下載最新訂單資料
- 📱 在瀏覽器中查看（無需其他軟體）

### 2️⃣ 恢復只需 4 個命令

```bash
# Step 1: 進入項目目錄
cd /path/to/tzg-dashboard

# Step 2: 安裝依賴（首次恢復時）
pip install -r requirements.txt

# Step 3: 生成報表
python3 generate_daily.py
python3 generate_monthly_review.py

# Step 4: 開啟報表
open output/dashboard_latest.html      # 日報表
open output/monthly_review.html        # 月報表
```

### 3️⃣ 完整指南在哪裡

- **新手指南**：打開 [`RECOVERY_GUIDE.md`](./RECOVERY_GUIDE.md)
- **驗證清單**：檢查 [`VERIFICATION_REPORT.md`](./VERIFICATION_REPORT.md)
- **這個檔案**：[`README_RECOVERY.md`](./README_RECOVERY.md)

---

## 🚀 快速恢復（各種場景）

### 情景 A：在同一台電腦上，但不同位置

```bash
cd /new/path/tzg-dashboard
python3 generate_daily.py && python3 generate_monthly_review.py
open output/dashboard_latest.html
```

**恢復時間：1-2 分鐘** ⏱️

---

### 情景 B：在全新的電腦上

```bash
# 1. Clone 專案
git clone <repo-url>
cd tzg-dashboard

# 2. 檢查 Python（必須 3.7+）
python3 --version

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 生成報表
python3 generate_daily.py
python3 generate_monthly_review.py

# 5. 開啟
open output/dashboard_latest.html
```

**恢復時間：4-6 分鐘** ⏱️

---

### 情景 C：只想查看報表，不重新生成

```bash
open output/dashboard_latest.html      # 日報表
open output/monthly_review.html        # 月報表
```

**恢復時間：5 秒** ⏱️

---

## 📊 項目結構速查表

```
tzg-dashboard/
├── 📄 README_RECOVERY.md          ← 您在這裡
├── 📄 RECOVERY_GUIDE.md           ← 完整恢復指南
├── 📄 VERIFICATION_REPORT.md      ← 驗證清單
│
├── 🐍 generate_daily.py            ← 生成日報表
├── 🐍 generate_monthly_review.py   ← 生成月報表
├── 🐍 auto_shopline.py             ← 同步 Shopline 資料
├── 📝 requirements.txt             ← 依賴清單
│
├── 📂 data/
│   ├── TZG_2026-01_orders.csv     ← 1月訂單
│   ├── TZG_2026-02_orders.csv     ← 2月訂單
│   ├── TZG_2026-03_orders.csv     ← 3月訂單
│   ├── TZG_2026-04_orders.xlsx    ← 4月訂單
│   ├── shopline_*.xlsx            ← 最新 Shopline 下載
│   └── templates/
│       └── monthly_review_template.html  ← 月報表模板
│
└── 📂 output/
    ├── dashboard_latest.html      ← 最新日報表 ⭐
    ├── monthly_review.html        ← 最新月報表 ⭐
    └── dashboard_YYYY-MM-DD_*.html ← 備份版本
```

---

## ⚡ 常用命令速查表

| 需求 | 命令 |
|------|------|
| 生成日報表 | `python3 generate_daily.py` |
| 生成月報表 | `python3 generate_monthly_review.py` |
| 同時生成兩個 | `python3 generate_daily.py && python3 generate_monthly_review.py` |
| 從 Shopline 同步資料 | `python3 auto_shopline.py` |
| 清理舊檔案 | `python3 cleanup_old_downloads.py` |
| 查看日報表 | `open output/dashboard_latest.html` |
| 查看月報表 | `open output/monthly_review.html` |

---

## 🔍 環境檢查（一鍵驗證）

執行此命令來確認環境已準備好：

```bash
python3 << 'EOF'
import sys
print(f"✅ Python: {sys.version.split()[0]}")
try:
    import pandas, openpyxl, jinja2
    print("✅ 依賴：已安裝")
except ImportError as e:
    print(f"❌ 缺少: {e}")
EOF
```

預期輸出：
```
✅ Python: 3.7.0（或更新版本）
✅ 依賴：已安裝
```

---

## ⚙️ 設定與自訂

### 修改年度目標

編輯 `annual_plan.json`：
```json
{
  "2026": {
    "revenue_target": 4500000,
    "order_target": 900,
    ...
  }
}
```

### 修改報表樣式

編輯 `data/templates/monthly_review_template.html`：
```html
:root {
  --primary: #FF6B6B;      /* 改變主色 */
  --secondary: #4ECDC4;    /* 改變輔色 */
}
```

### 修改資料來源

編輯 `auto_shopline.py` 中的 API 設定

---

## 📱 在不同裝置查看

### 電腦（推薦）

```bash
# macOS
open output/dashboard_latest.html

# Windows (WSL)
explorer.exe output/dashboard_latest.html

# Linux
xdg-open output/dashboard_latest.html
```

### 在線分享

1. 上傳 `output/monthly_review.html` 到 Google Drive / OneDrive
2. 右鍵 → 開放連結
3. 同事可用瀏覽器直接查看

### 自動上線到 GitHub Pages

專案支援部署到 GitHub Pages（詳見 `RECOVERY_GUIDE.md`）

---

## 🆘 遇到問題？

### ❌ "找不到 Python"

```bash
# macOS
brew install python3

# Ubuntu
sudo apt-get install python3 python3-pip

# 驗證
python3 --version
```

### ❌ "缺少依賴"

```bash
pip install -r requirements.txt
```

### ❌ "找不到資料檔案"

```bash
# 從 Shopline 重新下載
python3 auto_shopline.py

# 或查看完整恢復指南
cat RECOVERY_GUIDE.md
```

### ❌ "報表是空白的"

```bash
# 1. 清除瀏覽器快取 (Ctrl+Shift+Delete 或 Cmd+Shift+Delete)
# 2. 強制重新整理 (Ctrl+Shift+R 或 Cmd+Shift+R)
# 3. 重新生成報表
python3 generate_daily.py
python3 generate_monthly_review.py

# 4. 重新開啟瀏覽器
```

### 更多幫助

完整的故障排除指南請見：[`RECOVERY_GUIDE.md`](./RECOVERY_GUIDE.md#-常見問題排查)

---

## ✅ 驗證清單

若要確認恢復成功，檢查：

- [ ] ✅ Python 3.7+ 已安裝
- [ ] ✅ `pip list` 顯示 pandas, openpyxl, jinja2
- [ ] ✅ 執行 `python3 generate_daily.py` 無錯誤
- [ ] ✅ 執行 `python3 generate_monthly_review.py` 無錯誤
- [ ] ✅ `output/dashboard_latest.html` 已生成
- [ ] ✅ `output/monthly_review.html` 已生成
- [ ] ✅ 瀏覽器可開啟報表
- [ ] ✅ 報表中可看到本月資料

全部通過？恭喜！🎉 您已成功恢復專案

---

## 📚 進階文檔

| 文檔 | 用途 |
|------|------|
| [`RECOVERY_GUIDE.md`](./RECOVERY_GUIDE.md) | 完整分步驟恢復指南（適合複雜場景） |
| [`VERIFICATION_REPORT.md`](./VERIFICATION_REPORT.md) | 驗證清單（確認環境就緒） |
| [`README_RECOVERY.md`](./README_RECOVERY.md) | 本檔案（快速入門） |

---

## 🎯 下一步

### 首次使用

1. 閱讀本檔案（已完成 ✅）
2. 執行恢復命令（4 個命令，2 分鐘）
3. 開啟報表查看

### 日常使用

```bash
# 每日早上執行（自動化排程已配置）
python3 generate_daily.py

# 月末執行
python3 generate_monthly_review.py
```

### 進階設定

詳見 [`RECOVERY_GUIDE.md`](./RECOVERY_GUIDE.md#-自動化排程)：
- 配置 macOS 排程任務
- 配置 Linux cron 任務
- 配置 Windows 任務排程

---

## 📞 快速參考

| 需要... | 執行... |
|-------|--------|
| 生成今日報表 | `python3 generate_daily.py` |
| 生成月度報表 | `python3 generate_monthly_review.py` |
| 下載最新訂單 | `python3 auto_shopline.py` |
| 檢查環境 | `python3 -c "import pandas, openpyxl, jinja2; print('✅')"` |
| 查看日報表 | `open output/dashboard_latest.html` |
| 查看月報表 | `open output/monthly_review.html` |
| 恢復整個專案 | 見上面「快速恢復」部分 |

---

## 🎓 最後提醒

這個項目已經過完整驗證 ✅，可以：

✅ **安全恢復**：所有必要檔案都齊全  
✅ **快速啟動**：4 個命令，4-6 分鐘  
✅ **自動執行**：支援排程任務  
✅ **離線使用**：無需網路（除非更新 Shopline 資料）  
✅ **多地點**：可在任何地方、任何電腦上運作  

---

**準備好恢復了嗎？** 👇

```bash
cd /path/to/tzg-dashboard
pip install -r requirements.txt
python3 generate_daily.py && python3 generate_monthly_review.py
open output/dashboard_latest.html
```

**恢復時間：4-6 分鐘** ⏱️

---

**最後更新：2026-05-07**  
**版本：1.0 - Ready for Recovery**  
**狀態：✅ 已驗證，已簽核**
