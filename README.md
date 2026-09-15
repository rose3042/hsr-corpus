# 语料库全自动更新流水线

让"高速铁路标准语料库"每周自动更新：定时爬取学术文献与新闻 → 自动生成数据包 → 自动发布到
GitHub Pages → 团队打开页面即自动同步最新数据。全程无需手动操作。

---

## 一、整体架构

```
GitHub Actions（每周一、周四 03:00 UTC 定时触发）
    │
    ├─ 1. openalex_pipeline.py   增量爬取学术论文（OpenAlex，CC0）
    ├─ 2. news_pipeline.py       增量爬取新闻（Railway Gazette + 人民铁道）
    ├─ 3. build_pack.py          汇总五类数据 → hsr-corpus-data.json
    │
    └─ git commit & push 到仓库
        │
        └─ GitHub Pages 托管 hsr-corpus-data.json
            │
            └─ 页面"数据版本与更新 → 配置数据源"填入 URL
                打开页面 → 自动拉取最新数据（含版本号与更新时间）
```

## 二、部署步骤（约 10 分钟）

1. **注册 GitHub**（免费）：https://github.com/signup

2. **创建仓库**：New repository → 仓库名如 `hsr-corpus` → **Public**（公共仓库
   GitHub Actions 免费额度充足；且 Pages 免费）→ Create

3. **上传本流水线**（在仓库页 Upload files，或本地 git push）：
   ```
   .github/workflows/update-corpus.yml   ← 定时任务
   crawler/                               ← 三个爬虫/生成脚本
   data/                                  ← 初始数据（见下）
   hsr-corpus-data.json                   ← 首份数据包（可选，Actions 会生成）
   ```

4. **启用 GitHub Pages**：仓库 Settings → Pages → Source 选 `Deploy from a branch`
   → 分支选 `main`，路径 `/ (root)` → Save。等待 1-2 分钟，出现
   `https://<用户名>.github.io/<仓库名>/` 即成功。

5. **验证数据包可访问**：浏览器打开
   `https://cdn.jsdelivr.net/gh/<用户名>/<仓库名>@main/hsr-corpus-data.json`，能看到 JSON 即成功。
   （推荐用 jsDelivr CDN 地址：它自动带 CORS 头，本地双击 HTML 也能同步；首次发布后刷新一次
    `https://purge.jsdelivr.net/gh/<用户名>/<仓库名>@main/hsr-corpus-data.json` 立即生效。）

6. **在语料库页面配置**：打开网页 → "数据版本与更新" → 配置数据源 → 粘贴上面的
   jsDelivr 地址 → 保存 → 点"检查更新"，页面右上角提示已同步即打通。

7. **手动触发一次**：仓库 Actions 页 → 左侧 workflow → "Run workflow" → Run，确认流水线跑通。

## 三、定时规则（可改）

`update-corpus.yml` 中：
```yaml
schedule:
  - cron: '0 3 * * 1,4'   # 每周一、周四 03:00 UTC = 北京时间 11:00
```
- 每天更新：`'0 3 * * *'`
- 只在周一：`'0 3 * * 1'`

改完 commit 后自动生效。

## 四、初始数据放哪里

`data/` 目录需放以下文件（与本仓库 `高铁标准资料/` 中的文件一致）：

| 文件 | 内容 | 来源 |
|---|---|---|
| `terms_compact.json` | 术语 223 条 | 已交付（term_data/） |
| `corpus_compact.json` | 教材语料 6 篇 | 已交付（term_data/） |
| `announcements.json` | 标准公告 25 篇 | 已交付（学术文献语料/） |
| `news.json` | 新闻 24 篇 | 已交付（学术文献语料/） |
| `papers_selected.json` | 学术文献精选 1200 篇 | 已交付（corpus_library/data/） |
| `railway_standards_all.json` | 标准 1309 条 | 已交付（标准目录清单/） |

也可以先只放 `papers_meta.json`（完整 33,746 篇），流水线跑起来后自动生成精选。

## 五、团队协作

- 任何组员把新的标准全文 / 译本 PDF 转成 JSON 放进 `data/` 并 push，
  页面打开即同步（无需重新生成 HTML）
- 每条更新自动写入 commit 记录，`updated_at` 自动更新，可在页面看到"最近更新"
- 页面本身（index.html）不需要每次重新发布——它只是"壳"，数据全部走远程数据源
- 流水线会在每次推送后自动刷新 jsDelivr CDN 缓存，更新即时生效

## 六、注意事项

1. **CORS 说明**：本地用 file:// 打开页面时，浏览器禁止跨域读取普通托管（如 GitHub Pages 默认不带
   CORS 头），因此必须使用 jsDelivr CDN 地址（自动返回 `Access-Control-Allow-Origin: *`）。
   页面已内置提示。若页面部署在服务器上（同域），用普通地址即可。
2. **版权边界**：学术元数据（OpenAlex）为 CC0 可自由使用；新闻为公开报道摘录（保留来源链接）；
   标准全文（TB/GB/T）受版权保护，建议仅存于学校内部服务器，不要公开到公共仓库——
   如需公开，只放标准目录元数据，不放全文。
3. **频率控制**：OpenAlex 每次运行约 2 页/主题（增量），每月请求量远低于限额；
   如需首轮全量扩充，本地跑 `openalex_expand.py` 后上传数据即可。
4. **费用**：GitHub 公共仓库 Actions + Pages + jsDelivr 均免费。
5. 若想换成学校服务器：把 `cron` 换成服务器 crontab，把 push 换成上传到服务器目录即可，脚本不变。
