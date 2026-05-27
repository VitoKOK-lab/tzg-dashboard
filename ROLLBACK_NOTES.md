# 重大改動快照（Rollback 速查表）

每次重大邏輯改動都會打 git tag 留 snapshot，這份檔記下「想回到那個狀態時該怎麼做」。

---

## 2026-05-23 銷售客服真實貢獻調整（CSR adjustment）

**Commit**: `1d349d1` — feat: 銷售客服真實貢獻調整（裸石歸內容、金工歸客服）

**Tag**:
- `pre-csr-adjustment` → 改動**之前**的狀態（hash `a4a0d3b`）
- `csr-adjustment-v1` → 改動**之後**的狀態（hash `1d349d1`）

**改動範圍**：
- `generate_daily.py`：新增 `compute_csr_adjustment` / `attach_agent_revenue` 等函式，業務排行 6 處 groupby 改用「客服貢獻金額」
- `generate_monthly_review.py`：同步套用（歷史月份報表全部會自動重算）

**規則**：
- 推薦活動含「客服 / 跟單 / 銷售 / 行銷」之一
- 訂單備註或管理員備註含舊單號（regex: `#?\d{17}`）
- 舊單必須狀態=已取消、日期在新單前 ≤30 天
- 新舊單共同商品（by SKU）的金額從客服貢獻扣除

### 如果這次改動出問題、要回到舊行為

#### 選項 A：完全回退（最徹底，會丟掉之後所有新 commit）

```bash
cd /Users/vitomini/tzg-dashboard
# 確認沒有未 commit 的本機改動
git status

# 強制回到 CSR 之前的狀態（會丟掉所有 commit）
git reset --hard pre-csr-adjustment

# 強制推上 GitHub（覆蓋遠端歷史，請確認沒人在其他機器上有未推的 commit）
git push --force-with-lease origin main
```

⚠️ **這是 destructive 操作**。CSR 之後做的所有 commit（包括正常的每日 dashboard 自動 commit）都會消失。

#### 選項 B：只 revert CSR 那個 commit（保留之後的工作）

```bash
cd /Users/vitomini/tzg-dashboard
git revert 1d349d1
git push origin main
```

這會新增一個「反向 commit」抵消 CSR 改動，歷史保留。最安全，**推薦這個**。

#### 選項 C：軟停用（不動 git，只關閉功能）

不想動 git 歷史，純粹要「立刻讓客服業績回到舊算法」：

編輯 `generate_daily.py`，把 `CSR_KEYWORDS` 改成空 list：

```python
CSR_KEYWORDS = []  # 原本是 ['客服', '跟單', '銷售', '行銷']
```

`is_csr_agent` 永遠回 `False` → `compute_csr_adjustment` 永遠回 `{}` →
客服貢獻金額 = 訂單合計 → 等同舊行為。

之後想重啟，把關鍵字補回去即可。

---

### 比較 snapshot 差異

```bash
# 看兩個 tag 之間改了哪些檔
git diff pre-csr-adjustment csr-adjustment-v1 --stat

# 看具體 code diff
git diff pre-csr-adjustment csr-adjustment-v1 -- generate_daily.py
```

---

## 通用 tag 約定

之後重大改動都會打：
- `pre-<feature-name>`：改動前的最後狀態
- `<feature-name>-v1`：改動後的第一版

列出所有 snapshot：
```bash
git tag --list -n2
```
