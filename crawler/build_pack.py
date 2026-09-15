#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据包生成脚本（远程数据源格式）
汇总 术语 / 语料 / 标准 / 学术文献 / 新闻 → hsr-corpus-data.json
页面"数据版本与更新 → 配置数据源"填入该文件的托管 URL 即可自动同步。

运行前提：仓库 data/ 下存在以下数据文件（由各爬虫脚本产出）
  - terms_compact.json   术语 223 条
  - corpus_compact.json  教材语料 6 篇
  - announcements.json   标准公告语料 25 篇
  - news.json            新闻语料 N 篇
  - papers_selected.json 学术文献精选 1200 篇
  - railway_standards_all.json 标准 1309 条
"""
import json, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'hsr-corpus-data.json')

def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        print('警告: 缺少', name)
        return []
    return json.load(open(p, encoding='utf-8'))

# 1. 术语
terms = load('terms_compact.json')
# 2. 语料（教材 + 公告 + 新闻）
corpus = load('corpus_compact.json')
anns = load('announcements.json')
news_raw = load('news.json')
if isinstance(corpus, list):
    corpus = list(corpus)
corpus = corpus + [dict(a) for a in anns] if anns else corpus
for i, n in enumerate(news_raw):
    corpus.append({
        'id': 'news_' + str(i),
        'title': n.get('title', ''),
        'category': '新闻语料',
        'desc': n.get('source', '') + ' · ' + n.get('date', '') + '（' + ('中文' if n.get('lang') == 'zh' else '英文') + '）',
        'paras': [n.get('text', '')] if n.get('text') else [],
        'wc': len(n.get('text', '')),
        'cc': len(n.get('text', '')),
    })
# 3. 标准（含重点标记）
stds = load('railway_standards_all.json')
standards = []
key_path = os.path.join(DATA, '高铁重点标准清单.csv')
key_set = set()
if os.path.exists(key_path):
    import csv
    with open(key_path, encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[1] and row[1] != '标准编号':
                key_set.add(row[1].strip())
if isinstance(stds, dict):
    for cat, items in stds.items():
        for it in items:
            no = it.get('no', '')
            standards.append({'no': no, 'name': it.get('name', ''), 'category': cat,
                              'key': no.strip() in key_set})
print('重点标准标记:', sum(1 for s in standards if s.get('key')))
# 4. 学术文献精选
papers = load('papers_selected.json')
# 5. 新闻卡片
news_card = [{'title': n.get('title', ''), 'date': n.get('date', ''), 'source': n.get('source', ''),
              'lang': n.get('lang', ''), 'url': n.get('url', '')} for n in news_raw]

pack = {
    'version': '2.4',
    'updated_at': time.strftime('%Y-%m-%d'),
    'built': time.strftime('%Y-%m-%d %H:%M'),
    'terms': terms,
    'corpus': corpus,
    'standards': standards,
    'papers': papers,
    'news': news_card,
    'stats': {
        'terms': len(terms), 'corpus': len(corpus),
        'standards': len(standards), 'papers': len(papers), 'news': len(news_card),
        'corpus_chars': sum(d.get('cc', 0) or 0 for d in corpus),
        'papers_chars': sum(len(p.get('abstract', '')) for p in papers),
    }
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(pack, f, ensure_ascii=False)
size = os.path.getsize(OUT) / 1024
print('数据包已生成: %s (%.1f KB)' % (OUT, size))
print('统计:', json.dumps(pack['stats'], ensure_ascii=False))
print('\n页面配置数据源 URL:')
print('  https://<用户名>.github.io/<仓库名>/hsr-corpus-data.json')
