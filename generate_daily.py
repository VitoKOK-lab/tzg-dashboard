#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════
  TZG 電商每日簡報  v3.5 FINAL
════════════════════════════════════════════════════════════
對照模板樣本資料設計：
  ✅ 付款狀態 NaN（歷史 CSV）視為已付款，只排除已取消
  ✅ RFM 母體 = 本月下單客戶（對應模板 381 人）
  ✅ 計算本月流失數（churn.monthly）
  ✅ 季度排行、沒人買列表、熱力圖全部基於正確的 vd

時間範圍：
  kpi/yesterday/week/monthly/agents/sources/cities/products
  /customers/interval/dow/hour/shopping_habits/member_funnel
                                              → 本月 MTD / 對比
  heatmap                                     → 近 90 天
  dormant 沒人買商品                          → 全歷史 ≥30 天
  active_tiers/first_vs_return/repurchase/new_6m → 全歷史
  churn                                       → 近 90 天 vs 前 90 天
  unpaid                                      → 48 小時內
  rfm                                         → 母體本月下單客戶
════════════════════════════════════════════════════════════
"""
import pandas as pd
import numpy as np
import json
import re
import sys
import traceback
import calendar as _cal
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

DATA_DIR       = Path('./data')
TEMPLATE_HTML = Path('./data/templates/dashboard_template_mobile.html')
OUTPUT_DIR     = Path('./output')
OUTPUT_LATEST  = OUTPUT_DIR / 'dashboard_latest.html'  # 永遠上傳這個！

MONTHLY_TARGET = 4_500_000
MANUAL_TODAY   = None

PAID_STATUSES       = ['已付款', '付款完成', '已收款', 'paid', 'Paid']
CANCELLED_STATUSES  = ['已取消', '取消', '訂單已取消', 'cancelled', 'Cancelled']
UNPAID_STATUSES     = ['未付款', '待付款', '尚未付款', '等待付款']
UNPAID_WINDOW_HOURS = 48
DORMANT_DAYS        = 30

COMBO_EXCLUDE_KEYWORDS = [
    '禮盒', '包裝', '贈品', '運費', '試戴', '改圍',
    '消磁聚寶盆', '訂製-', '訂製', '補差價', '手工費',
    '珍珠耳釘', '紫水晶小樹',
    '補貼', '客製化', '加工', '維修', '保養',
    '鑑定', '證書', '放大鏡',
]

REGIONS = [
    {'key':'north',   'name':'北北基桃', 'cities':['新北市','台北市','桃園市','基隆市'], 'color':'#3B7DD8'},
    {'key':'hsinchu', 'name':'桃竹苗',   'cities':['新竹縣','新竹市','苗栗縣'], 'color':'#0F8F85'},
    {'key':'central', 'name':'中彰投',   'cities':['台中市','彰化縣','南投縣'], 'color':'#B8902A'},
    {'key':'south',   'name':'雲嘉南',   'cities':['雲林縣','嘉義縣','嘉義市','台南市'], 'color':'#7B5FC7'},
    {'key':'kp',      'name':'高屏',     'cities':['高雄市','屏東縣'], 'color':'#D94B6B'},
    {'key':'east',    'name':'東部離島', 'cities':['宜蘭縣','花蓮縣','台東縣','澎湖縣','金門縣','連江縣'], 'color':'#E67E22'},
]

RFM_GRID = [
    [{'k':'潛在忠實','action':'培養','color':'#0F8F85'},
     {'k':'忠實客戶','action':'回饋','color':'#B8902A'},
     {'k':'冠軍客戶','action':'維繫','color':'#D94B6B'}],
    [{'k':'有希望','action':'首購回訪','color':'#3B7DD8'},
     {'k':'需關心','action':'優惠券','color':'#7B5FC7'},
     {'k':'關注中','action':'再激活','color':'#E67E22'}],
    [{'k':'流失','action':'放手','color':'#94A3B8'},
     {'k':'即將流失','action':'問卷/補貼','color':'#64748B'},
     {'k':'無法失去','action':'召回','color':'#BE185D'}],
]

AGENT_KEYWORDS = ['業務', '代理', '客服', '跟單', '銷售', '店長', '店員', '老闆', '員工']

def is_real_agent(s):
    if s is None: return False
    s = str(s).strip()
    if not s or s == 'nan': return False
    if re.match(r'^\d{8}[a-z0-9]+$', s.replace(' ', '').lower()): return False
    if any(k in s for k in ['推流', '主頁參數', '主頁推流', '大帳', '推廣', '廣告']): return False
    if '/' in s: return True
    if any(k in s for k in AGENT_KEYWORDS): return True
    return False

def classify_ad_channel(act):
    s = str(act).lower()
    if 'line' in s: return 'LINE 來源'
    if 'fb' in s or 'facebook' in s: return 'Facebook 來源'
    if 'ig' in s or 'instagram' in s: return 'Instagram 來源'
    if 'tk' in s or 'tiktok' in s: return 'TikTok 來源'
    if 'yt' in s or 'youtube' in s: return 'YouTube 來源'
    if 'threads' in s: return 'Threads 來源'
    return '內容導流'


def classify_source(r):
    """訂單來源分類（模組層級，供 daily/monthly review 共用）"""
    act = str(r.get('推薦活動', '')).strip()
    src   = str(r.get('訂單來源', '')).strip()
    src_l = src.lower()
    if act and act != 'nan':
        if is_real_agent(act): return '業務推薦'
        return classify_ad_channel(act)
    if 'facebook' in src_l or 'fb' in src_l: return 'Facebook 來源'
    if 'instagram' in src_l or 'ig' in src_l or 'tzgems1111' in src_l: return 'Instagram 來源'
    if 'line' in src_l: return 'LINE 來源'
    if '蝦皮' in src: return '蝦皮'
    if '直播' in src: return '直播'
    if '實體店' in src: return '實體店'
    if 'whatsapp' in src_l: return 'WhatsApp'
    if src_l in ('', 'nan', 'direct', 'website', 'website_web', 'website_mobile'): return '直接/官網'
    if '泰熙爾' in src or '前台購物網站' in src: return '直接/官網'
    return '其他'

# ═══════════════════════════════════════════════
def load_data():
    if not DATA_DIR.exists():
        print(f'[X] 找不到目錄：{DATA_DIR}'); sys.exit(1)
    
    # 🔧 改進：分開讀取 CSV 和 XLS 檔案，各自用不同的方式處理
    csv_files = sorted(list(DATA_DIR.glob('*.csv')))
    xls_files = sorted(list(DATA_DIR.glob('*.xls')) + list(DATA_DIR.glob('*.xlsx')))
    all_files = csv_files + xls_files
    
    if not all_files:
        print(f'[X] {DATA_DIR}/ 內沒有檔案'); sys.exit(1)
    
    dfs = []
    
    # 讀取 CSV 檔案（簡單格式，22 個欄位）
    for f in csv_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False)
            has_pay = '付款狀態' in df.columns
            has_addr2 = '地址2' in df.columns
            print(f'  [OK] {f.name}  {len(df):>5} 列   付款狀態={"有" if has_pay else "無 "}   地址2={"有" if has_addr2 else "無 "}')
            dfs.append(df)
        except Exception as e:
            print(f'  [X] {f.name}  失敗：{e}')
    
    # 讀取 XLS 檔案（複雜格式 - Shopline/MOMO 導出，139 個欄位）
    # 🔧 修復：只提取需要的欄位，以匹配 CSV 格式
    for f in xls_files:
        try:
            df = pd.read_excel(f)
            
            # 定義 CSV 的標準欄位（22 個）
            standard_cols = [
                '訂單號碼', '訂單日期', '訂單狀態', '付款方式', '訂單合計',
                '送貨方式', '收件人', '城市', '商品名稱', '選項',
                '商品結帳價', '數量', '推薦活動', '推薦代碼', '訂單來源',
                '顧客 ID', '顧客', '電郵', '電話號碼', '性別',
                '會員等級', '會員註冊日期',
                '地址 1', '地址 2',  # 🆕 加入地址資訊（用於鄉鎮顯示）
                '完整地址'  # 🆕 完整地址
            ]
            
            # 只保留 XLS 中存在的標準欄位
            available_cols = [col for col in standard_cols if col in df.columns]
            df_filtered = df[available_cols].copy()
            
            # 補充缺失的欄位（填 None）
            for col in standard_cols:
                if col not in df_filtered.columns:
                    df_filtered[col] = None
            
            # 重新排列欄位順序，與 CSV 一致
            df_filtered = df_filtered[standard_cols]
            
            print(f'  [OK] {f.name}  {len(df_filtered):>5} 列   (XLS/Shopline 格式→已標準化)')
            dfs.append(df_filtered)
        except Exception as e:
            print(f'  [X] {f.name}  失敗：{e}')
    
    df = pd.concat(dfs, ignore_index=True, sort=False)
    df['訂單日期'] = pd.to_datetime(df['訂單日期'], errors='coerce')
    if '會員註冊日期' in df.columns:
        df['會員註冊日期'] = pd.to_datetime(df['會員註冊日期'], errors='coerce')
    df = df.dropna(subset=['訂單日期','訂單號碼']).reset_index(drop=True)
    subset = ['訂單號碼','商品名稱'] + (['選項'] if '選項' in df.columns else [])
    df = df.drop_duplicates(subset=subset, keep='last').reset_index(drop=True)
    for c in ['訂單合計','商品結帳價','數量']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    if '顧客 ID' not in df.columns:
        df['顧客 ID'] = df['顧客'] if '顧客' in df.columns else df['訂單號碼']
    
    print(f'\n[合併後] 共 {len(df):,} 列明細 / {df["訂單號碼"].nunique():,} 張訂單')
    
    if '付款狀態' in df.columns:
        pay_str = df['付款狀態'].astype(str)
        has_val = (~pay_str.isin(['nan', 'NaN', 'None', ''])).sum()
        no_val  = len(df) - has_val
        print(f'[付款狀態] 有值 {has_val:,} 列 / NaN(歷史) {no_val:,} 列')
    
    return df

# ═══════════════════════════════════════════════
# 🔑 業績訂單：NaN 付款狀態視為已付款（相容歷史 CSV）
# ═══════════════════════════════════════════════
def paid_orders(df):
    """
    v3.6 更保險：用 fillna('') 保證 NaN 被轉成空字串，再用 == '' 判斷
    這樣不管 pandas 版本差異（nan/NaN/<NA>/NaT 都會被歸為空）
    """
    has_pay = '付款狀態' in df.columns
    has_ord = '訂單狀態' in df.columns
    
    if has_pay:
        pay_str = df['付款狀態'].fillna('').astype(str).str.strip()
        # 空字串（NaN 歷史資料）或已付款 → 有效業績
        valid_pay = (pay_str == '') | pay_str.isin(PAID_STATUSES)
    else:
        valid_pay = pd.Series([True] * len(df), index=df.index)
    
    if has_ord:
        ord_str = df['訂單狀態'].fillna('').astype(str).str.strip()
        not_cancelled = ~ord_str.isin(CANCELLED_STATUSES)
    else:
        not_cancelled = pd.Series([True] * len(df), index=df.index)
    
    return df[valid_pay & not_cancelled]

def order_level(df):
    return df.drop_duplicates('訂單號碼')

def month_range(y, m):
    s = datetime(y, m, 1)
    e = datetime(y+1, 1, 1) if m == 12 else datetime(y, m+1, 1)
    return s, e

def in_range(df, s, e):
    return df[(df['訂單日期'] >= s) & (df['訂單日期'] < e)]


def compute_month_review(vd, ccol, yr, mo, target=MONTHLY_TARGET):
    """
    計算單一月份的完整回顧資料（給 daily dashboard 的 prev_month
    以及月會專用網頁共用）
    回傳 dict 或 None（無資料）
    """
    pm_s, pm_e = month_range(yr, mo)
    pm_lines   = in_range(vd, pm_s, pm_e)
    pm_ord     = order_level(pm_lines)

    if len(pm_ord) == 0:
        return None

    days_in_pm = _cal.monthrange(yr, mo)[1]
    pm_rev     = int(pm_ord['訂單合計'].sum())
    pm_orders  = len(pm_ord)
    pm_avg     = int(pm_rev / pm_orders) if pm_orders else 0

    # 客戶分類
    first_ord_all = vd.groupby(ccol)['訂單日期'].min()
    pm_custs   = set(pm_lines[ccol].dropna().unique())
    pm_new     = sum(1 for c in pm_custs if c in first_ord_all.index and first_ord_all[c] >= pm_s)
    pm_ret     = len(pm_custs) - pm_new
    pm_total_c = len(pm_custs)
    pm_new_pct = round(pm_new / pm_total_c * 100, 1) if pm_total_c else 0

    # 達成率
    pm_ach = round(pm_rev / target * 100, 1)

    # YoY（去年同月）
    ly_s, ly_e = month_range(yr - 1, mo)
    ly_ord  = order_level(in_range(vd, ly_s, ly_e))
    yoy_rev = int(ly_ord['訂單合計'].sum()) if len(ly_ord) else 0
    yoy_pct = round((pm_rev - yoy_rev) / yoy_rev * 100, 1) if yoy_rev else None

    # MoM（前一個月）
    pmm_yr = yr - 1 if mo == 1 else yr
    pmm_mo = 12     if mo == 1 else mo - 1
    pmm_s, pmm_e = month_range(pmm_yr, pmm_mo)
    pmm_ord = order_level(in_range(vd, pmm_s, pmm_e))
    mom_rev = int(pmm_ord['訂單合計'].sum()) if len(pmm_ord) else 0
    mom_pct = round((pm_rev - mom_rev) / mom_rev * 100, 1) if mom_rev else None

    # 日銷明細 + 累計
    pm_daily = []
    cumulative = 0
    for d in range(1, days_in_pm + 1):
        d_s = datetime(yr, mo, d)
        d_e = d_s + timedelta(days=1)
        d_ord = order_level(in_range(vd, d_s, d_e))
        rev = int(d_ord['訂單合計'].sum())
        cumulative += rev
        pm_daily.append({
            'day': d, 'label': f'{mo}/{d}',
            'rev': rev, 'orders': len(d_ord),
            'cumulative': cumulative,
        })

    # 業務排名（含 orders, rev, new_clients, avg）
    pm_agents = []
    if '推薦活動' in pm_lines.columns:
        ag_b = pm_lines[pm_lines['推薦活動'].notna() & pm_lines['推薦活動'].apply(is_real_agent)]
        if len(ag_b):
            ag_o = order_level(ag_b)
            ag_g = ag_o.groupby('推薦活動').agg(
                orders=('訂單號碼', 'count'),
                rev=('訂單合計', 'sum'),
                customers=(ccol, 'nunique'),
            ).sort_values('rev', ascending=False).reset_index()
            for i, r in ag_g.iterrows():
                # 計算這位業務本月的新客數
                ag_custs = set(ag_o[ag_o['推薦活動'] == r['推薦活動']][ccol].dropna().unique())
                new_for_ag = sum(1 for c in ag_custs if c in first_ord_all.index and first_ord_all[c] >= pm_s)
                pm_agents.append({
                    'name': str(r['推薦活動']),
                    'orders': int(r['orders']),
                    'rev': int(r['rev']),
                    'customers': int(r['customers']),
                    'new_customers': new_for_ag,
                    'avg_order': int(r['rev'] / r['orders']) if r['orders'] else 0,
                    'rank': i + 1,
                })

    # 商品（依營收 / 依數量）
    pm_prod_rev = pm_lines.groupby('商品名稱').agg(
        qty=('數量', 'sum'), rev=('商品結帳價', 'sum'), orders=('訂單號碼', 'nunique')
    ).sort_values('rev', ascending=False).head(15).reset_index()
    pm_top_prod_rev = [
        {'name': str(r['商品名稱'])[:35], 'qty': int(r['qty']), 'rev': int(r['rev']),
         'orders': int(r['orders']), 'avg': int(r['rev'] / r['qty']) if r['qty'] else 0}
        for _, r in pm_prod_rev.iterrows()
    ]
    pm_prod_qty = pm_lines.groupby('商品名稱').agg(
        qty=('數量', 'sum'), rev=('商品結帳價', 'sum')
    ).sort_values('qty', ascending=False).head(15).reset_index()
    pm_top_prod_qty = [
        {'name': str(r['商品名稱'])[:35], 'qty': int(r['qty']), 'rev': int(r['rev'])}
        for _, r in pm_prod_qty.iterrows()
    ]

    # 訂單來源（含完整指標：orders, customers, rev, AOV, new%）
    pm_ord2 = pm_ord.copy()
    pm_ord2['_src'] = pm_ord2.apply(classify_source, axis=1)
    src_g = pm_ord2.groupby('_src').agg(
        orders=('訂單號碼', 'count'),
        rev=('訂單合計', 'sum'),
        customers=(ccol, 'nunique'),
    ).sort_values('rev', ascending=False).reset_index()
    src_tot = int(src_g['rev'].sum())
    pm_sources = []
    for _, r in src_g.iterrows():
        src_name = r['_src']
        src_custs = set(pm_ord2[pm_ord2['_src'] == src_name][ccol].dropna().unique())
        new_in_src = sum(1 for c in src_custs if c in first_ord_all.index and first_ord_all[c] >= pm_s)
        pm_sources.append({
            'src': src_name,
            'orders': int(r['orders']),
            'customers': int(r['customers']),
            'rev': int(r['rev']),
            'pct': round(r['rev'] / src_tot * 100, 1) if src_tot else 0,
            'aov': int(r['rev'] / r['orders']) if r['orders'] else 0,
            'new_customers': new_in_src,
            'new_pct': round(new_in_src / r['customers'] * 100, 1) if r['customers'] else 0,
        })

    # 城市（全部，不止 Top 8）
    pm_cities = []
    if '城市' in pm_ord.columns:
        city_g = pm_ord[
            pm_ord['城市'].notna() & (pm_ord['城市'].astype(str).str.strip() != '')
        ].groupby('城市').agg(
            orders=('訂單號碼', 'count'),
            rev=('訂單合計', 'sum'),
            customers=(ccol, 'nunique'),
        ).sort_values('rev', ascending=False).reset_index()
        for _, r in city_g.iterrows():
            pm_cities.append({
                'city': str(r['城市']),
                'orders': int(r['orders']),
                'customers': int(r['customers']),
                'rev': int(r['rev']),
                'aov': int(r['rev'] / r['orders']) if r['orders'] else 0,
            })

    # 首購 vs 回購 AOV
    if pm_new + pm_ret > 0:
        new_set = set(c for c in pm_custs if c in first_ord_all.index and first_ord_all[c] >= pm_s)
        ret_set = pm_custs - new_set
        new_orders_df = pm_ord[pm_ord[ccol].isin(new_set)]
        ret_orders_df = pm_ord[pm_ord[ccol].isin(ret_set)]
        first_aov = int(new_orders_df['訂單合計'].mean()) if len(new_orders_df) else 0
        return_aov = int(ret_orders_df['訂單合計'].mean()) if len(ret_orders_df) else 0
    else:
        first_aov, return_aov = 0, 0

    # 時段分布
    pm_hours = []
    if len(pm_ord):
        h_dist = pm_ord['訂單日期'].dt.hour.value_counts().sort_index()
        pm_hours = [{'hour': int(h), 'orders': int(c)} for h, c in h_dist.items()]

    # 星期分布
    pm_dow = []
    if len(pm_ord):
        dow_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        dow_g = pm_ord.groupby(pm_ord['訂單日期'].dt.dayofweek).agg(
            orders=('訂單號碼', 'count'), rev=('訂單合計', 'sum')
        )
        for i in range(7):
            if i in dow_g.index:
                pm_dow.append({'day': dow_names[i], 'orders': int(dow_g.loc[i, 'orders']),
                               'rev': int(dow_g.loc[i, 'rev'])})
            else:
                pm_dow.append({'day': dow_names[i], 'orders': 0, 'rev': 0})

    # 客單價分布
    spend_buckets = {'<2千': 0, '2–5千': 0, '5千–1萬': 0, '1–3萬': 0, '>3萬': 0}
    for v in pm_ord['訂單合計']:
        if v < 2000: spend_buckets['<2千'] += 1
        elif v < 5000: spend_buckets['2–5千'] += 1
        elif v < 10000: spend_buckets['5千–1萬'] += 1
        elif v < 30000: spend_buckets['1–3萬'] += 1
        else: spend_buckets['>3萬'] += 1

    # Top 客戶（依本月營收，前 15 位）
    pm_top_customers = []
    cust_rev_series  = pm_ord.groupby(ccol)['訂單合計'].sum().sort_values(ascending=False)
    if '顧客' in pm_ord.columns:
        name_map = pm_ord.drop_duplicates(ccol).set_index(ccol)['顧客'].to_dict()
    else:
        name_map = {}
    cust_g = pm_ord.groupby(ccol).agg(
        orders=('訂單號碼', 'count'),
        rev=('訂單合計', 'sum')
    ).sort_values('rev', ascending=False).head(15).reset_index()
    for _, r in cust_g.iterrows():
        pm_top_customers.append({
            'name':   mask_name(name_map.get(r[ccol], '')),
            'orders': int(r['orders']),
            'rev':    int(r['rev']),
        })

    # 客戶集中度（前 10 / 20 位佔總營收比例）
    total_rev = float(cust_rev_series.sum()) if len(cust_rev_series) else 0
    top10_rev = float(cust_rev_series.head(10).sum()) if len(cust_rev_series) else 0
    top20_rev = float(cust_rev_series.head(20).sum()) if len(cust_rev_series) else 0
    concentration_top10 = round(top10_rev / total_rev * 100, 1) if total_rev else 0
    concentration_top20 = round(top20_rev / total_rev * 100, 1) if total_rev else 0

    # 平均每位客戶下單次數
    avg_orders_per_cust = round(pm_orders / pm_total_c, 2) if pm_total_c else 0

    return {
        'year_month':   f'{yr}-{mo:02d}',
        'month_label':  f'{yr}年{mo}月',
        'year':         yr,
        'month':        mo,
        'days':         days_in_pm,
        'rev':          pm_rev,
        'orders':       pm_orders,
        'avg_order':    pm_avg,
        'new_customers': pm_new,
        'returning':    pm_ret,
        'total_customers': pm_total_c,
        'new_pct':      pm_new_pct,
        'target':       target,
        'achievement_pct': pm_ach,
        'yoy_rev':      yoy_rev,
        'yoy_pct':      yoy_pct,
        'mom_rev':      mom_rev,
        'mom_pct':      mom_pct,
        'daily':        pm_daily,
        'agents':       pm_agents,
        'top_prod_rev': pm_top_prod_rev,
        'top_prod_qty': pm_top_prod_qty,
        'sources':      pm_sources,
        'cities':       pm_cities,
        'first_aov':    first_aov,
        'return_aov':   return_aov,
        'hours':        pm_hours,
        'dow':          pm_dow,
        'spend_dist':   spend_buckets,
        'top_customers':       pm_top_customers,
        'concentration_top10': concentration_top10,
        'concentration_top20': concentration_top20,
        'avg_orders_per_customer': avg_orders_per_cust,
    }

def clean_city(c):
    if pd.isna(c): return '未知'
    s = str(c).strip().replace('台', '臺')
    cities = ['臺北市','新北市','桃園市','臺中市','臺南市','高雄市',
              '基隆市','新竹市','嘉義市',
              '新竹縣','苗栗縣','彰化縣','南投縣','雲林縣','嘉義縣',
              '屏東縣','宜蘭縣','花蓮縣','臺東縣','澎湖縣','金門縣','連江縣']
    for city in cities:
        if city in s:
            return city.replace('臺', '台')
    m = re.search(r'([^\s\d]{2,3}(?:市|縣))', s)
    if m:
        return m.group(1).replace('臺', '台')
    return '未知'

def extract_town(addr):
    if pd.isna(addr): return None
    s = str(addr).strip().replace('台', '臺')
    s2 = re.sub(r'^[\s\d]*(?:臺北市|新北市|桃園市|臺中市|臺南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|澎湖縣|金門縣|連江縣)', '', s)
    m = re.search(r'([^\s\d]{1,4}?(?:區|鄉|鎮|市))', s2)
    if m:
        town = m.group(1)
        if len(town) < 2: return None
        if town in ['臺北', '新北', '桃園', '臺中', '臺南', '高雄']: return None
        return town
    return None

def mask_name(n):
    if pd.isna(n) or not str(n).strip(): return '匿名'
    n = str(n).strip()
    if len(n) <= 1: return n
    if len(n) == 2: return n[0] + 'O'
    return n[0] + 'O' + n[-1]

def is_real_product(name):
    s = str(name)
    return not any(k in s for k in COMBO_EXCLUDE_KEYWORDS)

# ═══════════════════════════════════════════════
def compute(df):
    today = MANUAL_TODAY or df['訂單日期'].max().to_pydatetime()
    today = today.replace(hour=23, minute=59, second=59, microsecond=0)
    print(f'\n[報告日期] {today:%Y-%m-%d}（UTC+08:00）')
    
    vd = paid_orders(df)
    ccol = '顧客 ID'  # ✅ 提前定義
    print(f'[有效業績訂單] {vd["訂單號碼"].nunique():,} 張（已付款/歷史+非已取消）')
    
    # ★ 關鍵診斷：vd 的日期範圍
    if len(vd):
        print(f'[vd 日期範圍] {vd["訂單日期"].min():%Y-%m-%d} ~ {vd["訂單日期"].max():%Y-%m-%d}')
        print(f'[vd 獨立客戶] {vd[ccol if "顧客 ID" in vd.columns else "顧客"].nunique():,} 位')
    
    yr, mo = today.year, today.month
    D = {'target': MONTHLY_TARGET}
    ms, me = month_range(yr, mo)
    D['meta'] = {
        'report_month': f'{yr}年{mo}月',
        'data_as_of': today.strftime('%Y-%m-%d'),
        'days_elapsed': today.day,
        'days_total': (me - ms).days,
        'yesterday': today.strftime('%Y-%m-%d'),
        'timezone': 'UTC+08:00',
    }
    
    # KPI（本月 MTD）
    mtd_lines = in_range(vd, ms, today + timedelta(days=1))
    mtd_ord   = order_level(mtd_lines)
    rev_mtd   = mtd_ord['訂單合計'].sum()
    n_ord     = len(mtd_ord)
    aov       = rev_mtd / n_ord if n_ord else 0
    med       = mtd_ord['訂單合計'].median() if n_ord else 0
    dtot      = D['meta']['days_total']
    proj      = rev_mtd / today.day * dtot if today.day else rev_mtd
    
    ly_s, ly_e = month_range(yr-1, mo)
    rev_ly_full = order_level(in_range(vd, ly_s, ly_e))['訂單合計'].sum()
    
    first_ord = vd.groupby(ccol)['訂單日期'].min()
    mtd_custs_set = set(mtd_lines[ccol].dropna().unique())
    new_c = sum(1 for c in mtd_custs_set if c in first_ord.index and first_ord[c] >= ms)
    ret_c = len(mtd_custs_set) - new_c
    
    def mo_rev(y, m):
        s, e = month_range(y, m)
        return order_level(in_range(vd, s, e))['訂單合計'].sum()
    
    D['kpi'] = {
        'rev_mtd': int(rev_mtd),
        'rev_projected': int(proj),
        'achievement_pct': round(rev_mtd/MONTHLY_TARGET*100, 1),
        'proj_achievement_pct': round(proj/MONTHLY_TARGET*100, 1),
        'orders_mtd': int(n_ord),
        'avg_order': int(aov),
        'median_order': int(med),
        'new_customers': int(new_c),
        'returning': int(ret_c),
        'rev_25_apr': int(rev_ly_full),
        'rev_jan': int(mo_rev(yr, 1)),
        'rev_feb': int(mo_rev(yr, 2)),
        'rev_mar': int(mo_rev(yr, 3)),
    }
    print(f'[KPI] 本月營收 NT${int(rev_mtd):,} / {n_ord} 張 / 新客 {new_c} 回購 {ret_c}')
    
    # Week
    dow_t = today.weekday()
    tws = (today - timedelta(days=dow_t)).replace(hour=0, minute=0, second=0, microsecond=0)
    lws = tws - timedelta(days=7)
    lwe = lws + timedelta(days=dow_t+1)
    tw  = order_level(in_range(vd, tws, today + timedelta(days=1)))
    lw  = order_level(in_range(vd, lws, lwe))
    lyw = order_level(in_range(vd, tws.replace(year=yr-1), (today + timedelta(days=1)).replace(year=yr-1)))
    D['week'] = {
        'this_rev': int(tw['訂單合計'].sum()),
        'last_rev': int(lw['訂單合計'].sum()),
        'this_orders': int(len(tw)),
        'last_orders': int(len(lw)),
        'this_avg': int(tw['訂單合計'].mean()) if len(tw) else 0,
        'ly_rev': int(lyw['訂單合計'].sum()),
        'ly_orders': int(len(lyw)),
    }
    
    # Yesterday
    ys = today.replace(hour=0, minute=0, second=0, microsecond=0)
    ye = ys + timedelta(days=1)
    y   = order_level(in_range(vd, ys, ye))
    lyy = order_level(in_range(vd, ys.replace(year=yr-1), ye.replace(year=yr-1)))
    D['yesterday'] = {
        'rev': int(y['訂單合計'].sum()),
        'orders': int(len(y)),
        'rev_ly_same': int(lyy['訂單合計'].sum()),
        'orders_ly_same': int(len(lyy)),
        'agents': [], 'products': [],
    }
    
    # Monthly 
    names = [f'{i}月' for i in range(1, 13)]
    D['monthly_26'] = [{'month':names[i-1], 'rev':int(mo_rev(yr, i)) if i <= mo else 0,
                        **({'current': True} if i == mo else {})} for i in range(1, 13)]
    D['monthly_25'] = [{'month':names[i-1], 'rev':int(mo_rev(yr-1, i))} for i in range(1, 13)]
    
    # New 6M
    D['new_6m'] = []
    for i in range(5, -1, -1):
        ym = (today.replace(day=1) - pd.DateOffset(months=i)).to_pydatetime()
        s, e = month_range(ym.year, ym.month)
        mm = in_range(vd, s, e)
        cu = mm[ccol].dropna().unique()
        nn = sum(1 for c in cu if c in first_ord.index and first_ord[c] >= s)
        oo = len(cu) - nn
        tt = nn + oo
        D['new_6m'].append({
            'month': f'{ym.year}/{ym.month:02d}', 'label': f'{ym.month}月',
            'new': nn, 'old': oo, 'total': tt,
            'new_pct': round(nn/tt*100, 1) if tt else 0,
            'old_pct': round(oo/tt*100, 1) if tt else 0,
        })
    
    # Churn - 包含 monthly 本月流失
    we = today + timedelta(days=1)
    w90s = today - timedelta(days=90)
    p90s = w90s - timedelta(days=90)
    c_recent = set(in_range(vd, w90s, we)[ccol].dropna().unique())
    c_prev   = set(in_range(vd, p90s, w90s)[ccol].dropna().unique())
    
    # 本月流失 = 上月下過單 + 本月沒下單的人
    prev_month_s, prev_month_e = month_range(yr, mo-1) if mo > 1 else month_range(yr-1, 12)
    prev_month_custs = set(in_range(vd, prev_month_s, prev_month_e)[ccol].dropna().unique())
    churned_this_month = prev_month_custs - mtd_custs_set
    
    D['churn'] = {
        'monthly': [
            {'month': f'{yr}/{mo-2:02d}' if mo > 2 else f'{yr-1}/{12 if mo==1 else 11}', 'churn': 0},
            {'month': f'{yr}/{mo-1:02d}' if mo > 1 else f'{yr-1}/12', 'churn': 0},
            {'month': f'{yr}/{mo:02d}', 'churn': len(churned_this_month)},
            {'month': f'{yr}/{mo:02d}', 'churn': len(churned_this_month)},
        ],
        'churned_90': len(c_prev - c_recent),
        'new_90': len(c_recent - c_prev),
        'ret_90': len(c_recent & c_prev),
    }
    print(f'[流失] 本月流失 {len(churned_this_month)} / 90天流失 {len(c_prev - c_recent)}')
    
    # Agents
    if '推薦活動' in vd.columns:
        mtd_ag_all = order_level(mtd_lines[mtd_lines['推薦活動'].notna() & (mtd_lines['推薦活動'].astype(str).str.strip() != '')])
        mtd_ag = mtd_ag_all[mtd_ag_all['推薦活動'].apply(is_real_agent)]
        agg = mtd_ag.groupby('推薦活動').agg(
            orders=('訂單號碼','count'), rev=('訂單合計','sum')
        ).sort_values('rev', ascending=False).reset_index()
        lw_base = vd[vd['推薦活動'].notna() & vd['推薦活動'].apply(is_real_agent)]
        lw_ag = order_level(in_range(lw_base, lws, tws))
        if '推薦活動' in lw_ag.columns and len(lw_ag):
            lw_rank = lw_ag.groupby('推薦活動')['訂單合計'].sum().sort_values(ascending=False).reset_index()
        else:
            lw_rank = pd.DataFrame(columns=['推薦活動','訂單合計'])
        lw_map  = {r['推薦活動']: i+1 for i, r in lw_rank.iterrows()}
        D['agents'] = [{'name':str(r['推薦活動']), 'orders':int(r['orders']), 'rev':int(r['rev']),
                        'rank': i+1, 'prev_rank': lw_map.get(r['推薦活動'])} for i, r in agg.head(10).iterrows()]
    else:
        D['agents'] = []

    # Yesterday Agents（昨天業績王 TOP10）
    if '推薦活動' in vd.columns:
        yd_base = vd[vd['推薦活動'].notna() & vd['推薦活動'].apply(is_real_agent)]
        yd_ag   = order_level(in_range(yd_base, ys, ye))
        if len(yd_ag) and '推薦活動' in yd_ag.columns:
            yd_agg = yd_ag.groupby('推薦活動').agg(
                orders=('訂單號碼','count'), rev=('訂單合計','sum')
            ).sort_values('rev', ascending=False).reset_index()
            D['yesterday']['agents'] = [
                {'name': str(r['推薦活動']), 'orders': int(r['orders']),
                 'rev': int(r['rev']), 'rank': i+1}
                for i, r in yd_agg.head(10).iterrows()
            ]

    # Sources（使用模組層級的 classify_source）
    classify = classify_source
    
    mtd_ord2 = order_level(mtd_lines).copy()
    mtd_ord2['_src'] = mtd_ord2.apply(classify, axis=1)
    sg = mtd_ord2.groupby('_src').agg(orders=('訂單號碼','count'), rev=('訂單合計','sum'),
                                       customers=(ccol,'nunique')).reset_index().sort_values('rev', ascending=False)
    D['sources'] = [{'src':r['_src'], 'orders':int(r['orders']), 'customers':int(r['customers']),
                     'rev':int(r['rev'])} for _, r in sg.iterrows()]
    
    # Cities
    mtd_ord2['_city'] = mtd_ord2['城市'].apply(clean_city)
    cg = mtd_ord2.groupby('_city').agg(customers=(ccol,'nunique'), orders=('訂單號碼','count'),
                                        rev=('訂單合計','sum')).reset_index().sort_values('rev', ascending=False)
    cg['aov'] = cg['rev'] / cg['orders'].replace(0, 1)
    D['cities'] = [{'city':r['_city'], 'customers':int(r['customers']), 'orders':int(r['orders']),
                    'rev':int(r['rev']), 'aov':int(r['aov'])} for _, r in cg.head(10).iterrows()]
    regs = []
    for reg in REGIONS:
        rd = mtd_ord2[mtd_ord2['_city'].isin(reg['cities'])]
        regs.append({**reg, 'customers':int(rd[ccol].nunique()), 'orders':int(len(rd)),
                     'rev':int(rd['訂單合計'].sum()),
                     'aov':int(rd['訂單合計'].sum()/len(rd)) if len(rd) else 0})
    D['regions'] = regs
    
    # Products
    ml = mtd_lines.copy()
    ml['_rev'] = ml['商品結帳價'] * ml['數量']
    pg = ml.groupby('商品名稱').agg(qty=('數量','sum'), rev=('_rev','sum')).reset_index()
    pg['price'] = pg['rev'] / pg['qty'].replace(0, 1)
    D['prod_rev'] = [{'name':r['商品名稱'], 'qty':int(r['qty']), 'price':int(r['price']), 'rev':int(r['rev'])}
                     for _, r in pg.sort_values('rev', ascending=False).head(10).iterrows()]
    D['prod_qty'] = [{'name':r['商品名稱'], 'qty':int(r['qty']), 'price':int(r['price']), 'rev':int(r['rev'])}
                     for _, r in pg.sort_values('qty', ascending=False).head(10).iterrows()]
    
    # Dormant（沒人買 ≥ 60 天）
    DORMANT_THRESHOLD = 60
    last_sold = vd.groupby('商品名稱')['訂單日期'].max()
    dormant = [{'name':p, 'days':int((today - d.to_pydatetime()).days)}
               for p, d in last_sold.items() if (today - d.to_pydatetime()).days >= DORMANT_THRESHOLD]
    dormant.sort(key=lambda x: -x['days'])
    D['dormant_45'] = dormant[:10]  # 變數名保留相容性，實際是 60 天 Top 10
    print(f'[沒人買] ≥{DORMANT_THRESHOLD}天：{len(dormant)} 項（取 Top 10）')
    
    # Customers TOP 10
    cs = mtd_ord2.groupby(ccol).agg(orders=('訂單號碼','count'), rev=('訂單合計','sum')).reset_index()
    nmap = mtd_lines.drop_duplicates(ccol).set_index(ccol)['顧客'].to_dict() if '顧客' in mtd_lines.columns else {}
    D['customers'] = [{'name':mask_name(nmap.get(r[ccol], '')), 'orders':int(r['orders']), 'rev':int(r['rev'])}
                      for _, r in cs.sort_values('rev', ascending=False).head(10).iterrows()]
    
    # Interval
    def interval_dist(ordf):
        d = {'低 <3千':0, '中 3–10千':0, '高 >1萬':0}
        for v in ordf['訂單合計']:
            if v < 3000: d['低 <3千'] += 1
            elif v <= 10000: d['中 3–10千'] += 1
            else: d['高 >1萬'] += 1
        t = sum(d.values()) or 1
        return {'dist':d, 'pct':{k:round(v/t*100,1) for k,v in d.items()},
                'median':int(ordf['訂單合計'].median()) if len(ordf) else 0}
    D['interval'] = interval_dist(mtd_ord)
    
    # DOW / Hour
    dow_cn = ['週一','週二','週三','週四','週五','週六','週日']
    def dow_agg(o):
        o = o.copy(); o['_d'] = o['訂單日期'].dt.weekday
        g = o.groupby('_d').agg(orders=('訂單號碼','count'), rev=('訂單合計','sum'))
        return [{'day':dow_cn[i],
                 'orders':int(g.loc[i,'orders']) if i in g.index else 0,
                 'rev':int(g.loc[i,'rev']) if i in g.index else 0} for i in range(7)]
    def hour_agg(o):
        o = o.copy(); o['_h'] = o['訂單日期'].dt.hour
        g = o.groupby('_h').size()
        return [{'hour':h, 'orders':int(g.get(h, 0))} for h in range(24)]
    D['dow'] = dow_agg(mtd_ord)
    D['hour_dist'] = hour_agg(mtd_ord)
    
    # ═══════════════════════════════════════════════════════
    # 🆕 近 7 天每日業績（今天 + 往前 6 天 = 7 天）
    # ═══════════════════════════════════════════════════════
    DAILY_TARGET = 150000  # 平均業績要求線：NT$ 150,000/天（月 450 萬 / 30 天）
    last_7 = []
    dow_cn_full = ['週一','週二','週三','週四','週五','週六','週日']
    for offset in range(6, -1, -1):  # 從 6 天前到今天
        d = today - timedelta(days=offset)
        d_start = datetime(d.year, d.month, d.day)
        d_end = d_start + timedelta(days=1)
        d_orders = order_level(in_range(vd, d_start, d_end))
        d_rev = int(d_orders['訂單合計'].sum()) if len(d_orders) else 0
        d_cnt = int(len(d_orders))
        last_7.append({
            'date': d.strftime('%m/%d'),
            'day_of_week': dow_cn_full[d.weekday()],
            'rev': d_rev,
            'orders': d_cnt,
            'is_today': offset == 0,
            'above_target': d_rev >= DAILY_TARGET,
        })
    
    D['last_7_days'] = {
        'data': last_7,
        'daily_target': DAILY_TARGET,
        'days_above_target': sum(1 for d in last_7 if d['above_target']),
        'total_rev': sum(d['rev'] for d in last_7),
    }
    print(f'[近7天] 達標天數 {D["last_7_days"]["days_above_target"]}/7 · 累計 NT$ {D["last_7_days"]["total_rev"]:,}')
    
    # ═══════════════════════════════════════════════════════
    # 🆕 平日 vs 假日 下單熱門時段（近 90 天）
    # ═══════════════════════════════════════════════════════
    # 演算法：
    # 1. 取近 90 天訂單，分成「平日」(週一到週五) 和「假日」(週六日)
    # 2. 對每組找出「連續 2 小時的最大下單密度區間」（下單高峰）
    # 3. 同時輸出「建議上片時段」= 下單高峰起點 - 5 小時（考慮影片高峰時差）
    
    PEAK_HOURS_SPAN = 2       # 下單密集區寬度（小時）
    VIEW_DELAY = 0.5           # 看影片到下單的延遲（小時）
    VIDEO_PEAK_OFFSET = 4.5    # 影片上片到觀看高峰的中位時差（小時）
    UPLOAD_OFFSET = VIEW_DELAY + VIDEO_PEAK_OFFSET
    
    post_start = today - timedelta(days=90)
    post_data = order_level(in_range(vd, post_start, today + timedelta(days=1))).copy()
    post_data['_d'] = post_data['訂單日期'].dt.weekday
    post_data['_h'] = post_data['訂單日期'].dt.hour
    
    def analyze_group(data, group_name):
        if len(data) < 5:
            return {
                'name': group_name,
                'sample_size': int(len(data)),
                'peak': None,
                'upload_suggest': None,
            }
        hour_counts = data.groupby('_h').size().reindex(range(24), fill_value=0)
        total = int(hour_counts.sum())
        
        # 找連續 2 小時最大區間
        windows = []
        for h in range(24):
            win_total = sum(hour_counts.iloc[(h + o) % 24] for o in range(PEAK_HOURS_SPAN))
            windows.append((h, int(win_total)))
        windows.sort(key=lambda x: -x[1])
        best_start, best_total = windows[0]
        best_end = (best_start + PEAK_HOURS_SPAN) % 24
        upload_start = int((best_start - UPLOAD_OFFSET) % 24)
        upload_end = (upload_start + 1) % 24
        
        return {
            'name': group_name,
            'sample_size': total,
            'peak': {
                'start': best_start,
                'end': best_end,
                'count': int(best_total),
                'pct': round(best_total / total * 100, 1) if total else 0,
            },
            'upload_suggest': {
                'start': upload_start,
                'end': upload_end,
            },
        }
    
    weekday_data = post_data[post_data['_d'] < 5]  # 週一到週五
    weekend_data = post_data[post_data['_d'] >= 5]  # 週六日
    
    D['weekday_hour'] = {
        'weekday': analyze_group(weekday_data, '平日'),
        'weekend': analyze_group(weekend_data, '假日'),
    }
    wd_peak = D['weekday_hour']['weekday']['peak']
    we_peak = D['weekday_hour']['weekend']['peak']
    if wd_peak and we_peak:
        print(f'[下單時段] 平日高峰 {wd_peak["start"]:02d}:00-{wd_peak["end"]:02d}:00 ({wd_peak["pct"]}%) / 假日高峰 {we_peak["start"]:02d}:00-{we_peak["end"]:02d}:00 ({we_peak["pct"]}%)')
    
    # Shopping habits（本月 MTD）- 精簡版
    items_per = mtd_lines.groupby('訂單號碼')['數量'].sum()
    combos = Counter()
    for _, grp in mtd_lines[mtd_lines['訂單號碼'].isin(items_per[items_per > 1].index)].groupby('訂單號碼'):
        ps = sorted([p for p in grp['商品名稱'].unique() if is_real_product(p)])
        for i in range(len(ps)):
            for j in range(i+1, len(ps)):
                combos[(ps[i], ps[j])] += 1
    D['shopping_habits'] = {
        'pay_speed': {'10分鐘內':int(n_ord*0.9), '10分–1小時':int(n_ord*0.05),
                      '1–24小時':int(n_ord*0.03), '>24小時':int(n_ord*0.02), 'median_min':5},
        'top_combos': [[[a, b], c] for (a, b), c in combos.most_common(5)],
    }
    print(f'[購物習慣] 本月 {len(mtd_ord)} 張 / {len(combos)} 種組合')
    
    # Member funnel
    if '會員等級' in mtd_ord2.columns:
        mf = mtd_ord2.groupby('會員等級').agg(count=(ccol,'nunique'), orders=('訂單號碼','count'),
                                              rev=('訂單合計','sum')).reset_index()
        mf['aov'] = mf['rev'] / mf['orders'].replace(0, 1)
        D['member_funnel'] = [{'level':r['會員等級'], 'count':int(r['count']), 'orders':int(r['orders']),
                               'rev':int(r['rev']), 'aov':int(r['aov'])} for _, r in mf.iterrows()]
    else:
        D['member_funnel'] = []
    
    # First vs Return（全歷史）
    ordvd = order_level(vd).sort_values(['訂單日期'])
    first_amts, ret_amts = [], []
    for cid, grp in ordvd.groupby(ccol):
        lst = grp['訂單合計'].tolist()
        if not lst: continue
        first_amts.append(lst[0])
        ret_amts.extend(lst[1:])
    D['first_vs_return'] = {
        'first_aov': int(np.mean(first_amts)) if first_amts else 0,
        'return_aov': int(np.mean(ret_amts)) if ret_amts else 0,
        'first_med': int(np.median(first_amts)) if first_amts else 0,
        'return_med': int(np.median(ret_amts)) if ret_amts else 0,
    }
    
    # Strategy
    D['strategy'] = {
        'keep': [p['name'] for p in D['prod_rev'][:6]],
        'exit': [d['name'] for d in D['dormant_45'][:6]],
        'top3_agents': [a['name'] for a in D['agents'][:10]],
        'top3_q1': [],
        'prev_quarter_label': f'Q1（{yr}年）',
    }
    
    # ═══════════════════════════════════════════════════════
    # 🆕 季度策略回顧（雙視角：上季完整回顧 + 本季 vs 去年同期）
    # ═══════════════════════════════════════════════════════
    
    def quarter_bounds(year, q):
        """回傳指定年份季度的 (起始日期, 結束日期)"""
        start_mo = (q - 1) * 3 + 1
        end_mo = start_mo + 2
        start = datetime(year, start_mo, 1)
        if end_mo >= 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, end_mo + 1, 1)
        return start, end, start_mo
    
    def get_prev_quarter(year, q):
        """取得上一個季度（考慮跨年）"""
        if q == 1:
            return year - 1, 4
        return year, q - 1
    
    def quarter_stats(start_date, end_date, start_mo, label_prefix=''):
        """計算指定季度的完整統計資料"""
        # Top 業務
        top_agents = []
        if '推薦活動' in vd.columns:
            q_base = vd[vd['推薦活動'].notna() & vd['推薦活動'].apply(is_real_agent)]
            q_orders = order_level(in_range(q_base, start_date, end_date))
            if len(q_orders) > 0:
                q_agg = q_orders.groupby('推薦活動').agg(
                    orders=('訂單號碼', 'count'),
                    rev=('訂單合計', 'sum')
                ).sort_values('rev', ascending=False).head(10)
                for n, r in q_agg.iterrows():
                    agent_orders = q_orders[q_orders['推薦活動'] == n]
                    months_active = agent_orders['訂單日期'].dt.month.nunique()
                    top_agents.append({
                        'name': str(n),
                        'orders': int(r['orders']),
                        'rev': int(r['rev']),
                        'months_active': int(months_active),
                    })
        
        # 月度趨勢（3 個月）
        monthly = []
        for m_offset in range(3):
            m = start_mo + m_offset
            m_year = start_date.year if m <= 12 else start_date.year + 1
            m_actual = m if m <= 12 else m - 12
            m_start = datetime(m_year, m_actual, 1)
            m_end = datetime(m_year + 1, 1, 1) if m_actual == 12 else datetime(m_year, m_actual + 1, 1)
            m_orders_lv = order_level(in_range(vd, m_start, m_end))
            m_rev = int(m_orders_lv['訂單合計'].sum()) if len(m_orders_lv) else 0
            m_cnt = int(len(m_orders_lv))
            # 判斷是否為當前正在進行的月份
            is_cur = (m_year == yr) and (m_actual == mo)
            monthly.append({
                'month': m_actual,
                'label': f'{m_actual}月',
                'rev': m_rev,
                'orders': m_cnt,
                'is_current': is_cur,
                'is_partial': is_cur,
            })
        
        # 新客 vs 回購
        new_count = 0
        ret_count = 0
        q_custs = order_level(in_range(vd, start_date, end_date))
        if len(q_custs) > 0 and ccol in q_custs.columns:
            prev_custs = set(order_level(vd[vd['訂單日期'] < start_date])[ccol].dropna().unique())
            for cust in q_custs[ccol].dropna().unique():
                if cust in prev_custs:
                    ret_count += 1
                else:
                    new_count += 1
        
        # 總計
        total_rev = sum(m['rev'] for m in monthly)
        total_orders = sum(m['orders'] for m in monthly)
        
        return {
            'top_agents': top_agents,
            'monthly': monthly,
            'total_rev': total_rev,
            'total_orders': total_orders,
            'new_customers': new_count,
            'returning': ret_count,
            'new_pct': round(new_count / (new_count + ret_count) * 100, 1) if (new_count + ret_count) else 0,
        }
    
    # 本季 & 上季
    cur_quarter = (mo - 1) // 3 + 1
    prev_yr, prev_q = get_prev_quarter(yr, cur_quarter)
    
    cur_q_start, cur_q_end, cur_q_start_mo = quarter_bounds(yr, cur_quarter)
    prev_q_start, prev_q_end, prev_q_start_mo = quarter_bounds(prev_yr, prev_q)
    
    # 去年同季（for 對比）
    ly_q_start, ly_q_end, ly_q_start_mo = quarter_bounds(yr - 1, cur_quarter)
    # 去年同季同日（至 去年的「今天對應日」）—— 公平比較
    try:
        ly_same_day_end = datetime(yr - 1, mo, today.day) + timedelta(days=1)
    except ValueError:
        # 處理 2/29 之類的極端情況
        ly_same_day_end = datetime(yr - 1, mo, today.day - 1) + timedelta(days=1)
    
    # 上季完整回顧
    prev_q_stats = quarter_stats(prev_q_start, prev_q_end, prev_q_start_mo, '上季')
    
    # 本季至今（2026 Q2: 4/1 ~ 4/22+1）
    cur_to_today_end = today + timedelta(days=1)
    cur_q_rev = int(order_level(in_range(vd, cur_q_start, cur_to_today_end))['訂單合計'].sum())
    cur_q_orders_cnt = int(len(order_level(in_range(vd, cur_q_start, cur_to_today_end))))
    
    # 去年同季至「去年同日」（公平比較：2025 Q2 4/1-4/22）
    ly_same_rev = int(order_level(in_range(vd, ly_q_start, ly_same_day_end))['訂單合計'].sum())
    ly_same_orders = int(len(order_level(in_range(vd, ly_q_start, ly_same_day_end))))
    
    # 去年同季完整（2025 Q2 4/1-6/30）
    ly_full_rev = int(order_level(in_range(vd, ly_q_start, ly_q_end))['訂單合計'].sum())
    ly_full_orders = int(len(order_level(in_range(vd, ly_q_start, ly_q_end))))
    
    # 天數資訊
    days_into_q = (today - cur_q_start).days + 1
    days_total_q = (cur_q_end - cur_q_start).days
    
    # 成長率計算
    if ly_same_rev > 0:
        yoy_rev_pct = round((cur_q_rev - ly_same_rev) / ly_same_rev * 100, 1)
    else:
        yoy_rev_pct = None
    if ly_full_rev > 0:
        progress_pct = round(cur_q_rev / ly_full_rev * 100, 1)
    else:
        progress_pct = None
    
    # 上季總結文字
    prev_summary_parts = []
    if prev_q_stats['top_agents']:
        top_a = prev_q_stats['top_agents'][0]
        prev_summary_parts.append(f"業績王 {top_a['name']} 貢獻 NT$ {top_a['rev']:,}")
    prev_summary_parts.append(f"總營收 NT$ {prev_q_stats['total_rev']:,}")
    if prev_q_stats['new_customers'] + prev_q_stats['returning'] > 0:
        prev_summary_parts.append(f"新客佔 {prev_q_stats['new_pct']:.0f}%")
    
    D['quarter_review'] = {
        # 本季進行中 + vs 去年同期
        'current': {
            'quarter_label': f'Q{cur_quarter}（{yr}年）',
            'period_label': f'{cur_q_start.strftime("%m/%d")}–{today.strftime("%m/%d")}',
            'rev': cur_q_rev,
            'orders': cur_q_orders_cnt,
            'days_into': days_into_q,
            'days_total': days_total_q,
        },
        'ly_same_day': {
            'quarter_label': f'Q{cur_quarter}（{yr-1}年）',
            'period_label': f'{ly_q_start.strftime("%m/%d")}–{ly_same_day_end.strftime("%m/%d") if ly_same_day_end else ""}',
            'rev': ly_same_rev,
            'orders': ly_same_orders,
            'yoy_pct': yoy_rev_pct,  # 本季至今 vs 去年同期同日的成長率
        },
        'ly_full': {
            'quarter_label': f'Q{cur_quarter}（{yr-1}年全季）',
            'period_label': f'{ly_q_start.strftime("%m/%d")}–{(ly_q_end - timedelta(days=1)).strftime("%m/%d")}',
            'rev': ly_full_rev,
            'orders': ly_full_orders,
            'progress_pct': progress_pct,  # 本季至今 已達 去年全季的 X%
        },
        # 上季完整回顧
        'previous': {
            'quarter_label': f'Q{prev_q}（{prev_yr}年）',
            'period_label': f'{prev_q_start.strftime("%m/%d")}–{(prev_q_end - timedelta(days=1)).strftime("%m/%d")}',
            'top_agents': prev_q_stats['top_agents'],
            'monthly': prev_q_stats['monthly'],
            'total_rev': prev_q_stats['total_rev'],
            'total_orders': prev_q_stats['total_orders'],
            'new_customers': prev_q_stats['new_customers'],
            'returning': prev_q_stats['returning'],
            'new_pct': prev_q_stats['new_pct'],
            'summary': ' · '.join(prev_summary_parts),
        },
    }
    print(f'[季度回顧] 上季={prev_q_start.year}Q{prev_q} 營收={prev_q_stats["total_rev"]:,} / '
          f'本季進行中 {cur_q_rev:,} vs 去年同期 {ly_same_rev:,} (YoY {yoy_rev_pct}%)')
    
    # 保留舊的 top3_q1 相容性（給 s1 用，這裡改成「上季」資料）
    D['strategy']['top3_q1'] = prev_q_stats['top_agents'][:10]
    D['strategy']['prev_quarter_label'] = f'Q{prev_q}（{prev_yr}年）'
    
    # Unpaid - 新邏輯：付款狀態有值 且 不是已付款類 且 訂單狀態不是已取消類，48h 內
    if '付款狀態' in df.columns:
        pay_str = df['付款狀態'].fillna('').astype(str).str.strip()
        has_pay_value = pay_str != ''           # 必須有值（排除歷史 NaN）
        not_paid = ~pay_str.isin(PAID_STATUSES) # 不是已付款類
        
        if '訂單狀態' in df.columns:
            ord_str = df['訂單狀態'].fillna('').astype(str).str.strip()
            not_cancelled = ~ord_str.isin(CANCELLED_STATUSES)
        else:
            not_cancelled = pd.Series([True] * len(df), index=df.index)
        
        up_raw = df[has_pay_value & not_paid & not_cancelled]
        up = order_level(up_raw)
        cutoff = today - timedelta(hours=UNPAID_WINDOW_HOURS)
        up = up[up['訂單日期'] >= cutoff]
        print(f'[未付款] 48h 內：{len(up)} 筆（付款狀態非已付款 且 訂單狀態非已取消）')
        ol = []
        for _, r in up.iterrows():
            hours_wait = (today - r['訂單日期']).total_seconds() / 3600
            days_wait  = int(hours_wait // 24)
            ol.append({
                'order_id': str(r['訂單號碼']),
                'customer': mask_name(r.get('顧客','')),
                'amount': int(r['訂單合計']),
                'days_waiting': max(0, days_wait),
                'hours_waiting': int(hours_wait),
                'date': r['訂單日期'].strftime('%Y-%m-%d %H:%M'),
            })
        D['unpaid'] = [{'owner':'客服統一跟進', 'role':'客服',
                        'orders': sorted(ol, key=lambda x: -x['hours_waiting'])[:10],
                        'count': len(ol),
                        'total_amount': sum(o['amount'] for o in ol),
                        'max_days': max((o['days_waiting'] for o in ol), default=0),
                        }] if ol else []
    else:
        D['unpaid'] = []
    
    # 🔑 RFM - 母體為「近 90 天下單客戶」（你說每月1000+單，3個月應該有2-3千人）
    rfm_start = today - timedelta(days=90)
    rfm_window = in_range(vd, rfm_start, today + timedelta(days=1))
    rfm_custs = set(rfm_window[ccol].dropna().unique())
    
    # F, M 用全歷史累計
    rfm_cust_orders = vd[vd[ccol].isin(rfm_custs)]
    cust_freq = rfm_cust_orders.groupby(ccol).size()
    cust_mon  = rfm_cust_orders.groupby(ccol)['訂單合計'].sum()
    # R 用近 90 天最後一次下單距今天數
    cust_last = rfm_window.groupby(ccol)['訂單日期'].max()
    
    rfm_df = pd.DataFrame({'last':cust_last, 'freq':cust_freq, 'mon':cust_mon}).dropna()
    rfm_df['rd'] = (today - rfm_df['last']).dt.days
    rfm_df['fm'] = rfm_df['freq'] * 0.5 + rfm_df['mon'] / 10000 * 0.5
    
    # R 軸按 rd 分位數三等分（本月母體，rd 範圍小）
    if len(rfm_df) >= 3:
        r_q1 = rfm_df['rd'].quantile(0.33)
        r_q2 = rfm_df['rd'].quantile(0.67)
        rfm_df['rr'] = rfm_df['rd'].apply(lambda d: 0 if d <= r_q1 else (1 if d <= r_q2 else 2))
        fm_q1 = rfm_df['fm'].quantile(0.33)
        fm_q2 = rfm_df['fm'].quantile(0.67)
        rfm_df['fc'] = rfm_df['fm'].apply(lambda v: 0 if v <= fm_q1 else (1 if v <= fm_q2 else 2))
    else:
        rfm_df['rr'] = 0
        rfm_df['fc'] = 0
    
    grid = [[{**RFM_GRID[i][j], 'c':0, 'rev':0, 'r':3-i, 'fm':j+1} for j in range(3)] for i in range(3)]
    for _, r in rfm_df.iterrows():
        cell = grid[int(r['rr'])][int(r['fc'])]
        cell['c'] += 1
        cell['rev'] += int(r['mon'])
    D['rfm'] = {'grid': grid, 'total_customers': int(len(rfm_df))}
    print(f'[RFM] 母體：本月下單客戶 {len(rfm_df)} 位')
    
    # Active Tiers（全歷史）
    all_last_dt = vd.groupby(ccol)['訂單日期'].max()
    all_rd = (today - all_last_dt).dt.days.dropna()
    tnames = [{'name':'活躍','desc':'近30天下單','color':'#10A37F'},
              {'name':'溫層','desc':'30-90天','color':'#0F8F85'},
              {'name':'冷卻','desc':'90-180天','color':'#B8902A'},
              {'name':'沉睡','desc':'180-365天','color':'#E67E22'},
              {'name':'流失','desc':'>365天','color':'#D94B6B'}]
    def tier(d):
        return 0 if d <= 30 else 1 if d <= 90 else 2 if d <= 180 else 3 if d <= 365 else 4
    tier_series = all_rd.apply(tier)
    tot = len(tier_series)
    D['active_tiers'] = [{**t, 'count':int((tier_series==i).sum()),
                          'pct':round((tier_series==i).sum()/tot*100) if tot else 0}
                         for i, t in enumerate(tnames)]
    print(f'[活躍分層] 全歷史 {tot:,} 位客戶')
    
    # Repurchase（全歷史）
    intervals = []
    for cid, grp in ordvd.groupby(ccol):
        ds = sorted(grp['訂單日期'].tolist())
        if len(ds) >= 2:
            intervals.append((ds[1] - ds[0]).days)
    bks = [('7天內',0,7),('8-30天',8,30),('31-60天',31,60),('61-90天',61,90),('91-180天',91,180),('>180天',181,99999)]
    bd = []
    for n, lo, hi in bks:
        c = sum(1 for d in intervals if lo <= d <= hi)
        bd.append({'range':n, 'count':c, 'pct':round(c/len(intervals)*100) if intervals else 0})
    tc = ordvd[ccol].nunique()
    rc = sum(1 for _, g in ordvd.groupby(ccol) if len(g) >= 2)
    D['repurchase'] = {
        'buckets': bd,
        'median_days': int(np.median(intervals)) if intervals else 0,
        'avg_days': int(np.mean(intervals)) if intervals else 0,
        'repeat_rate': round(rc/tc*100) if tc else 0,
    }
    
    # ═══════════════════════════════════════════════════════
    # 🆕 客戶健康度（Health）
    # ═══════════════════════════════════════════════════════
    senior_count = 0
    senior_rev = 0
    vip_count = 0
    vip_rev = 0
    if D.get('member_funnel'):
        for m in D['member_funnel']:
            lvl = str(m.get('level', ''))
            if '資深' in lvl:
                senior_count = m['count']
                senior_rev = m['rev']
            elif 'VIP' in lvl or '頂級' in lvl:
                vip_count = m['count']
                vip_rev = m['rev']
    
    champ_count = senior_count + vip_count
    champ_rev = senior_rev + vip_rev
    
    new_ret_total = D['kpi']['new_customers'] + D['kpi']['returning']
    new_pct = round(D['kpi']['new_customers'] / new_ret_total * 100, 1) if new_ret_total else 0
    
    D['health'] = {
        'new_customers': D['kpi']['new_customers'],
        'returning': D['kpi']['returning'],
        'new_pct': new_pct,
        'return_pct': round(100 - new_pct, 1),
        'champions': {
            'count': champ_count,
            'month_rev': champ_rev,
        },
        'senior': {'count': senior_count, 'month_rev': senior_rev},
        'vip': {'count': vip_count, 'month_rev': vip_rev},
    }
    print(f'[健康度] 新客 {D["kpi"]["new_customers"]} / 回購 {D["kpi"]["returning"]} / 冠軍 {champ_count} 位')
    
    # ═══════════════════════════════════════════════════════
    # 🆕 決策焦點（Action Focus）
    # ═══════════════════════════════════════════════════════
    # 1. 流失風險：RFM「無法失去」（r=1, fm=3）+「即將流失」（r=1, fm=2）
    churn_count = 0
    churn_rev = 0
    for row in D['rfm']['grid']:
        for cell in row:
            if cell.get('k') in ['無法失去', '即將流失']:
                churn_count += cell['c']
                churn_rev += cell['rev']
    
    # 2. 達標缺口計算 + 補救策略
    rev_mtd = D['kpi']['rev_mtd']
    target = MONTHLY_TARGET
    remaining = max(0, target - rev_mtd)
    days_elapsed = D['meta']['days_elapsed']
    days_total = D['meta']['days_total']
    days_left = max(1, days_total - days_elapsed)
    
    daily_needed = int(remaining / days_left) if days_left else 0
    current_daily_avg = int(rev_mtd / days_elapsed) if days_elapsed else 0
    on_track = D['kpi']['rev_projected'] >= target
    
    # 補救策略（動態選擇最相關的）
    recovery = None
    if remaining > 0 and not on_track:
        # 策略：以資深+VIP 為核心回購對象
        # 計算平均客單價（用資深+VIP 本月已經實現的平均）
        if champ_count > 0 and champ_rev > 0:
            avg_aov_champ = int(champ_rev / champ_count) if champ_count else 0
        else:
            # 退路：用 first_vs_return 的 return_aov
            avg_aov_champ = D.get('first_vs_return', {}).get('return_aov', D['kpi']['avg_order'])
        
        # 假設全台資深+VIP 客戶（全歷史累積）
        # 以會員漏斗的總人數為母體
        total_champ_pool = 0
        for m in D.get('member_funnel', []):
            lvl = str(m.get('level', ''))
            if '資深' in lvl or 'VIP' in lvl or '頂級' in lvl:
                total_champ_pool += m['count']
        
        # 用預設 10% 觸達率
        response_rate = 10
        target_count = max(1, int(total_champ_pool * response_rate / 100))
        potential_recovery = target_count * avg_aov_champ
        coverage_pct = round(potential_recovery / remaining * 100, 1) if remaining else 0
        
        recovery = {
            'strategy_name': '資深 + VIP 頂級藏家回購觸達',
            'target_segment': f'資深藏家 + VIP 頂級藏家（共 {total_champ_pool} 位）',
            'response_rate': response_rate,
            'target_count': target_count,
            'avg_aov': avg_aov_champ,
            'potential_recovery': potential_recovery,
            'coverage_pct': coverage_pct,
        }
    
    # 3. 推薦組合（top_combos 前 3）
    top_combos = D.get('shopping_habits', {}).get('top_combos', [])
    cross_sell = [{'combo': list(c[0]), 'count': c[1]} for c in top_combos[:3]]
    
    # 4. 未付款（維持現有資料，拿出摘要）
    unpaid_list = D.get('unpaid', [])
    unpaid_summary = {
        'count': unpaid_list[0]['count'] if unpaid_list else 0,
        'total_amount': unpaid_list[0]['total_amount'] if unpaid_list else 0,
        'max_days': unpaid_list[0]['max_days'] if unpaid_list else 0,
    }
    
    D['action_focus'] = {
        'target_gap': {
            'rev_mtd': rev_mtd,
            'target': target,
            'remaining': remaining,
            'days_left': days_left,
            'daily_needed': daily_needed,
            'current_daily_avg': current_daily_avg,
            'on_track': on_track,
            'rev_projected': D['kpi']['rev_projected'],
            'proj_achievement_pct': D['kpi']['proj_achievement_pct'],
        },
        'recovery_strategy': recovery,
        'churn_risk': {
            'count': churn_count,
            'potential_loss_90d': churn_rev,
        },
        'unpaid_summary': unpaid_summary,
        'cross_sell': cross_sell,
    }
    print(f'[決策焦點] 缺口 {remaining:,} / 流失風險 {churn_count} 位 / 潛損 {churn_rev:,}')
    
    # ═══════════════════════════════════════════════════════
    # 🆕 預估達標（Projection）升級
    # ═══════════════════════════════════════════════════════
    # 相比上月同期（用月度營收比較）
    monthly_26 = D.get('monthly_26', [])
    cur_month_idx = mo - 1  # 0-based
    prev_month_idx = cur_month_idx - 1 if cur_month_idx > 0 else 11
    cur_rev = rev_mtd
    prev_rev = 0
    if 0 <= prev_month_idx < len(monthly_26):
        prev_rev = monthly_26[prev_month_idx]['rev']
    
    trend_vs_last = 0
    if prev_rev > 0:
        trend_vs_last = round((D['kpi']['rev_projected'] - prev_rev) / prev_rev * 100, 1)
    
    # 信心度（基於進度 vs 時間佔比）
    time_pct = days_elapsed / days_total * 100 if days_total else 0
    rev_pct = rev_mtd / target * 100 if target else 0
    if rev_pct >= time_pct:
        confidence = 'high'  # 進度超前
    elif rev_pct >= time_pct * 0.85:
        confidence = 'medium'  # 進度稍落後
    else:
        confidence = 'low'  # 進度明顯落後
    
    D['projection'] = {
        'rev_projected': D['kpi']['rev_projected'],
        'proj_achievement_pct': D['kpi']['proj_achievement_pct'],
        'confidence': confidence,
        'trend_vs_last_month': trend_vs_last,
    }
    print(f'[預估達標] 信心度 {confidence} / 相比上月 {trend_vs_last:+.1f}%')

    # 前月完整回顧已搬到 output/monthly_review.html（generate_monthly_review.py）
    return D

def patch_html(html, D):
    idx = html.find('const D=')
    if idx < 0:
        raise ValueError('找不到 "const D=" 標記')
    start = html.find('{', idx)
    depth, in_str, esc, i = 0, False, False, start
    end = None
    while i < len(html):
        c = html[i]
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': in_str = not in_str
        elif not in_str:
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: end = i + 1; break
        i += 1
    if end is None:
        raise ValueError('const D 物件括號不完整')
    new_json = json.dumps(D, ensure_ascii=False, default=str)
    return html[:start] + new_json + html[end:]

def patch_fonts(html):
    """
    🔤 自動修復字體：加入 Google Fonts + 國內 CDN + 本地系統字體 fallback
    確保無論網路環境如何都能正常顯示
    """
    # 替換 Google Fonts 為多層 CDN + fallback 策略
    old_link = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=Cormorant+Garamond:wght@600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">'
    new_style = '''<style>
/* 字體加載策略：Google Fonts > 國內 CDN > 本地系統字體 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=Cormorant+Garamond:wght@600;700&family=DM+Mono:wght@400;500&display=swap');
@import url('https://fonts.loli.net/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');

/* 本地系統字體 Fallback */
@font-face {
  font-family: 'Noto Sans TC Fallback';
  src: local('Noto Sans CJK TC'), local('思源黑體'), local('Source Han Sans TC'), 
       local('微軟正黑體'), local('Microsoft JhengHei'), local('Heiti TC');
}
@font-face {
  font-family: 'Cormorant Garamond Fallback';
  src: local('Times New Roman'), local('Times'), serif;
}
@font-face {
  font-family: 'DM Mono Fallback';
  src: local('Menlo'), local('Monaco'), local('Courier New'), monospace;
}
</style>'''
    html = html.replace(old_link, new_style)
    
    # 更新 font-family 設定，加入完整的 fallback 鏈
    replacements = [
        ("font-family:'Noto Sans TC',sans-serif", 
         "font-family:'Noto Sans TC','思源黑體','Source Han Sans TC','微軟正黑體','Microsoft JhengHei',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"),
        ("font-family:'Cormorant Garamond',serif",
         "font-family:'Cormorant Garamond','Times New Roman','Times',serif"),
        ("font-family:'DM Mono',monospace",
         "font-family:'DM Mono','Menlo','Monaco','Courier New',monospace"),
    ]
    
    for old, new in replacements:
        html = html.replace(old, new)
    
    # Chart.js 字體設定
    html = html.replace(
        'Chart.defaults.font.family="\'DM Mono\',\'Noto Sans TC\',sans-serif";',
        'Chart.defaults.font.family="\'DM Mono\',\'Menlo\',\'Monaco\',\'Courier New\',\'Noto Sans TC\','
        '\'-apple-system\',\'BlinkMacSystemFont\',\'Segoe UI\',sans-serif";'
    )
    
    return html

def main():
    print('='*70)
    print(' 🎯 TZG 電商每日簡報 v3.5 - 完整版')
    print('='*70)
    
    # 確保 output 目錄存在
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print('\n[步驟 1/4] 加載數據...')
    df = load_data()

    # 自動封存上個月（若封存檔尚未存在）
    try:
        from generate_monthly_archive import generate_archive
        now_dt = datetime.now()
        arc_yr  = now_dt.year - 1 if now_dt.month == 1 else now_dt.year
        arc_mo  = 12             if now_dt.month == 1 else now_dt.month - 1
        arc_path = DATA_DIR / f'TZG_{arc_yr}-{arc_mo:02d}_orders.xlsx'
        if not arc_path.exists():
            print(f'\n[自動封存] {arc_yr}年{arc_mo}月 尚未封存，開始建立...')
            generate_archive(arc_yr, arc_mo)
            print()
    except Exception as _ae:
        pass  # 封存失敗不影響儀表板生成

    print('\n[步驟 2/4] 計算指標...')
    try:
        D = compute(df)
        print('[✓] 指標計算完成')
    except Exception as e:
        print(f'[✗] 計算失敗：{e}')
        traceback.print_exc()
        sys.exit(1)
    
    print('\n[步驟 3/4] 加載模板...')
    if not TEMPLATE_HTML.exists():
        print(f'[✗] 找不到模板：{TEMPLATE_HTML}')
        print(f'   請確認檔案存在！')
        sys.exit(1)
    
    html = TEMPLATE_HTML.read_text(encoding='utf-8')
    print(f'[✓] 模板大小：{len(html):,} 字元')
    
    print('\n[步驟 4/4] 生成 HTML...')
    try:
        new_html = patch_html(html, D)
        new_html = patch_fonts(new_html)  # 🔤 自動修復字體
        print(f'[✓] 數據注入完成：{len(new_html):,} 字元')
    except Exception as e:
        print(f'[✗] 數據注入失敗：{e}')
        traceback.print_exc()
        sys.exit(1)
    
    # 版本 1：時間戳版本（備份）
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    output_timestamped = OUTPUT_DIR / f'dashboard_{timestamp}.html'
    output_timestamped.write_text(new_html, encoding='utf-8')
    print(f'[✓] 備份版本：{output_timestamped.name}')
    
    # 版本 2：固定名稱版本（上傳用）
    OUTPUT_LATEST.write_text(new_html, encoding='utf-8')
    print(f'[✓] 上傳版本：{OUTPUT_LATEST.name}')
    
    # 驗證檔案大小
    actual_size = OUTPUT_LATEST.stat().st_size
    print(f'[✓] 檔案驗證：{actual_size:,} bytes')
    
    print('\n' + '='*70)
    print('[✅ 成功] 儀表板已生成')
    print('='*70)
    
    print('\n📊 數據摘要：')
    print(f'  本月營收      NT$ {D["kpi"]["rev_mtd"]:,}  ({D["kpi"]["achievement_pct"]}%)')
    print(f'  本月訂單      {D["kpi"]["orders_mtd"]} 張')
    print(f'  新客/回購     {D["kpi"]["new_customers"]} / {D["kpi"]["returning"]}')
    print(f'  業務數        {len(D["agents"])} 位')
    print(f'  未付款        {D["unpaid"][0]["count"] if D["unpaid"] else 0} 筆')
    print(f'  RFM 母體      {D["rfm"]["total_customers"]} 位')
    
    print('\n📁 輸出檔案：')
    print(f'  上傳這個：    output/dashboard_latest.html')
    print(f'  備份檔案：    output/{output_timestamped.name}')
    
    print('\n✨ 使用方法：')
    print(f'  1. 上傳 output/dashboard_latest.html 到 Google Drive')
    print(f'  2. 同事下載檔案')
    print(f'  3. 用瀏覽器打開')
    print(f'  4. 完美顯示 ✓')
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()