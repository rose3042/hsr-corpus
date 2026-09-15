#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻增量爬虫
供 GitHub Actions 定时运行：Railway Gazette RSS + 人民铁道，增量合并。
"""
import urllib.request, urllib.parse, re, json, time, html as H, os

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'}
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore')

def clean(t):
    t = H.unescape(t)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def extract_pr(h):
    i = h.find('details-xq')
    if i < 0:
        return ''
    seg = h[i:i+20000]
    ps = re.findall(r'<p[^>]*>(.*?)</p>', seg, re.S)
    txt = ' '.join(clean(p) for p in ps)
    return re.sub(r'\s+', ' ', txt).strip()

def extract_rg_body(h):
    m = re.search(r'<article.*?</article>', h, re.S)
    return clean(m.group(0)) if m else ''

# 已有
existing = {}
if os.path.exists(NEWS_FILE):
    for n in json.load(open(NEWS_FILE, encoding='utf-8')):
        existing[n['url']] = True
print('已有新闻:', len(existing))

news = []
# 1. Railway Gazette RSS
try:
    rss = get('https://www.railwaygazette.com/category/high-speed/feed/')
    items = re.findall(r'<item>(.*?)</item>', rss, re.S)
    for it in items[:12]:
        tm = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', it, re.S)
        lm = re.search(r'<link>(.*?)</link>', it, re.S)
        dm = re.search(r'<pubDate>(.*?)</pubDate>', it, re.S)
        title = clean(tm.group(1)) if tm else ''
        link = lm.group(1).strip() if lm else ''
        date = dm.group(1).strip() if dm else ''
        if not link or link in existing:
            continue
        try:
            body = extract_rg_body(get(link))
            if len(body) < 300:
                continue
            news.append({'title': title, 'date': date[:16], 'source': 'Railway Gazette International',
                         'lang': 'en', 'category': '国际行业', 'url': link, 'text': body[:4000]})
        except Exception:
            pass
        time.sleep(0.4)
except Exception as e:
    print('RG失败:', e)

# 2. 人民铁道
try:
    list_pages = ['http://www.peoplerail.com/rail/list-2762-1.html',
                  'http://www.peoplerail.com/rail/list-2770-1.html']
    links = []
    for lp in list_pages:
        links += re.findall(r'href="(http://www\.peoplerail\.com/rail/show-\d+-\d+-\d+\.html)"', get(lp))
    links = list(dict.fromkeys(links))
    for l in links[:12]:
        if l in existing:
            continue
        try:
            h = get(l)
            tm = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) or re.search(r'<title>(.*?)</title>', h, re.S)
            dm = re.search(r'(\d{4}-\d{2}-\d{2})', h)
            body = extract_pr(h)
            if len(body) < 300:
                continue
            title = clean(tm.group(1)) if tm else l[:60]
            title = re.sub(r'[-—].*$', '', title).strip()
            news.append({'title': title[:80], 'date': dm.group(1) if dm else '',
                         'source': '人民铁道网', 'lang': 'zh', 'category': '国内行业',
                         'url': l, 'text': body[:4000]})
        except Exception:
            pass
        time.sleep(0.4)
except Exception as e:
    print('人民铁道失败:', e)

# 合并保存
old = json.load(open(NEWS_FILE, encoding='utf-8')) if os.path.exists(NEWS_FILE) else []
merged = old + news
with open(NEWS_FILE, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=1)
print('本轮新增: %d，总计: %d' % (len(news), len(merged)))
