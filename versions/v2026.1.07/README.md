# 魔物獵人：旅人助手（Monster Hunter Outlanders Helper）

HIS J17｜為《魔物獵人：旅人》（MHO）而做的隨身資料庫，手機優先（760px 深色、底部 4 Tab）。
資料全部來自飛書「Video Games」Base，前端只讀本地 `data.json` / `news-cache.json`，不直連 API。

## Header

右上角固定顯示（只此三行，不放其他字眼）：

```
資料來源：Video Games Base（冒險者／武器防具／隨從／魔物）
更新 YYYY-MM-DD HH:MM｜v2026.1.07｜ https://www.doubao.com/base/RhuZbZCs0aJhdDsKvMicds5Hn0d
```

左上角 Logo 用 Register List 該條記錄「圖標」欄的附件（`channels4_profile.jpg` → `images/logo.jpg`，bytes 對齊不另製，圓形 34px）；
同一張圖亦設為頁面 favicon（`<link rel="icon">`），瀏覽器分頁標籤顯示同一個 MHO logo；
底部 Tab 圖標：冒險者用彌多律頭像（`images/reczz28W1fqrmNCp.webp`）、魔物用光稜龍 Profile Pict（`images/reczz28WqB6QiE7m_pict.png`），圓形 22px、選中時加藍框；
標題與 Register List `HIS Tools` 名稱對齊為「魔物獵人 旅人助手」。

## 四個 Tab

| Tab | 內容 | 說明 |
|---|---|---|
| 🛡️ 冒險者 | 冒險者圖庫（14 位） | 卡片點入 → 全部詳細：定位／屬性／擁有日期、攻略與介紹影片、**武器詳細**、**裝備詳細**（5 部位）、**發動技能**、**隨從**、所屬隊伍；最底加「能剋制的魔物」「難打的魔物」圖庫（點入可跳去魔物詳情） |
| ⚔️ 武器防具 | 357 件裝備（武器 172／防具 185） | 可搜尋（裝備名／套裝／技能）＋ FILTER（類別／武器種類／部位／屬性），點入看能力值、套裝技能、技能清單 |
| 🐲 魔物 | 57 隻魔物 | 點入先看一張 **matrix 表**（同一形式「3 格方塊 + 星數」）：屬性弱點／異常弱點／道具・陷阱效果／咆哮・風壓・震動／肉質；另有異常狀態攻擊、可破壞部位、棲息地、種類／尺寸；最底「能制剋牠的冒險者」「被牠剋制的冒險者」 |
| 📰 新聞 | News Feed List 動態 | 只取 `Job ID` link 指向 J17 的來源，現時 3 個 Feed / 39 條，按日期分組、有縮圖、可點開原文 |

### 魔物 matrix 表的星級口徑

| 區塊 | 取值 → 星 |
|---|---|
| 屬性弱點 | `弱點火/水/雷/冰/龍` 原值（0–3） |
| 異常弱點 | `異常弱點` 文字（如「毒 3星、睡眠 2星」）逐項拆出 |
| 道具／陷阱效果 | `有效` = 3 星（綠）／`無效` = 0 星（紅） |
| 咆哮／風壓／震動 | `大` = 3 星／`中` = 2 星／`小` = 1 星／`無` = 0 星 |
| 肉質 | `部位(斬n/打n/彈n)` 逐部位拆成三組小方塊，右側顯示 `斬/打/彈` |

方塊顏色沿用全站語義：3 星紅 `#f85149`、2 星黃 `#f0b429`、1 星綠 `#3fb950`、0 星灰。

### 冒險者 ↔ 魔物 互聯規則（程式化，非人手填）

- 冒險者「主屬性」= 其 `屬性` 欄第一個屬性值。
- **能剋制的魔物** = 該屬性對應弱點 ≥3 星；若一隻都沒有，放寬到 ≥2 星（每邊最多 8 隻）。
- **難打的魔物** = 該屬性弱點 = 0 星（最多 8 隻）。
- 魔物頁用同一份資料反查：**能制剋牠的冒險者** = 弱點最高星（max）對應屬性的冒險者；**被牠剋制的冒險者** = 該魔物 0 星弱點屬性的冒險者。
- 沒有屬性（路加／阿坎亞／朧／瑪德琳／羅德／菈雅／光赫／法里歐）的冒險者，詳情頁不會出現這兩個圖庫。

## 資料來源（Video Games Base `RhuZbZCs0aJhdDsKvMicds5Hn0d`）

| 表 | table_id | 筆數 |
|---|---|---|
| 冒險者 | `tblYrAeCY4eye7A3` | 14 |
| 武器防具 | `tblrT0r8Urn7JQOv` | 357（武器 172／防具 185） |
| 隨從 | `tblMXptKXbfQcbY1` | 38 |
| 隊伍 | `tblRfOxsRMxC9Cvl` | 4 |
| 魔物 | `tbljeaBoOZps0NlX` | 57（21 欄位） |

新聞來源：HIS Tools Base `An0abQoUBalSqJsG66ucDzT3ncg` → News Feed List `tblHXtZC4Dc0RpEQ`，
篩選條件為 `Job ID` link 指向常數設定 `tbldGpfjk9ylijwU` 的 J17 記錄（`reczz28WqHQpirNP`）。

現時 3 個 Feed（均由 `build_news.py` 自動分派抓法）：

| 名稱 | Source Type | URL | 抓法 |
|---|---|---|---|
| 官方 | Webpage | `https://mho.garena.com/zh_tw` | 官網 `/zh_tw/news` 的 `__NUXT_DATA__`（devalue 扁平陣列解碼） |
| 官方 | Youtube | `https://www.youtube.com/@MHO_TW` | `/videos` 頁 `ytInitialData` 的 `lockupViewModel`，逐片取 `uploadDate` 定日期；RSS `feeds/videos.xml` 已失效（404）不可用 |
| Tutorial | Webpage | `https://gamewith.ai/monster-hunter-outlanders/zh-hant/articles` | 列表頁 `<li><a href>` + `<time dateTime>`（大小寫敏感）+ `<span class="rounded">` 分類；正文第一張 `assets.gamewith.ai` 圖作縮圖；取最新 12 篇 |

## 檔案結構

```
MHO/
├─ index.html            單檔前端（4 Tab + 詳情面板，760px 深色）
├─ data.json             由 build_data.py 生成（冒險者／裝備／隨從／魔物／隊伍／互聯）
├─ news-cache.json       由 build_news.py 生成（新聞 39 條 / 3 Feed）
├─ news-img/             新聞縮圖快取（URL hash 命名）
├─ images/<record_id>.*  Base 附件原始圖（冒險者／裝備／隨從）
├─ images/<record_id>_pict.*  魔物 Profile Pict
├─ images/logo.jpg       Register List 圖標（Header logo）
├─ build/
│   ├─ build_data.py     讀 _raw/*.ndjson → data.json
│   └─ build_news.py     讀 News Feed List（J17）→ news-cache.json + news-img/
├─ _raw/                 各表 ndjson dump、除錯腳本（不影響前端）
├─ start-localhost.bat   啟動 localhost：8792
└─ README.md
```

## 重建資料

```bat
cd /d "D:\Onedrive\Harry Information System\豆包Agents Program Backup\MHO"
python build\build_data.py
python build\build_news.py
```

`build_data.py` 讀 `_raw/adventurers*.ndjson`、`gear*.ndjson`、`pals*.ndjson`、`teams*.ndjson`、`monsters*.ndjson`
（同一表可有多個分頁檔，會自動去重），並把 `images/<record_id>.*` 對應到記錄；圖片優先序為
`<id>_pict`（魔物 Profile Pict）> 原檔名 > `<id>_icon`（舊 Icon 欄，已不再使用）。

更新 Base 後重新 dump：

```bat
lark-cli base +record-list --base-token RhuZbZCs0aJhdDsKvMicds5Hn0d --table-id <table_id> --as user --format ndjson --output "_raw\<name>.ndjson" --limit 200
```

（`+record-list` 單次上限 200，357 件裝備需 `--offset 200` 再 dump 第二個分頁檔。）

## 本地測試

```bat
start-localhost.bat
```

開 `http://127.0.0.1:8792/index.html`。直接雙擊 `index.html`（file://）會因跨來源限制讀不到 JSON，屬正常。
改完 HTML 必先跑語法檢查：`python _raw\extract_js.py`（抽 `<script>` 再 `node --check`）。

## 已知資料缺口（來自 Base 現況，非前端問題）

- 14 位冒險者只有 6 位掛了武器／防具 link（彌多律、瑪德琳、炎囂、御谷龍之介、冒險者(長槍) 等），其餘詳情頁顯示「尚未收錄」。
- 隨從表有 38 位，但只有 2 位被冒險者引用。
- 裝備剩 1 件無圖：`reczz28W1jSAYJ3p` 飛龍刀 [紅葉] II（Base 該欄本就空）。
- 魔物 8 個新欄位仍有空值：`異常狀態攻擊` 31 空、`可破壞部位` 19 空、`咆哮/風壓/震動` 各 19 空、`閃光彈/音爆彈/地洞` 各 20 空、`肉質/異常弱點` 19 空；前端如實不顯示，不補假值。
- gamewith 列表有 103 篇，前端只取最新 12 篇，避免蓋過官方消息。

## 版本

- v2026.1.07（建立 J17：四 Tab 前端 + 資料生成腳本 + 魔物 8 新欄位 + 星級 matrix 表 + 冒險者／魔物互聯 + News Feed List 三來源 + Header 資料來源與 Register List 圖標）
