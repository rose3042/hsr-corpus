#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学术文献增量爬虫（OpenAlex）
供 GitHub Actions 定时运行：增量拉取高铁相关论文，合并去重后保存。
数据源：OpenAlex（CC0 开放学术元数据）
"""
import urllib.request, urllib.parse, json, time, os

MAILTO = 'research@csu.edu.cn'
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
META = os.path.join(DATA_DIR, 'papers_meta.json')

# 主题查询（首轮全量爬取用；增量运行时会跳过已有ID）
QUERIES = [
    'high-speed railway', 'high-speed rail transport', 'high speed train rolling stock',
    'railway terminology translation', 'railway standard China', 'high-speed rail economics policy',
    'railway track ballastless', 'high-speed railway bridge tunnel', 'railway signaling communication',
    'railway electrification traction', 'railway safety', 'railway maintenance',
    'railway freight transport', 'urban rail transit metro', 'maglev train',
    'railway noise vibration', 'railway steel materials', 'railway station design',
    'railway big data artificial intelligence', 'railway sustainability environment',
    'railway traction power supply', 'railway bridge inspection', 'railway tunnel ventilation',
    'railway passenger service', 'railway high-speed rail development',
]

def get(url, retry=3):
    for i in range(retry):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (corpus-bot; mailto:%s)' % MAILTO})
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception:
            if i == retry - 1:
                raise
            time.sleep(2)

def rebuild_abstract(inv):
    if not inv:
        return ''
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return ' '.join(pos[i] for i in sorted(pos))

# 已有数据
seen = {}
if os.path.exists(META):
    for p in json.load(open(META, encoding='utf-8')):
        seen[p['id']] = True
print('已有文献:', len(seen))

# 增量模式：每主题拉 2 页（最新文献），首轮可调大
PAGES_PER_TOPIC = int(os.environ.get('PAGES_PER_TOPIC', '2'))
all_new = []
for search in QUERIES:
    cursor = '*'
    for pg in range(PAGES_PER_TOPIC):
        url = ('https://api.openalex.org/works?search=%s&per-page=200&cursor=%s'
               '&filter=type:article|review&select=id,display_name,publication_year,'
               'authorships,primary_location,abstract_inverted_index,type,concepts,doi'
               '&mailto=%s') % (urllib.parse.quote(search), cursor, MAILTO)
        try:
            data = get(url)
        except Exception as e:
            print('  [%s] p%d 失败: %s' % (search, pg + 1, e))
            break
        results = data.get('results', [])
        if not results:
            break
        for w in results:
            abst = rebuild_abstract(w.get('abstract_inverted_index'))
            if not abst or len(abst) < 200:
                continue
            wid = w.get('id', '').split('/')[-1]
            if wid in seen:
                continue
            seen[wid] = True
            loc = w.get('primary_location') or {}
            src = (loc.get('source') or {}).get('display_name', '')
            authors = [a['author']['display_name'] for a in (w.get('authorships') or [])[:6]]
            concepts = [c['display_name'] for c in (w.get('concepts') or [])[:4]]
            all_new.append({
                'id': wid, 'title': w.get('display_name', ''), 'year': w.get('publication_year'),
                'type': w.get('type'), 'journal': src, 'authors': authors, 'doi': w.get('doi'),
                'concepts': concepts, 'topic': 'auto', 'abstract': abst,
            })
        cursor = data.get('meta', {}).get('next_cursor')
        if not cursor:
            break
        time.sleep(0.4)
    time.sleep(0.4)

# 合并保存
old = json.load(open(META, encoding='utf-8')) if os.path.exists(META) else []
merged = old + all_new
with open(META, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False)
print('本轮新增: %d，总计: %d' % (len(all_new), len(merged)))
