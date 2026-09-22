"""
laya_news_filter.py — 晨报 Laya 预筛器（真实任务：接入明日 8:35 晨报 cron 流程）

任务：从今日新闻候选里，用 Laya 判断「哪条值得进晨报、进哪个版块」，
     并记录完整判断日志（state/questions/输出/conf）供一周后回看效果。

数据源：Hacker News front page（真实实时数据，非构造样本）
输出：/tmp/laya_news_filter_log.jsonl（判断日志）
      stdout（筛选结果，cron 可直接消费）
"""
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

HN_FRONT = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
LOG = "/tmp/laya_news_filter_log.jsonl"
LAYA = "http://127.0.0.1:8600/ask"

# Tech blogs followed in addition to HN front page (checked for new posts each run).
BLOG_FEEDS = [
    ("microsoft", "https://blogs.microsoft.com/feed/"),
    ("openai", "https://openai.com/news/rss.xml"),
    ("cloudflare", "https://blog.cloudflare.com/rss/"),
    ("google_blog", "https://blog.google/rss/"),
    ("google_deepmind", "https://deepmind.google/blog/rss.xml"),
    ("huggingface", "https://huggingface.co/blog/feed.xml"),
]

QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "Categorize this news item for a backend engineer learning AI agents.",
        "criteria": {
            "tech_ai": "AI, agents, LLM, infra, programming, databases",
            "business": "funding, market moves, company strategy",
            "humanities": "history, philosophy, psychology, culture",
            "fun": "nature, physics, curiosities, cool demos",
            "skip": "celebrity, politics, ads, low substance",
        },
    },
    "value": {
        "type": "score",
        "instructions": "How valuable is this for the reader's daily morning briefing?",
        "criteria": ["worthless filler", "mildly interesting", "must read today"],
    },
}


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "laya-news-filter/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def laya_ask(state):
    req = urllib.request.Request(
        LAYA, data=json.dumps({"state": state, "questions": QUESTIONS}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_blog_posts(limit_per_feed=5, max_age_days=7):
    """Recent posts from followed tech blogs, newest first."""
    import xml.etree.ElementTree as ET
    posts = []
    cutoff = datetime.now().timestamp() - max_age_days * 86400
    for name, url in BLOG_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "laya-news-filter/0.1"})
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
            items = root.findall(".//item") or root.findall(".//{*}entry")
            for it in items[:10]:
                title = (it.findtext("title") or it.findtext("{*}title") or "").strip()
                link = it.findtext("link") or it.findtext("{*}link") or ""
                pub = (it.findtext("pubDate") or it.findtext("{*}updated")
                       or it.findtext("{*}published") or "")
                try:
                    from email.utils import parsedate_to_datetime
                    ts = parsedate_to_datetime(pub).timestamp() if pub else 0
                except Exception:
                    ts = 0
                if title and (not ts or ts >= cutoff):
                    posts.append({"source": name, "title": title, "link": link, "ts": ts})
            posts.sort(key=lambda p: -p["ts"])
        except Exception as e:
            print(f"[blog:{name}] fetch fail: {e}")
    return posts[:limit_per_feed * len(BLOG_FEEDS)]


def main(limit=12, include_blogs=True):
    ids = fetch_json(HN_FRONT)[:limit]
    results = []
    # Blog posts first (higher priority source, already curated by the vendors)
    blog_posts = fetch_blog_posts() if include_blogs else []
    for post in blog_posts:
        state = {"title": post["title"], "url_domain": post["source"] + ".blog",
                 "source": "vendor_blog"}
        try:
            answers = laya_ask(state)
        except (urllib.error.URLError, OSError) as e:
            print(f"[blog] laya fail: {e}")
            continue
        cat, val = answers["category"], answers["value"]
        include = cat["choice"] != "skip" and val["score"] >= 1.0
        rec = {"ts": datetime.now().isoformat(timespec="seconds"),
               "hn_id": None, "title": post["title"], "source": post["source"],
               "link": post["link"], "state": state,
               "judgment": {"category": cat["choice"], "category_conf": cat["confidence"],
                            "value_score": round(val["score"], 2), "value_conf": val["confidence"]},
               "include": include}
        results.append(rec)
        with open(LOG, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        flag = "✓ INCLUDE" if include else "✗ skip"
        print(f"[b] {flag} | {cat['choice']:10s} conf={cat['confidence']:.2f} "
              f"value={val['score']:.2f} | {post['title'][:60]}")
    for i, hid in enumerate(ids):
        try:
            item = fetch_json(HN_ITEM.format(hid))
        except (urllib.error.URLError, OSError) as e:
            print(f"[{i}] fetch fail: {e}")
            continue
        title = item.get("title", "")
        if not title:
            continue
        state = {"title": title,
                 "url_domain": re.sub(r"^www\.", "", item.get("url", "").split("/")[2]) if item.get("url") else "news.ycombinator.com",
                 "points": item.get("score", 0), "comments": item.get("descendants", 0)}
        try:
            answers = laya_ask(state)
        except (urllib.error.URLError, OSError) as e:
            print(f"[{i}] laya fail: {e}")
            continue
        cat = answers["category"]
        val = answers["value"]
        verdict = cat["choice"]
        include = verdict != "skip" and val["score"] >= 1.0
        rec = {"ts": datetime.now().isoformat(timespec="seconds"),
               "hn_id": hid, "title": title, "state": state,
               "judgment": {"category": cat["choice"], "category_conf": cat["confidence"],
                            "value_score": round(val["score"], 2), "value_conf": val["confidence"]},
               "include": include}
        results.append(rec)
        with open(LOG, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        flag = "✓ INCLUDE" if include else "✗ skip"
        print(f"[{i:2d}] {flag} | {verdict:10s} conf={cat['confidence']:.2f} "
              f"value={val['score']:.2f} | {title[:60]}")
    picked = [r for r in results if r["include"]]
    print(f"\n=== {len(picked)}/{len(results)} included ===")
    for r in picked:
        print(f"  [{r['judgment']['category']}] {r['title']}")


if __name__ == "__main__":
    main()
