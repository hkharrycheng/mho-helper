"""MHO (J17) news cache builder.

Reads News Feed List records whose Job ID link points at J17, fetches each
source, and writes news-cache.json + news-img/.
Supported source types:
  - Webpage  -> Garena official site (Nuxt payload decoded) or generic anchor scan
  - RSS      -> standard RSS 2.0
  - Youtube  -> skipped (video channel, no feed items)
"""

import json, io, os, re, sys, hashlib, urllib.request, datetime, glob

BASE = r"D:\Onedrive\Harry Information System\豆包Agents Program Backup\MHO"
RAW = os.path.join(BASE, "_raw")
IMGDIR = os.path.join(BASE, "news-img")
OUT = os.path.join(BASE, "news-cache.json")
JOB_ID = "reczz28WqHQpirNP"  # J17 MHO Assistant in 常數設定
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"}
LIMIT = 40
MHO_CAT = {1: "社群", 2: "新聞", 3: "公告"}


def fetch(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout).read()


def cache_image(url):
    if not url:
        return ""
    os.makedirs(IMGDIR, exist_ok=True)
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    name = hashlib.md5(url.encode("utf-8")).hexdigest()[:16] + ext
    path = os.path.join(IMGDIR, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return "news-img/" + name
    try:
        data = fetch(url, timeout=40)
        if not data:
            return ""
        io.open(path, "wb").write(data)
        return "news-img/" + name
    except Exception:
        return ""


def sources_for_job():
    rows = []
    for line in io.open(os.path.join(RAW, "newsfeed.ndjson"), encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        o = json.JSONDecoder().raw_decode(line)[0]
        if "record_id" in o:
            rows.append(o)
    out = []
    for r in rows:
        ids = [x["id"] for x in (r.get("Job ID") or [])]
        if JOB_ID not in ids:
            continue
        src = r.get("Source") or ""
        m = re.search(r"\((https?://[^)]+)\)", src)
        url = m.group(1) if m else src.strip()
        if not url.startswith("http"):
            continue
        out.append({"name": r.get("Filter用標籤名") or "", "type": (r.get("Source Type") or "").strip(), "url": url})
    return out


# ---------------- Nuxt (Garena official site) ----------------
WRAP = {"Reactive", "ShallowReactive", "Ref", "ShallowRef", "EmptyRef", "EmptyShallowRef"}


def nuxt_state(html):
    m = re.search(r'__NUXT_DATA__">(\[.*?\])</script>', html, re.S)
    if not m:
        return {}
    arr = json.loads(m.group(1))

    def resolve(i, depth=0):
        if depth > 14:
            return None
        v = arr[i]
        if isinstance(v, dict):
            return {k: resolve(val, depth + 1) for k, val in v.items()}
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in WRAP and len(v) == 2:
                return resolve(v[1], depth + 1)
            if v and v[0] == "Set":
                return [resolve(x, depth + 1) for x in v[1:]]
            if v and v[0] == "Map":
                return {resolve(x, depth + 1): resolve(y, depth + 1) for x, y in zip(v[1::2], v[2::2])}
            return [resolve(x, depth + 1) for x in v]
        return v

    root = resolve(1)
    return root.get("state") if isinstance(root, dict) else {}


def garena_items(url):
    base = url.rstrip("/")
    if not base.endswith("/news"):
        base += "/news"
    items = []
    seen = set()
    for page in range(1, 9):
        page_url = base if page == 1 else base + "?page=%d" % page
        try:
            html = fetch(page_url).decode("utf-8", "ignore")
        except Exception:
            break
        state = nuxt_state(html)
        bucket = None
        for k, v in state.items():
            if "news-list" in k and isinstance(v, dict):
                bucket = v
                break
        if not bucket or not bucket.get("items"):
            break
        total = bucket.get("totalPage") or 1
        for it in bucket["items"]:
            did = it.get("displayId")
            if not did or did in seen:
                continue
            seen.add(did)
            items.append({
                "title": it.get("title") or "",
                "link": base + "/" + did,
                "ts": it.get("publishAt"),
                "img": it.get("banner") or "",
                "cat": MHO_CAT.get(it.get("categoryId"), "公告"),
            })
        if page >= total:
            break
    return items


# ---------------- generic helpers ----------------
def generic_webpage(url):
    html = fetch(url).decode("utf-8", "ignore")
    out = []
    seen = set()
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, inner = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        title = re.sub(r"\s+", " ", inner).strip()
        if len(title) < 8 or not href.startswith("http"):
            continue
        if href in seen:
            continue
        d = re.search(r"20\d\d[-/.]\d\d?[-/.]\d\d?", inner) or re.search(r"20\d\d[-/.]\d\d?[-/.]\d\d?", href)
        seen.add(href)
        out.append({"title": title[:120], "link": href,
                    "date": d.group(0).replace(".", "-").replace("/", "-") if d else "", "cat": "新聞"})
    return out[:LIMIT]


def rss_items(url):
    xml = fetch(url).decode("utf-8", "ignore")
    out = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.S):
        block = m.group(1)
        t = re.search(r"<title>(?:<![CDATA[)?(.*?)(?:]]>)?</title>", block, re.S)
        l = re.search(r"<link>(?:<![CDATA[)?(.*?)(?:]]>)?</link>", block, re.S)
        d = re.search(r"<(?:pubDate|dc:date)>(.*?)</(?:pubDate|dc:date)>", block, re.S)
        if not (t and l):
            continue
        date = ""
        if d:
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z"):
                try:
                    date = datetime.datetime.strptime(d.group(1).strip(), fmt).strftime("%Y-%m-%d")
                    break
                except Exception:
                    continue
        out.append({"title": re.sub(r"\s+", " ", t.group(1)).strip(), "link": l.group(1).strip(),
                    "date": date, "cat": "新聞", "ts": None})
    return out[:LIMIT]


# ---------------- YouTube channel ----------------
def yt_channel_id(url):
    html = fetch(url).decode("utf-8", "ignore")
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'"externalId":"(UC[^"]+)"', html)
    return m.group(1) if m else ""


def _rel_date(txt):
    """'3 天前' / '2 週前' / '1 個月前' -> YYYY-MM-DD"""
    now = datetime.datetime.now()
    m = re.search(r"(\d+)\s*(秒|分鐘|小時|天|週|個月|年)前", txt or "")
    if not m:
        return ""
    n = int(m.group(1))
    unit = m.group(2)
    days = {"秒": 0, "分鐘": 0, "小時": 0, "天": n, "週": n * 7, "個月": n * 30, "年": n * 365}[unit]
    return (now - datetime.timedelta(days=days)).strftime("%Y-%m-%d")


def youtube_items(url):
    if "/videos" not in url:
        url = url.rstrip("/") + "/videos"
    html = fetch(url).decode("utf-8", "ignore")
    i = html.find("ytInitialData")
    if i < 0:
        return []
    data, _ = json.JSONDecoder().raw_decode(html[html.find("{", i):])
    locks = []

    def walk(o):
        if isinstance(o, dict):
            if "lockupViewModel" in o:
                locks.append(o["lockupViewModel"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    out = []
    for lk in locks[:20]:
        vid = lk.get("contentId") or ""
        md = (lk.get("metadata") or {}).get("lockupMetadataViewModel") or {}
        title = (md.get("title") or {}).get("content") or ""
        rel = ""
        rows = (((md.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows")) or []
        for row in rows:
            for part in row.get("metadataParts") or []:
                t = (part.get("text") or {}).get("content") or ""
                if "前" in t or "ago" in t:
                    rel = t
        if not (vid and title):
            continue
        out.append({"title": title, "link": "https://www.youtube.com/watch?v=" + vid,
                    "date": _rel_date(rel), "cat": "影片", "ts": None,
                    "img": "https://i.ytimg.com/vi/%s/hqdefault.jpg" % vid})
    # refine dates from the watch page (uploadDate) for the newest videos
    for it in out[:12]:
        try:
            w = fetch(it["link"]).decode("utf-8", "ignore")
            d = re.search(r'"uploadDate":"([^"]+)"', w) or re.search(r'"publishDate":"([^"]+)"', w)
            if d:
                it["date"] = d.group(1)[:10]
        except Exception:
            pass
    return out


# ---------------- gamewith article list ----------------
def gamewith_items(url):
    html = fetch(url).decode("utf-8", "ignore")
    out = []
    seen = set()
    base = "https://gamewith.ai"
    for m in re.finditer(r'<li><a[^>]+href="(/[^"]+)"[^>]*>(.*?)</a></li>', html, re.S):
        href, inner = m.group(1), m.group(2)
        if "/articles/" not in href:
            continue
        t = re.search(r'<h2[^>]*>(.*?)</h2>', inner, re.S)
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""
        d = re.search(r'<time[^>]*dateTime="([^"]+)"', inner)
        tag = re.findall(r'<span class="rounded[^"]*">([^<]+)</span>', inner)
        if not title or href in seen:
            continue
        seen.add(href)
        out.append({"title": title, "link": base + href, "date": (d.group(1)[:10] if d else ""),
                    "cat": "攻略", "tag": (tag[0] if tag else ""), "ts": None, "img": ""})
    # keep only the newest N articles, and fetch each one's og:image
    out = out[:12]
    for it in out:
        try:
            page = fetch(it["link"]).decode("utf-8", "ignore")
            imgs = [x for x in re.findall(r'<img[^>]+src="([^"]+)"', page) if "assets.gamewith.ai" in x]
            if imgs:
                it["img"] = cache_image(imgs[0])
        except Exception:
            pass
    return out


def main():
    sources = sources_for_job()
    print("sources:", [(s["name"], s["type"], s["url"]) for s in sources])
    items = []
    meta = []
    for s in sources:
        raw = []
        try:
            if "mho.garena.com" in s["url"]:
                raw = garena_items(s["url"])
            elif s["type"].lower() == "rss":
                raw = rss_items(s["url"])
            elif s["type"].lower() == "youtube":
                raw = youtube_items(s["url"])
            elif "gamewith.ai" in s["url"]:
                raw = gamewith_items(s["url"])
            else:
                raw = generic_webpage(s["url"])
        except Exception as e:
            print("fetch fail", s["url"], repr(e)[:100])
        for it in raw:
            if it.get("ts"):
                dt = datetime.datetime.fromtimestamp(it["ts"], datetime.timezone(datetime.timedelta(hours=8)))
                it["date"] = dt.strftime("%Y-%m-%d")
            it["ts"] = it.get("ts") or 0
            it["src"] = s["name"]
            it["img"] = cache_image(it["img"]) if str(it.get("img") or "").startswith("http") else (it.get("img") or "")
            items.append(it)
        meta.append({"name": s["name"], "type": s["type"], "url": s["url"], "count": len(raw)})

    # dedupe by link, newest first, undated at tail
    seen = set()
    uniq = []
    for it in items:
        key = it["link"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    uniq.sort(key=lambda x: (x.get("date") or "", x.get("ts") or 0), reverse=True)
    dated = [i for i in uniq if i.get("date")]
    undated = [i for i in uniq if not i.get("date")]
    final = (dated + undated)[:LIMIT]

    out = {
        "app": "MHO",
        "feed": "魔物獵人：旅人助手（J17）",
        "jobId": JOB_ID,
        "sources": meta,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(final),
        "items": [{"title": i["title"], "link": i["link"], "date": i.get("date") or "",
                   "img": i.get("img") or "", "cat": i.get("cat") or "新聞", "src": i.get("src") or ""} for i in final],
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1))
    print("news-cache.json", os.path.getsize(OUT), "bytes, items", len(final),
          "dated", len(dated), "undated", len(undated))
    for i in out["items"]:
        print(" ", i["date"] or "----", i["cat"], i["title"][:46], "| img" if i["img"] else "| noimg")


if __name__ == "__main__":
    main()
