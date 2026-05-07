# 📋 TZG 儀表板 - 快速恢復指南

此文檔說明如何在新電腦或新資料夾中快速恢復整個項目。

---

## 🎯 30秒快速恢復

```bash
# 1. 進入項目目錄
cd /path/to/tzg-dashboard

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 重新生成所有報表
python3 generate_daily.py
python3 generate_monthly_review.py

# 4. 開啟瀏覽器查看
# output/dashboard_latest.html  (日報表)
# output/monthly_review.html    (月報表)
```

---

## 📚 完整恢復步驟

### 前置需求

| 項目 | 要求 |
|------|------|
| Python | 3.7+ |
| 必要套件 | pandas, openpyxl, jinja2 |
| 系統 | macOS / Linux / Windows (WSL) |
| 磁碟空間 | 至少 50 MB |

### Step 1: 複製項目

```bash
# 從 GitHub 複製（如果是首次）
git clone https://github.com/your-username/tzg-dashboard.git
cd tzg-dashboard

# 或者，進入已有的項目目錄
cd /path/to/existing/tzg-dashboard
```

### Step 2: 檢查環境

```bash
# 驗證 Python 版本
python3 --version  # 需要 3.7 以上

# 驗證項目結構
ls -la
# 應該看到：
# - generate_daily.py
# - generate_monthly_review.py
# - data/              (資料檔案)
# - output/            (輸出檔案)
# - requirements.txt
```

### Step 3: 安裝依賴

```bash
# 在項目根目錄執行
pip install -r requirements.txt

# 驗證安裝成功
python3 -c "import pandas, openpyxl, jinja2; print('✅ 所有依賴已安裝')"
```

### Step 4: 準備資料檔案

項目需要以下資料檔案（已包含在 `/data` 目錄）：

```
data/
├── TZG_2025_orders.csv           (1.83 MB) - 2025年訂單歷史
├── TZG_2026-01_orders.csv        (0.31 MB) - 1月訂單
├── TZG_2026-02_orders.csv        (0.54 MB) - 2月訂單
├── TZG_2026-03_orders.csv        (0.54 MB) - 3月訂單
├── TZG_2026-04_orders.xlsx       (1.54 MB) - 4月訂單
├── shopline_20260501_to_*.xlsx   (0.63 MB) - 最近 Shopline 下載
└── templates/
    └── monthly_review_template.html      - 月報表模板
```

**若缺少資料檔案：**
- 手動從 Shopline API 下載：執行 `python3 auto_shopline.py`
- 從備份恢復：檢查 git history 中的舊版本

### Step 5: 執行生成腳本

```bash
# 生成日報表（今日資料）
python3 generate_daily.py
# 輸出：output/dashboard_latest.html

# 生成月報表（月度匯總）
python3 generate_monthly_review.py
# 輸出：output/monthly_review.html
```

### Step 6: 驗證輸出

```bash
# 檢查輸出檔案是否生成
ls -lah output/*.html

# 預期結果：
# - output/dashboard_latest.html    (~100 KB)
# - output/monthly_review.html      (~190 KB)
# - 若干備份版本 (*.html 時間戳)
```

### Step 7: 查看報表

```bash
# macOS
open output/dashboard_latest.html
open output/monthly_review.html

# Linux
xdg-open output/dashboard_latest.html
xdg-open output/monthly_review.html

# Windows (WSL)
explorer.exe output/dashboard_latest.html
explorer.exe output/monthly_review.html
```

---

## 🔧 常見問題排查

### ❌ "找不到 Python"

```bash
# 安裝 Python 3.7+
# macOS
brew install python3

# Ubuntu
sudo apt-get install python3 python3-pip

# 驗證安裝
python3 --version
```

### ❌ "ModuleNotFoundError: No module named 'pandas'"

```bash
# 重新安裝依賴
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 或手動安裝
pip3 install pandas openpyxl jinja2
```

### ❌ "找不到資料檔案"

```bash
# 檢查 data/ 目錄
ls -la data/

# 若缺少檔案，執行 Shopline 同步
python3 auto_shopline.py

# 或從 git 恢復
git restore data/
```

### ❌ "報表無法開啟或顯示空白"

```bash
# 清空瀏覽器快取
# Chrome: Ctrl+Shift+Delete (或 Cmd+Shift+Delete)
# Safari: 開發 > 清空所有快取
# Firefox: Ctrl+Shift+Delete

# 強制刷新瀏覽器
# Chrome/Firefox: Ctrl+Shift+R (或 Cmd+Shift+R)
# Safari: Cmd+Option+R

# 重新生成報表
python3 generate_daily.py
python3 generate_monthly_review.py
```

### ❌ "腳本執行出錯"

```bash
# 1. 檢查 Python 語法
python3 -m py_compile generate_daily.py generate_monthly_review.py

# 2. 查看完整錯誤訊息
python3 -u generate_daily.py 2>&1 | head -50

# 3. 驗證資料格式（CSV/XLSX）
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/TZG_2026-04_orders.csv')
print(f"✅ 資料檔案正常：{len(df)} 列")
print(df.columns.tolist())
EOF
```

---

## 📊 完整恢復驗證清單

執行以下命令進行完整驗證：

```bash
#!/bin/bash
echo "🔍 TZG Dashboard 恢復驗證"
echo "================================"

# 1. 檢查 Python
echo "✓ Python 版本："
python3 --version

# 2. 檢查依賴
echo "✓ 檢查依賴..."
python3 -c "import pandas, openpyxl, jinja2; print('  ✅ 所有依賴已安裝')" 2>&1 || echo "  ❌ 缺少依賴，執行: pip install -r requirements.txt"

# 3. 檢查檔案結構
echo "✓ 檢查檔案結構..."
test -f generate_daily.py && echo "  ✅ generate_daily.py" || echo "  ❌ 缺少 generate_daily.py"
test -f generate_monthly_review.py && echo "  ✅ generate_monthly_review.py" || echo "  ❌ 缺少 generate_monthly_review.py"
test -d data && echo "  ✅ data/ 目錄" || echo "  ❌ 缺少 data/ 目錄"
test -d data/templates && echo "  ✅ data/templates/" || echo "  ❌ 缺少 data/templates/"

# 4. 檢查資料檔案
echo "✓ 檢查資料檔案..."
test -f "data/TZG_2026-01_orders.csv" && echo "  ✅ TZG 訂單資料" || echo "  ⚠️  需要下載訂單資料"
test -f "data/shopline_*.xlsx" && echo "  ✅ Shopline 資料" || echo "  ⚠️  需要下載 Shopline 資料"

# 5. 檢查模板
echo "✓ 檢查報表模板..."
test -f "data/templates/monthly_review_template.html" && echo "  ✅ 月報表模板" || echo "  ❌ 缺少模板"

echo "================================"
echo "✅ 恢復驗證完成！"
```

---

## 🚀 快速啟動命令集

### 僅生成日報表
```bash
python3 generate_daily.py
```

### 僅生成月報表
```bash
python3 generate_monthly_review.py
```

### 同時生成兩個報表
```bash
python3 generate_daily.py && python3 generate_monthly_review.py
```

### 清理舊備份檔案
```bash
python3 cleanup_old_downloads.py   # 清理 Shopline 舊檔
rm -f output/dashboard_2*.html      # 清理 HTML 備份（保留 latest）
```

### 從 Shopline API 同步最新資料
```bash
python3 auto_shopline.py
```

---

## 📁 完整檔案說明

### 核心腳本

| 檔案 | 用途 | 執行時機 |
|------|------|---------|
| `generate_daily.py` | 生成日報表 HTML | 每日執行 |
| `generate_monthly_review.py` | 生成月報表 HTML | 月末執行 |
| `auto_shopline.py` | 從 Shopline API 下載訂單 | 定期執行 |
| `cleanup_old_downloads.py` | 清理舊 Shopline 檔案 | 需要時執行 |

### 資料檔案

| 目錄 | 內容 | 來源 |
|------|------|------|
| `data/TZG_*.csv` | 月度訂單彙總 | 手動上傳或 Shopline API |
| `data/shopline_*.xlsx` | 最新訂單詳情 | Shopline API (`auto_shopline.py`) |
| `data/templates/` | HTML 模板 | 版本控制 |

### 輸出檔案

| 檔案 | 內容 | 用途 |
|------|------|------|
| `output/dashboard_latest.html` | 日報表（當日資料） | 日常查看 |
| `output/dashboard_YYYY-MM-DD_HHMMSS.html` | 日報表備份 | 恢復用 |
| `output/monthly_review.html` | 月度完整報表 | 月度彙總 |

### 設定檔

| 檔案 | 用途 |
|------|------|
| `requirements.txt` | Python 依賴列表 |
| `annual_plan.json` | 年度目標設定 |
| `.gitignore` | Git 忽略規則 |

---

## 🔐 資料安全

### .gitignore 保護策略

以下檔案被 git 忽略（**不會上傳到 GitHub**）：

```
# 客戶資料 ❌ 不上傳
data/*.csv
data/*.xlsx
!data/templates/

# 時間戳備份 ❌ 只保留 latest
output/dashboard_*.html
output/dashboard_employee_*.html

# 憑證 ❌ 絕對不上傳
.env
credentials/
```

### 敏感資訊

若專案包含以下敏感資訊，**務必添加到 .gitignore**：

```bash
# .env 檔案（API 密鑰等）
echo ".env" >> .gitignore

# 客戶資料
echo "data/*.csv" >> .gitignore
echo "data/*.xlsx" >> .gitignore

# 認證檔
echo "credentials/" >> .gitignore
```

---

## 🔄 自動化排程

### macOS 系統排程 (.plist)

項目包含以下排程檔：

- `com.tzg.dashboard.boot.plist` - 開機執行
- `com.tzg.dashboard.daily.plist` - 每日定時執行
- `com.tzg.dashboard.afternoon.plist` - 下午執行

**安裝排程：**

```bash
# 將排程檔複製到 LaunchAgents
cp *.plist ~/Library/LaunchAgents/

# 啟用排程
launchctl load ~/Library/LaunchAgents/com.tzg.dashboard.daily.plist

# 驗證排程
launchctl list | grep tzg
```

**在新電腦上恢復排程：**

```bash
# 1. 編輯排程檔中的路徑（替換為新路徑）
sed -i '' "s|/old/path|/new/path|g" *.plist

# 2. 重新安裝排程
cp *.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.tzg.dashboard.*.plist

# 3. 驗證
launchctl list | grep tzg
```

---

## 💾 備份與還原

### 創建備份

```bash
# 備份整個項目（不含 git 歷史）
tar -czf tzg-dashboard-$(date +%Y%m%d).tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.claude' \
  .

# 備份只含必要檔案
tar -czf tzg-dashboard-minimal-$(date +%Y%m%d).tar.gz \
  data/ output/ *.py *.json *.sh requirements.txt
```

### 還原備份

```bash
# 完全還原
tar -xzf tzg-dashboard-YYYYMMDD.tar.gz

# 進入目錄
cd tzg-dashboard

# 重新安裝依賴並生成報表
pip install -r requirements.txt
python3 generate_daily.py
python3 generate_monthly_review.py
```

---

## 🎓 進階主題

### 修改報表樣式

報表樣式定義在：
- `data/templates/monthly_review_template.html` - CSS 和 HTML 結構

修改方式：
```html
<!-- 修改色彩主題 -->
:root {
  --primary: #FF6B6B;    /* 主色 */
  --secondary: #4ECDC4;  /* 輔色 */
  --gold: #FFD93D;       /* 強調色 */
}
```

### 擴展功能

若要添加新的報表頁面：

1. 在 `generate_daily.py` 中添加資料計算邏輯
2. 在 HTML 模板中添加新的 `<div class="page">` 區塊
3. 添加相應的 JavaScript 渲染函數

### 性能優化

若報表生成速度慢：

```python
# 使用 chunksize 處理大檔案
df = pd.read_csv('data/TZG_orders.csv', chunksize=10000)

# 使用快取避免重複計算
import functools
@functools.lru_cache(maxsize=128)
def expensive_calculation(x):
    ...
```

---

## 📞 求助資源

| 問題 | 資源 |
|------|------|
| Python 安裝 | https://www.python.org/downloads/ |
| pandas 文檔 | https://pandas.pydata.org/docs/ |
| Git 問題 | https://git-scm.com/doc |
| 報表樣式 | 檢查瀏覽器開發者工具 (F12) |

---

## ✅ 恢復成功標誌

完成以下檢查，即表示恢復成功：

- [ ] ✅ Python 3.7+ 已安裝
- [ ] ✅ 依賴套件已安裝 (`pip show pandas`)
- [ ] ✅ 檔案結構完整 (`ls data/ output/`)
- [ ] ✅ `generate_daily.py` 執行成功
- [ ] ✅ `generate_monthly_review.py` 執行成功
- [ ] ✅ HTML 報表已生成 (`ls -lah output/*.html`)
- [ ] ✅ 瀏覽器可正常開啟報表
- [ ] ✅ 報表顯示完整內容（p1-p9 所有頁面）

---

**最後更新：2026-05-07**  
**版本：1.0**
