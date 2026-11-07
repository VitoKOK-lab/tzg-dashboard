#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行銷管道成效分析:行銷力道該放在哪裡

客服是「成交」的人,不是「帶客人進來」的管道。所以這裡用每位客人的
「第一筆訂單」判斷他是從哪個行銷管道進來的(首次接觸),再算這個管道
帶進來的客人後續總共貢獻多少營收。

輸出:
  ① 各管道帶進來的新客 + 這些客人的累計價值(回購率、每位平均營收)
  ② 各管道每月新客數趨勢(哪個在成長、哪個在萎縮)
  ③ 單篇貼文/單支廣告排行(哪一篇帶最多新客、最多後續營收)
  ④ 客服成交的客人,原本是從哪個管道進來的
  ⑤ 辨識不出管道的推薦碼(供人工確認分類規則)

用法:
    python3 analyze_marketing.py              # 趨勢看最近 6 個月
    python3 analyze_marketing.py --months 12
"""
import argparse
import re
from pathlib import Path

import pandas as pd

import generate_daily as gd

CCOL = '顧客 ID'
STAFF_KEYWORDS = ['客服', '跟單', '業務', '銷售', '中控', '電商', '行政', '培訓', '助理', '行銷']
CODE_SUFFIX = {'fb': 'Facebook', 'line': 'LINE', 'ig': 'Instagram',
               'yt': 'YouTube', 'tk': 'TikTok', 'tt': 'TikTok', 'th': 'Threads'}
AD_OR_CONTENT = {'Facebook', 'LINE', 'Instagram', 'YouTube', 'TikTok', 'Threads',
                 '內容貼文', '直播', '代理/合作夥伴'}


def classify_channel(r):
    """推薦活動優先(精確規則),沒填才看訂單來源。客服名字一律歸「客服成交」。"""
    act = str(r.get('推薦活動', '')).strip()
    if act and act.lower() != 'nan':
        a = act.lower().replace(' ', '')
        # 廣告/貼文追蹤碼:20260807f87fb、20260828f03line、20260417f31line2
        m = re.match(r'^\d{8}[a-z]*\d*([a-z]+)\d*$', a)
        if m and m.group(1) in CODE_SUFFIX:
            return CODE_SUFFIX[m.group(1)]
        if 'facebook' in a or '臉書' in act:
            return 'Facebook'
        if 'sl-ref=' in a:
            m2 = re.search(r'sl-ref=\d*([a-z]+)', a)
            if m2 and m2.group(1) in CODE_SUFFIX:
                return CODE_SUFFIX[m2.group(1)]
        if 'threads' in a:
            return 'Threads'
        if '直播' in act or '主播' in act:
            return '直播'
        if '代理' in act or '加盟' in act or '專用連結' in act:
            return '代理/合作夥伴'
        if '店務' in act or '門市' in act:
            return '門市'
        # 客服代碼格式是「職稱/名字/地點」,沒有斜線的「社群貼文行銷」之類不算
        if '/' in act and any(k in act for k in STAFF_KEYWORDS):
            return '客服成交'
        if '｜' in act or '|' in act or '貼文' in act or '社群' in act:
            return '內容貼文'
        return '其他推薦碼'
    src = gd.classify_source(r)
    return {'Facebook 來源': 'Facebook', 'Instagram 來源': 'Instagram',
            'LINE 來源': 'LINE'}.get(src, src)


def build(vd, months):
    ords = gd.order_level(vd).copy()
    ords = ords[ords[CCOL].notna()]
    ords['_ch'] = ords.apply(classify_channel, axis=1)
    ords = ords.sort_values('訂單日期')

    first = ords.groupby(CCOL).first()
    acq = first['_ch'].where(first['_ch'] != '客服成交', '客服成交(來源未記錄)')
    cust = pd.DataFrame({
        '管道': acq,
        '首購日': first['訂單日期'],
        '首購碼': first['推薦活動'].astype(str),
        '首購營收': first['訂單合計'],
        '累計營收': ords.groupby(CCOL)['訂單合計'].sum(),
        '訂單數': ords.groupby(CCOL)['訂單號碼'].count(),
    })
    cust['回購'] = cust['訂單數'] > 1

    t1 = cust.groupby('管道').agg(
        新客數=('首購營收', 'size'), 首購營收=('首購營收', 'sum'),
        累計營收=('累計營收', 'sum'), 回購率=('回購', 'mean'),
    )
    t1['每位平均累計營收'] = (t1['累計營收'] / t1['新客數']).round(0)
    t1['回購率'] = (t1['回購率'] * 100).round(1)
    t1['營收佔比%'] = (t1['累計營收'] / t1['累計營收'].sum() * 100).round(1)
    t1 = t1.sort_values('累計營收', ascending=False)

    cust['首購月'] = cust['首購日'].dt.to_period('M')
    last = sorted(cust['首購月'].dropna().unique())[-months:]
    t2 = (cust[cust['首購月'].isin(last)]
          .pivot_table(index='管道', columns='首購月', values='首購營收', aggfunc='size', fill_value=0))
    t2 = t2.loc[t2.sum(axis=1).sort_values(ascending=False).index]

    posts = cust[cust['管道'].isin(AD_OR_CONTENT) & (cust['首購碼'].str.lower() != 'nan')]
    t3 = posts.groupby(['管道', '首購碼']).agg(
        新客數=('首購營收', 'size'), 累計營收=('累計營收', 'sum'),
    ).reset_index().sort_values(['新客數', '累計營收'], ascending=False).head(20)

    staff_custs = ords.loc[ords['_ch'] == '客服成交', CCOL].unique()
    t4 = cust.loc[cust.index.isin(staff_custs), '管道'].value_counts()
    staff_rev = ords.loc[ords['_ch'] == '客服成交', '訂單合計'].sum()
    staff_share = staff_rev / ords['訂單合計'].sum() * 100 if len(ords) else 0

    t5 = (ords[ords['_ch'] == '其他推薦碼'].groupby('推薦活動')
          .agg(訂單數=('訂單號碼', 'count'), 營收=('訂單合計', 'sum'))
          .sort_values('營收', ascending=False).head(20))
    return t1, t2, t3, t4, staff_share, t5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--months', type=int, default=6, help='趨勢表看最近幾個月(預設 6)')
    args = ap.parse_args()

    print('載入資料...')
    vd = gd.paid_orders(gd.load_data())
    t1, t2, t3, t4, staff_share, t5 = build(vd, args.months)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 20)
    pd.set_option('display.unicode.east_asian_width', True)

    print('\n① 各管道帶進來的客人(依「第一筆訂單」判斷首次接觸管道)\n')
    print(t1.to_string(formatters={'首購營收': '{:,.0f}'.format, '累計營收': '{:,.0f}'.format,
                                   '每位平均累計營收': '{:,.0f}'.format}))
    print('\n  註:越早進來的客人累計時間越長,累計營收會偏高,跨管道比較時請搭配②看趨勢')

    print(f'\n② 各管道每月新客數(最近 {args.months} 個月)\n')
    print(t2.to_string())

    print('\n③ 單篇貼文/單支廣告排行(帶進最多新客的前 20 名)\n')
    print(t3.to_string(index=False, formatters={'累計營收': '{:,.0f}'.format}))

    print(f'\n④ 客服成交的訂單佔全部營收 {staff_share:.1f}%;這些客人原本的進來管道:\n')
    print(t4.to_string())

    print('\n⑤ 辨識不出管道的推薦碼(營收前 20,請確認要歸哪一類)\n')
    print(t5.to_string(formatters={'營收': '{:,.0f}'.format}))

    out = Path('output')
    out.mkdir(exist_ok=True)
    t1.to_csv(out / 'marketing_channels.csv', encoding='utf-8-sig')
    t2.to_csv(out / 'marketing_trend.csv', encoding='utf-8-sig')
    t3.to_csv(out / 'marketing_top_posts.csv', index=False, encoding='utf-8-sig')
    print('\n[✓] 表格已存到 output/marketing_*.csv(可用 Excel 打開)')


if __name__ == '__main__':
    main()
