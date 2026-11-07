#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行銷管道 / 付費廣告成效分析(以 UTM 為主)

來源判斷順序:
  1. 導購來源平台是直播 → 直播
  2. 有 UTM → 依 UTM 來源/媒介判斷(paid/cpc/meta = Meta 付費廣告)
  3. 沒 UTM → 才看推薦活動;「商品名+編號」的碼是 FB/IG 付費廣告(使用者確認)
客服只是成交的人,不是來源。推薦活動填客服名字的訂單,UTM 還在的話照 UTM 算來源。

UTM 只有 Shopline 原始 .xlsx 才有(2026/4 之後),所以範圍限定在原始檔涵蓋的期間。

輸出:
  ① 各管道營收與新客(訂單層級)
  ② 各管道每月營收  ③ 各管道每月新客
  ④ 付費廣告明細(依 UTM 活動名稱/內容,可對 Meta 廣告管理員的編號算投報率)
  ⑤ 各管道新客的首購後 90 天價值
  ⑥ 客服經手的訂單,客人原本從哪個管道進來

用法:
    python3 analyze_ads.py
"""
import re
from pathlib import Path

import pandas as pd

import analyze_marketing as am
import generate_daily as gd
from inspect_source_columns import load_raw

CCOL = '顧客 ID'
PAID_MED = {'paid', 'cpc', 'paid_social', 'ppc', 'cpm'}
PRODUCT_AD = re.compile(r'[一-鿿].*\d{1,3}$')
FALLBACK = {'Facebook': 'FB 自然貼文', 'Instagram': 'IG 自然貼文', 'LINE': 'LINE 社群/OA',
            '客服成交': '客服成交(無來源)', '直接/官網': '無來源紀錄', '其他推薦碼': '其他推薦碼'}


def s(v):
    v = '' if v is None else str(v).strip()
    return '' if v.lower() in ('nan', 'none', 'nat') else v


def norm_id(series):
    return series.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)


def channel(r):
    if '直播' in s(r.get('導購來源平台')):
        return '直播'
    src, med = s(r.get('UTM 來源')).lower(), s(r.get('UTM 媒介')).lower()
    if src:
        if src == 'shopline' or med == 'email':
            return 'Email'
        if src.startswith('fb') or src == 'facebook':
            plat = 'FB'
        elif src.startswith('ig') or src == 'instagram':
            plat = 'IG'
        elif src in ('meta', 'an'):
            return 'Meta 付費廣告'
        elif src.startswith('line'):
            return 'LINE 社群/OA'
        elif src in ('th', 'threads'):
            return 'Threads'
        elif src in ('youtube', 'yt'):
            return 'YouTube'
        elif src in ('wapp', 'whatsapp'):
            return 'WhatsApp'
        elif 'chatgpt' in src:
            return 'AI 搜尋'
        else:
            return 'UTM 其他'
        return 'Meta 付費廣告' if med in PAID_MED else f'{plat} 自然貼文'
    act = s(r.get('推薦活動'))
    ch = am.classify_channel({'推薦活動': act, '訂單來源': s(r.get('訂單來源'))})
    if ch == '內容貼文' and ('｜' in act or '|' in act or PRODUCT_AD.search(act)):
        return 'Meta 付費廣告'
    return FALLBACK.get(ch, ch)


def build(ords, first_order_ids):
    ords = ords.copy()
    ords['訂單日期'] = pd.to_datetime(ords['訂單日期'], errors='coerce')
    ords = ords[ords['訂單日期'].notna()].sort_values('訂單日期')
    ords['_ch'] = ords.apply(channel, axis=1)
    ords['_new'] = norm_id(ords['訂單號碼']).isin(first_order_ids)
    ords['_staff'] = ords.apply(
        lambda r: am.classify_channel({'推薦活動': s(r.get('推薦活動')), '訂單來源': ''}) == '客服成交', axis=1)
    ords['_月'] = ords['訂單日期'].dt.to_period('M')
    total = ords['訂單合計'].sum()

    t1 = ords.groupby('_ch').agg(
        訂單數=('訂單號碼', 'count'), 營收=('訂單合計', 'sum'),
        新客數=('_new', 'sum'), 客服經手=('_staff', 'sum'),
    ).sort_values('營收', ascending=False)
    t1['營收佔比%'] = (t1['營收'] / total * 100).round(1) if total else 0
    t1.index.name = '管道'

    t2 = ords.pivot_table(index='_ch', columns='_月', values='訂單合計', aggfunc='sum', fill_value=0)
    t2 = t2.loc[t2.sum(axis=1).sort_values(ascending=False).index]
    t3 = (ords[ords['_new']].pivot_table(index='_ch', columns='_月', values='訂單號碼',
                                         aggfunc='count', fill_value=0))
    t3 = t3.loc[t3.sum(axis=1).sort_values(ascending=False).index]
    t2.index.name = t3.index.name = '管道'

    ads = ords[ords['_ch'] == 'Meta 付費廣告'].copy()
    camp = ads['UTM 活動名稱'].map(s)
    ads['廣告活動'] = camp.where(camp != '', '(無UTM)' + ads['推薦活動'].map(s))
    ads['廣告內容'] = ads['UTM 活動內容'].map(s)
    t4 = ads.groupby(['廣告活動', '廣告內容']).agg(
        訂單數=('訂單號碼', 'count'), 營收=('訂單合計', 'sum'), 新客數=('_new', 'sum'),
        首筆=('訂單日期', 'min'), 末筆=('訂單日期', 'max'),
    ).reset_index().sort_values('營收', ascending=False)
    t4['首筆'] = t4['首筆'].dt.strftime('%Y-%m-%d')
    t4['末筆'] = t4['末筆'].dt.strftime('%Y-%m-%d')

    new = ords[ords['_new']].drop_duplicates(CCOL)
    cutoff = ords['訂單日期'].max() - pd.Timedelta(days=90)
    new = new[new['訂單日期'] <= cutoff].set_index(CCOL)
    rows = ords[ords[CCOL].isin(new.index)]
    first_dt = rows[CCOL].map(new['訂單日期'])
    win = rows[rows['訂單日期'] <= first_dt + pd.Timedelta(days=90)]
    v90 = pd.DataFrame({'管道': new['_ch'],
                        '營收': win.groupby(CCOL)['訂單合計'].sum(),
                        '筆數': win.groupby(CCOL)['訂單號碼'].count()})
    t5 = v90.groupby('管道').agg(
        新客數=('營收', 'size'), 平均90天營收=('營收', 'mean'), 中位數90天營收=('營收', 'median'),
        回購率=('筆數', lambda x: (x > 1).mean() * 100),
    ).round(1).sort_values('中位數90天營收', ascending=False)

    t6 = ords.loc[ords['_staff'], '_ch'].value_counts()
    return t1, t2, t3, t4, t5, t6


def main():
    print('讀取原始 .xlsx(含 UTM)...')
    raw = load_raw()
    if raw is None:
        print('[X] 找不到含 UTM 的原始 .xlsx')
        return
    ords = gd.paid_orders(raw)

    print('讀取全部歷史資料(判斷新客/舊客)...')
    full = gd.order_level(gd.paid_orders(gd.load_data())).sort_values('訂單日期')
    first_ids = set(norm_id(full.drop_duplicates(CCOL, keep='first')['訂單號碼']))

    t1, t2, t3, t4, t5, t6 = build(ords, first_ids)

    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 220)
    pd.set_option('display.max_columns', 20)
    money = '{:,.0f}'.format
    d = pd.to_datetime(ords['訂單日期'], errors='coerce')
    print(f'\n範圍:{d.min():%Y-%m-%d} ~ {d.max():%Y-%m-%d},已付款訂單 {len(ords):,} 張\n')

    print('① 各管道營收與新客(客服經手 = 這個管道裡有多少張是客服接單)\n')
    print(t1.to_string(formatters={'營收': money}))
    print('\n② 各管道每月營收\n')
    print(t2.to_string(float_format=money))
    print('\n③ 各管道每月新客數\n')
    print(t3.to_string())
    print('\n④ 付費廣告明細(營收前 30;完整清單見 CSV,可用活動編號對 Meta 廣告管理員算投報率)\n')
    print(t4.head(30).to_string(index=False, formatters={'營收': money}))
    print('\n⑤ 各管道新客的首購後 90 天價值(只算首購滿 90 天的新客)\n')
    print(t5.to_string(formatters={'平均90天營收': money, '中位數90天營收': money}))
    print('\n⑥ 客服經手的訂單,客人原本從哪個管道進來\n')
    print(t6.to_string())

    out = Path('output')
    out.mkdir(exist_ok=True)
    t1.to_csv(out / 'ads_channels.csv', encoding='utf-8-sig')
    t2.to_csv(out / 'ads_monthly_revenue.csv', encoding='utf-8-sig')
    t4.to_csv(out / 'ads_campaigns.csv', index=False, encoding='utf-8-sig')
    print('\n[✓] 已存 output/ads_*.csv(ads_campaigns.csv 是付費廣告完整清單)')


if __name__ == '__main__':
    main()
