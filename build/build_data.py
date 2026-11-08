import json, io, os, glob, datetime

BASE = r"D:\Onedrive\Harry Information System\豆包Agents Program Backup\MHO"
RAW = os.path.join(BASE, "_raw")
IMG = os.path.join(BASE, "images")
OUT = os.path.join(BASE, "data.json")


def load(name):
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, name + "*.ndjson"))):
        for line in io.open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            o = json.JSONDecoder().raw_decode(line)[0]
            if "record_id" in o:
                rows.append(o)
    seen, out = set(), []
    for r in rows:
        if r["record_id"] in seen:
            continue
        seen.add(r["record_id"])
        out.append(r)
    return out


image_map = {}
_pri = {}
for f in os.listdir(IMG):
    stem = os.path.splitext(f)[0]
    rid = stem
    if stem.endswith("_pict"):
        rid, rank = stem[:-5], 0
    elif stem.endswith("_icon"):
        rid, rank = stem[:-5], 2
    else:
        rank = 1
    _pri.setdefault(rid, {})
    _pri[rid][rank] = "images/" + f
for rid, ranks in _pri.items():
    image_map[rid] = ranks[min(ranks)]

adventurers = load("adventurers")
gear_rows = load("gear")
pals_rows = load("pals")
team_rows = load("teams")
mon_rows = load("monsters")

gear = []
for r in gear_rows:
    if r.get("武器種類") or r.get("攻擊力"):
        kind = "weapon"
    elif r.get("部位") or r.get("防禦力"):
        kind = "armor"
    else:
        kind = "other"
    gear.append({
        "id": r["record_id"],
        "name": r.get("裝備名") or r.get("DisplayName"),
        "kind": kind,
        "wtype": (r.get("武器種類") or [None])[0],
        "slot": (r.get("部位") or [None])[0],
        "element": (r.get("屬性") or [None])[0],
        "sharp": (r.get("鋒利度") or [None])[0],
        "atk": r.get("攻擊力"),
        "def": r.get("防禦力"),
        "set": r.get("套裝"),
        "setSkill": r.get("套裝技能"),
        "skills": r.get("技能") or [],
        "img": image_map.get(r["record_id"]),
    })

pals = []
for r in pals_rows:
    pals.append({
        "id": r["record_id"],
        "name": r.get("隨從"),
        "kind": (r.get("種類") or [None])[0],
        "role": (r.get("類型") or [None])[0],
        "skill": r.get("技能"),
        "boost": r.get("提升冒險者"),
        "atk": r.get("攻擊力"),
        "maxAtk": r.get("最大攻擊力"),
        "img": image_map.get(r["record_id"]),
    })

G = {g["id"]: g for g in gear}
P = {p["id"]: p for p in pals}

teams = []
for t in team_rows:
    teams.append({
        "id": t["record_id"],
        "name": t.get("隊伍名"),
        "label": t.get("文本"),
        "lead": [x["id"] for x in (t.get("主控") or [])],
        "members": [x["id"] for x in (t.get("冒險者") or [])],
    })


def team_of(rid):
    res = []
    for t in teams:
        if rid in t["lead"] or rid in t["members"]:
            res.append({"name": t["name"], "label": t["label"], "lead": rid in t["lead"]})
    return res


adv = []
_gal = {}
for f in os.listdir(IMG):
    m = __import__("re").match(r"^(rec\w*)_gal(\d+)(\.[A-Za-z0-9]+)$", f)
    if m:
        _gal.setdefault(m.group(1), []).append((int(m.group(2)), "images/" + f))
for r in adventurers:
    rid = r["record_id"]
    adv.append({
        "id": rid,
        "name": r.get("冒險者"),
        "display": r.get("DisplayName"),
        "role": (r.get("定位") or []),
        "element": (r.get("屬性") or []),
        "owned": (r.get("擁有日期") or "")[:10],
        "trailer": r.get("Official Trailer") or "",
        "guide": r.get("攻略") or "",
        "img": image_map.get(rid),
        "gallery": [p for _, p in sorted(_gal.get(rid, []))],
        "weapons": [G[i] for i in [x["id"] for x in (r.get("武器") or [])] if i in G],
        "armors": [G[i] for i in [x["id"] for x in (r.get("防具") or [])] if i in G],
        "pals": [P[i] for i in [x["id"] for x in (r.get("隨從") or [])] if i in P],
        "teams": team_of(rid),
    })

mon = []
for r in mon_rows:
    rid = r["record_id"]
    mon.append({
        "id": rid,
        "name": r.get("魔物名") or r.get("DisplayName"),
        "kind": (r.get("種類") or [None])[0],
        "size": (r.get("尺寸") or [None])[0],
        "habitat": r.get("棲息地") or "",
        "weak": {
            "火": r.get("弱點火"), "水": r.get("弱點水"), "雷": r.get("弱點雷"),
            "冰": r.get("弱點冰"), "龍": r.get("弱點龍"),
        },
        "ailment": r.get("異常弱點") or "",
        "ailmentAtk": r.get("異常狀態攻擊") or "",
        "breakable": r.get("可破壞部位") or "",
        "parts": r.get("肉質") or "",
        "traits": {
            "咆哮": (r.get("咆哮") or [""])[0],
            "風壓": (r.get("風壓") or [""])[0],
            "震動": (r.get("震動") or [""])[0],
        },
        "items": {
            "閃光彈": (r.get("閃光彈") or [""])[0],
            "音爆彈": (r.get("音爆彈") or [""])[0],
            "地洞": (r.get("地洞") or [""])[0],
        },
        "img": image_map.get(rid),
    })

ELS = ["火", "水", "雷", "冰", "龍"]


def main_el(a):
    for e in a["element"]:
        if e in ELS:
            return e
    return ""


# 冒險者 <-> 魔物 互聯
for a in adv:
    el = main_el(a)
    a["el"] = el
    if not el:
        a["counterMon"], a["hardMon"] = [], []
        continue
    weak_of = lambda m: (m["weak"] or {}).get(el) or 0
    hit = [m for m in mon if weak_of(m) >= 3]
    if not hit:
        hit = [m for m in mon if weak_of(m) >= 2]
    hard = [m for m in mon if weak_of(m) == 0]
    a["counterMon"] = [{"id": m["id"], "name": m["name"], "img": m["img"], "v": weak_of(m)} for m in hit[:8]]
    a["hardMon"] = [{"id": m["id"], "name": m["name"], "img": m["img"]} for m in hard[:8]]

for m in mon:
    w = m["weak"] or {}
    mx = max([v or 0 for v in w.values()] or [0])
    if mx <= 0:
        m["counterAdv"], m["counteredAdv"] = [], []
        continue
    good_els = [e for e in ELS if (w.get(e) or 0) == mx]
    bad_els = [e for e in ELS if (w.get(e) or 0) == 0]
    m["counterAdv"] = [{"id": a["id"], "name": a["display"] or a["name"], "img": a["img"],
                        "el": a["el"], "role": (a["role"] or [""])[0]}
                       for a in adv if a["el"] in good_els][:8]
    m["counteredAdv"] = [{"id": a["id"], "name": a["display"] or a["name"], "img": a["img"],
                          "el": a["el"], "role": (a["role"] or [""])[0]}
                         for a in adv if a["el"] in bad_els][:8]

data = {
    "app": "MHO 魔物獵人：旅人助手",
    "version": "2026.1.08",    "base": "RhuZbZCs0aJhdDsKvMicds5Hn0d",
    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "counts": {"adventurers": len(adv), "weapons": sum(1 for g in gear if g["kind"] == "weapon"),
               "armors": sum(1 for g in gear if g["kind"] == "armor"), "monsters": len(mon), "pals": len(pals)},
    "adventurers": adv,
    "gear": gear,
    "pals": pals,
    "monsters": mon,
    "teams": teams,
}
io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
print("data.json", os.path.getsize(OUT), "bytes")
print("counts", data["counts"])
print("no image:", sum(1 for x in adv + gear + pals + mon if not x["img"]))
