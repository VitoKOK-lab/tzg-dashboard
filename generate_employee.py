#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TZG 員工版儀表板 — 只顯示本月達標進度與業務貢獻
不含：公司總營收脈絡、毛利、顧客個資、年度/季度比較
"""
import pandas as pd
import json
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
import calendar

DATA_DIR      = Path('./data')
OUTPUT_DIR    = Path('./output')
OUTPUT_LATEST = OUTPUT_DIR / 'dashboard_employee_latest.html'
MONTHLY_TARGET = 4_500_000

CANCELLED_STATUSES = ['已取消', '取消', '訂單已取消', 'cancelled', 'Cancelled']
AGENT_KEYWORDS     = ['業務', '代理', '客服', '跟單', '銷售', '店長', '店員', '老闆', '員工']

def is_real_agent(s):
    if s is None: return False
    s = str(s).strip()
    if not s or s == 'nan': return False
    if re.match(r'^\d{8}[a-z0-9]+$', s.replace(' ', '').lower()): return False
    if any(k in s for k in ['推流', '主頁參數', '主頁推流', '大帳', '推廣', '廣告']): return False
    if '/' in s: return True
    if any(k in s for k in AGENT_KEYWORDS): return True
    return False

def fmt_money(n):
    """NT$1,234,567 → NT$123萬 / NT$1.2M style"""
    if n >= 10_000_000:
        return f'NT${n/10_000_000:.1f}千萬'
    if n >= 1_000_000:
        return f'NT${n/10_000:.0f}萬'
    if n >= 10_000:
        return f'NT${n/10_000:.1f}萬'
    return f'NT${n:,.0f}'

def fmt_money_k(n):
    """業務個人金額：NT$329K"""
    if n >= 1_000_000:
        return f'NT${n/10_000:.0f}萬'
    if n >= 1_000:
        return f'NT${n/1_000:.0f}K'
    return f'NT${n:,.0f}'

# ── 1. 讀取資料 ──────────────────────────────────────────
def load_data():
    csv_files = sorted(DATA_DIR.glob('*.csv'))
    xls_files = sorted(list(DATA_DIR.glob('*.xls')) + list(DATA_DIR.glob('*.xlsx')))
    standard_cols = [
        '訂單號碼', '訂單日期', '訂單狀態', '訂單合計',
        '推薦活動', '顧客 ID', '顧客',
    ]
    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False)
            dfs.append(df[[c for c in standard_cols if c in df.columns]])
        except Exception as e:
            print(f'  [!] {f.name}: {e}')
    for f in xls_files:
        try:
            df = pd.read_excel(f)
            available = [c for c in standard_cols if c in df.columns]
            dfs.append(df[available])
        except Exception as e:
            print(f'  [!] {f.name}: {e}')
    if not dfs:
        print('[X] 沒有資料檔案'); sys.exit(1)
    df = pd.concat(dfs, ignore_index=True, sort=False)
    df['訂單日期'] = pd.to_datetime(df['訂單日期'], errors='coerce')
    df = df.dropna(subset=['訂單日期', '訂單號碼'])
    # 注意：訂單合計只有每筆訂單的第一行有值，不可 keep='last'
    df['訂單合計'] = pd.to_numeric(df.get('訂單合計', 0), errors='coerce').fillna(0)
    return df

# ── 2. 計算指標 ──────────────────────────────────────────
def calc(df):
    today    = datetime.now()
    m_start  = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    m_end    = today
    last_day = calendar.monthrange(today.year, today.month)[1]
    days_remaining = last_day - today.day

    # 本月有效訂單（排除已取消）
    mtd = df[(df['訂單日期'] >= m_start) & (df['訂單日期'] <= m_end)].copy()
    if '訂單狀態' in mtd.columns:
        mtd = mtd[~mtd['訂單狀態'].isin(CANCELLED_STATUSES)]

    # 訂單層級：訂單合計只有第一行有值，用 keep='first' 取正確金額
    order_mtd  = mtd.drop_duplicates(subset=['訂單號碼'], keep='first')
    month_rev  = int(order_mtd['訂單合計'].sum())

    pct     = min(month_rev / MONTHLY_TARGET * 100, 100)
    reached = month_rev >= MONTHLY_TARGET
    gap     = max(MONTHLY_TARGET - month_rev, 0)

    # 業務排行：用 first() 確保每筆訂單只算一次金額
    agents = []
    if '推薦活動' in mtd.columns:
        # 先依訂單號碼 + 推薦活動分組，取第一行（確保金額正確）
        ag_base = mtd[mtd['推薦活動'].apply(
            lambda x: is_real_agent(x) if pd.notna(x) else False
        )]
        ag_orders = ag_base.drop_duplicates(subset=['訂單號碼'], keep='first')
        agg = ag_orders.groupby('推薦活動').agg(
            orders=('訂單號碼', 'count'),
            rev=('訂單合計', 'sum')
        ).sort_values('rev', ascending=False).reset_index()
        for i, r in agg.iterrows():
            agents.append({
                'rank':   i + 1,
                'name':   str(r['推薦活動']),
                'orders': int(r['orders']),
                'rev':    int(r['rev']),
            })

    return {
        'month_label':     today.strftime('%Y年%-m月') if sys.platform != 'win32' else f"{today.year}年{today.month}月",
        'today':           today.strftime('%Y/%m/%d'),
        'days_remaining':  days_remaining,
        'month_rev':       month_rev,
        'target':          MONTHLY_TARGET,
        'pct':             round(pct, 1),
        'reached':         reached,
        'gap':             gap,
        'agents':          agents,
    }

# ── 3. 產生 HTML ─────────────────────────────────────────
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TZG 本月業績達標</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #0f1117; color: #e2e8f0; min-height: 100vh; padding: 16px; }}

  .header {{ text-align: center; padding: 20px 0 8px; }}
  .header h1 {{ font-size: 20px; font-weight: 700; color: #f8fafc; letter-spacing: 1px; }}
  .header .sub {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}

  .card {{ background: #1e2330; border-radius: 16px; padding: 20px; margin: 12px 0; }}

  /* 達標狀態 */
  .status-reached {{ background: linear-gradient(135deg, #064e3b, #065f46);
                     border: 1px solid #10b981; }}
  .status-not {{ background: linear-gradient(135deg, #1e1b2e, #2d1f3d);
                 border: 1px solid #7c3aed; }}
  .status-icon {{ font-size: 48px; text-align: center; margin-bottom: 8px; }}
  .status-label {{ text-align: center; font-size: 22px; font-weight: 700; }}
  .status-reached .status-label {{ color: #10b981; }}
  .status-not .status-label {{ color: #a78bfa; }}
  .status-gap {{ text-align: center; font-size: 14px; color: #94a3b8; margin-top: 6px; }}

  /* 進度條 */
  .progress-section {{ }}
  .progress-numbers {{ display: flex; justify-content: space-between;
                       font-size: 13px; color: #94a3b8; margin-bottom: 8px; }}
  .progress-numbers .current {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
  .progress-numbers .target-label {{ font-size: 14px; color: #64748b; align-self: flex-end; padding-bottom: 4px; }}
  .bar-bg {{ background: #2d3748; border-radius: 999px; height: 14px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 999px; transition: width 0.8s ease;
               background: linear-gradient(90deg, #7c3aed, #10b981); }}
  .bar-fill.full {{ background: linear-gradient(90deg, #059669, #10b981); }}
  .pct-row {{ display: flex; justify-content: space-between;
              font-size: 12px; color: #64748b; margin-top: 6px; }}

  /* 剩餘天數 */
  .days-row {{ display: flex; justify-content: center; gap: 6px;
               font-size: 13px; color: #94a3b8; margin-top: 10px; }}
  .days-num {{ color: #f8fafc; font-weight: 700; font-size: 16px; }}

  /* 排行榜 */
  .section-title {{ font-size: 14px; font-weight: 600; color: #94a3b8;
                    letter-spacing: 0.5px; margin-bottom: 14px; }}
  .agent-row {{ display: flex; align-items: center; padding: 12px 0;
                border-bottom: 1px solid #2d3748; }}
  .agent-row:last-child {{ border-bottom: none; }}
  .rank {{ width: 32px; font-size: 15px; font-weight: 700; color: #64748b; flex-shrink: 0; }}
  .rank.r1 {{ color: #f59e0b; }}
  .rank.r2 {{ color: #94a3b8; }}
  .rank.r3 {{ color: #cd7c2f; }}
  .agent-info {{ flex: 1; min-width: 0; }}
  .agent-name {{ font-size: 15px; font-weight: 600; color: #f1f5f9;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .agent-orders {{ font-size: 12px; color: #64748b; margin-top: 2px; }}
  .agent-rev {{ font-size: 16px; font-weight: 700; color: #e2e8f0; text-align: right; flex-shrink: 0; }}

  /* 免責 */
  .footer {{ text-align: center; font-size: 11px; color: #334155;
             padding: 20px 0 8px; }}
</style>
</head>
<body>

<div class="header">
  <h1>TZG 本月業績達標</h1>
  <div class="sub">{month_label} &nbsp;·&nbsp; 更新：{today}</div>
</div>

<!-- 達標狀態 -->
<div class="card {status_class}">
  <div class="status-icon">{status_icon}</div>
  <div class="status-label">{status_label}</div>
  <div class="status-gap">{status_detail}</div>
</div>

<!-- 進度 -->
<div class="card progress-section">
  <div class="progress-numbers">
    <div class="current">{month_rev_fmt}</div>
    <div class="target-label">目標 {target_fmt}</div>
  </div>
  <div class="bar-bg">
    <div class="bar-fill {bar_class}" style="width:{pct}%"></div>
  </div>
  <div class="pct-row">
    <span>{pct}%</span>
    <span class="days-row">本月剩 <span class="days-num">&nbsp;{days_remaining}&nbsp;</span> 天</span>
  </div>
</div>

<!-- 業務排行 -->
<div class="card">
  <div class="section-title">業務貢獻排行</div>
  {agents_html}
</div>

<div class="footer">此頁面僅供內部參考 · 請勿對外分享</div>
</body>
</html>'''

def render_agents(agents):
    if not agents:
        return '<div style="color:#64748b;text-align:center;padding:20px">本月尚無業務資料</div>'
    rows = []
    for a in agents:
        r = a['rank']
        rank_cls = {1: 'r1', 2: 'r2', 3: 'r3'}.get(r, '')
        rank_sym = {1: '🥇', 2: '🥈', 3: '🥉'}.get(r, f'#{r}')
        rows.append(f'''
  <div class="agent-row">
    <div class="rank {rank_cls}">{rank_sym}</div>
    <div class="agent-info">
      <div class="agent-name">{a["name"]}</div>
      <div class="agent-orders">{a["orders"]} 筆</div>
    </div>
    <div class="agent-rev">{fmt_money_k(a["rev"])}</div>
  </div>''')
    return '\n'.join(rows)

def generate(d):
    OUTPUT_DIR.mkdir(exist_ok=True)
    reached = d['reached']
    html = HTML_TEMPLATE.format(
        month_label   = d['month_label'],
        today         = d['today'],
        status_class  = 'status-reached' if reached else 'status-not',
        status_icon   = '🎉' if reached else '💪',
        status_label  = '本月達標！' if reached else '繼續衝刺！',
        status_detail = f'已超越目標 {fmt_money(d["month_rev"] - d["target"])}' if reached
                        else f'還差 {fmt_money(d["gap"])} 達標',
        month_rev_fmt = fmt_money(d['month_rev']),
        target_fmt    = fmt_money(d['target']),
        pct           = d['pct'],
        bar_class     = 'full' if reached else '',
        days_remaining= d['days_remaining'],
        agents_html   = render_agents(d['agents']),
    )
    OUTPUT_LATEST.write_text(html, encoding='utf-8')
    # 備份
    backup = OUTPUT_DIR / f"dashboard_employee_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.html"
    backup.write_text(html, encoding='utf-8')
    print(f'[OK] 員工版儀表板：{OUTPUT_LATEST}')
    return str(OUTPUT_LATEST)

# ── 主程式 ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 50)
    print(' TZG 員工版儀表板')
    print('=' * 50)
    df   = load_data()
    data = calc(df)
    print(f'  本月營收：{fmt_money(data["month_rev"])} / 目標 {fmt_money(MONTHLY_TARGET)}')
    status_str = '達標' if data['reached'] else f'還差 {fmt_money(data["gap"])}'
    print(f'  進度：{data["pct"]}%  {status_str}')
    print(f'  業務人數：{len(data["agents"])}')
    path = generate(data)
    print(f'\n[成功] {path}')
