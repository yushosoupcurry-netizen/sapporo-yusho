# -*- coding: utf-8 -*-
"""
札幌湯匠 官方網站 — 網站產生器（只需 Python 3）

    python3 build.py

輸出：
  dist/            上傳到 Cloudways 的 public_html（含 api/ 綠界結帳後端、admin/ 訂單後台）
  dist-artifact/   claude.ai 發佈版（無後端：結帳改為電話／LINE 確認）
"""
import html, json, os, shutil, datetime
import config as C
from content import L, VEG, SOUP_CURRY, AGED_CURRY, CRAFT, COMMITMENTS, FROZEN, HEAT, NEWS, FAQ, BENTO, BENTO_TAG

ROOT = os.path.dirname(os.path.abspath(__file__))
e = html.escape
YEAR = datetime.date.today().year
MODE = "contact"          # 由 build() 依輸出目標設定：ecpay / contact
ARTIFACT = False

FONTS = ("https://fonts.googleapis.com/css2?family=Bodoni+Moda:wght@400;500;600"
         "&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@500;700;900"
         "&family=Shippori+Mincho+B1:wght@500;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap")

PAGES = {
    "home":     dict(file="index.html",          t=L("首頁", "トップ"), en="Home"),
    "products": dict(file="products.html",       t=L("商品介紹", "商品紹介"), en="Products"),
    "menu":     dict(file="menu.html",           t=L("門市菜單", "店舗メニュー"), en="Menu", parent="products"),
    "bento":    dict(file="bento.html",          t=L("百貨催事弁當", "催事のお弁当"), en="Pop-up Bento", parent="products"),
    "store":    dict(file="store.html",          t=L("門市資訊", "店舗情報"), en="Store"),
    "shop":     dict(file="shop.html",           t=L("線上訂購", "オンラインショップ"), en="Online Shop", parent="products"),
    "news":     dict(file="news.html",           t=L("最新消息", "お知らせ"), en="News"),
    "story":    dict(file="story.html",          t=L("關於湯匠", "札幌湯匠について"), nav=L("關於湯匠", "ブランド"), en="About"),
    "company":  dict(file="company.html",        t=L("公司資訊", "会社概要"), en="Company", parent="story"),
    "catering": dict(file="catering.html",       t=L("團體・企業訂購", "法人・団体のご注文"), nav=L("團體訂購", "団体注文"), en="Catering"),
    "faq":      dict(file="faq.html",            t=L("常見問題", "よくあるご質問"), en="FAQ"),
    "sitemap":  dict(file="sitemap.html",        t=L("網站地圖", "サイトマップ"), en="Sitemap"),
    "cart":     dict(file="cart.html",           t=L("購物車", "カート"), en="Cart", parent="shop"),
    "checkout": dict(file="checkout.html",       t=L("結帳", "ご注文手続き"), en="Checkout", parent="shop"),
    "complete": dict(file="order-complete.html", t=L("訂單完成", "ご注文完了"), en="Thank You", parent="shop"),
    "terms":    dict(file="terms.html",          t=L("購物須知", "ご購入について"), nav=L("購物須知", "ご購入ガイド"), en="Guide"),
    "privacy":  dict(file="privacy.html",        t=L("隱私權政策", "プライバシーポリシー"), en="Privacy Policy"),
    "404":      dict(file="404.html",            t=L("找不到頁面", "ページが見つかりません"), en="Not Found"),
}
for _p in FROZEN:
    PAGES["p-" + _p["id"]] = dict(file=f'product-{_p["id"]}.html', t=_p["short"], en=_p["en"], parent="shop")
NAV = ["home", "news", "products", "store", "terms", "story", "catering"]
NOINDEX = {"cart", "checkout", "complete", "404"}


def url(slug, lang):
    f = PAGES[slug]["file"]
    if lang == "zh":
        return f
    return "ja.html" if f == "index.html" else "ja-" + f


def t(d, lang):
    return d[lang]


def yen(n, tax=None):
    tx = f'<small class="yen__tax">{e(tax)}</small>' if tax else ""
    return f'<span class="yen"><small>NT$</small>{n:,}{tx}</span>'


def price(n, lang):
    if n is None:
        return '<span class="yen yen--tbd">' + ("価格は店頭にて" if lang == "ja" else "價格依門市公告") + "</span>"
    return yen(n, "税込" if lang == "ja" else "含稅")


def tel():
    return f'<a class="tel" href="tel:{C.STORE["phone_intl"]}">{C.STORE["phone"]}</a>'


def btn(href, text, kind="navy", ext=False):
    tgt = ' target="_blank" rel="noopener"' if ext else ""
    return f'<a class="btn btn--{kind}" href="{href}"{tgt}><span>{e(text)}</span><i aria-hidden="true">›</i></a>'


def sh(title, en, more_href=None, more_text=None, light=False, tag="h2"):
    m = f'<a class="sh__more" href="{more_href}">{e(more_text)}<i aria-hidden="true">›</i></a>' if more_href else ""
    return f'<div class="sh{" sh--light" if light else ""}"><{tag} class="sh__t">{title}</{tag}><p class="sh__en">{e(en)}</p>{m}</div>'


def chip(text, kind=""):
    return f'<span class="chip{" chip--" + kind if kind else ""}">{e(text)}</span>'


def seal(text):
    return f'<span class="seal" aria-hidden="true">{e(text)}</span>'


ICON = {
    "cart": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h2.2l2.1 10.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.8L20 7H6.1" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="9.5" cy="19" r="1.4" fill="currentColor"/><circle cx="17" cy="19" r="1.4" fill="currentColor"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 3.5 9 3l1.6 4.2-1.9 1.4a11 11 0 0 0 6.7 6.7l1.4-1.9L21 15l-.5 2.4a2 2 0 0 1-2 1.6A15.5 15.5 0 0 1 5 5.5a2 2 0 0 1 1.6-2Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.1-6.5-11a6.5 6.5 0 0 1 13 0c0 4.9-6.5 11-6.5 11Z" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="10" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    "bowl": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0Zm6 8h6M9 9c-1-1 1-2 0-4m3 4c-1-1 1-2 0-4m3 4c-1-1 1-2 0-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H9l-5 4V5Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    "search": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="m15 15 5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "up": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 14 6-6 6 6" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
}


STEAM = ('<svg class="steam" viewBox="0 0 200 220" aria-hidden="true">'
         '<path d="M70 210c-18-26 18-40 0-66s16-42 0-70" /><path d="M100 214c-18-30 20-44 0-74s18-44 0-74" /><path d="M130 210c-18-26 18-40 0-66s16-42 0-70" /></svg>')


def marquee(lang, dark=False):
    ja = lang == "ja"
    words = (["SAPPORO SOUP CURRY", "札幌湯匠", "ダブル高湯", "23種のスパイス", "72時間熟成", "お持ち帰り可", "冷凍スープカレー"] if ja else
             ["SAPPORO SOUP CURRY", "札幌湯匠", "雙重高湯", "23 種香料", "72 小時熟成", "全品項外帶", "冷凍宅配"])
    run = "".join(f"<span>{e(w)}</span><i>✦</i>" for w in words)
    return f'<div class="marq{" marq--dark" if dark else ""}"><div class="marq__run">{run}{run}</div></div>'


# ───────── 外殼 ─────────
def navl(s, lang):
    return t(PAGES[s].get("nav", PAGES[s]["t"]), lang)


def tree(lang):
    """全站導覽樹：主選單、下拉選單、頁尾網站地圖、網站地圖頁共用。"""
    u = lambda s, a="": url(s, lang) + a
    k = lambda h, zh, ja, img=None: (h, L(zh, ja), img)
    return [
        ("home", []),
        ("news", []),
        ("products", [k(u("products", "#cat=soup"), "湯咖哩", "スープカレー", "cat-soup.jpg"), k(u("products", "#cat=aged"), "熟成咖哩", "熟成カレー", "cat-aged.jpg"),
                      k(u("products", "#cat=bento"), "玉子燒弁當", "玉子焼き弁当", "cat-bento.jpg"), k(u("products", "#cat=frozen"), "冷凍調理包", "冷凍スープカレー", "cat-frozen.jpg"),
                      k(u("menu"), "門市菜單・點餐方式", "店舗メニュー・ご注文方法"), k(u("bento"), "百貨催事弁當", "催事のお弁当"), k(u("shop"), "線上訂購（冷凍宅配）", "オンラインショップ")]),
        ("store", [k(u("store", "#dali"), "台中大里店", "台中大里店", "cat-store.jpg"), k(u("store", "#popup"), "百貨催事出店", "催事への出店", "cat-popup.jpg")]),
        ("terms", []),
        ("story", [k(u("story", "#story"), "品牌故事", "ブランドストーリー", "cat-story.jpg"), k(u("story", "#commitment"), "湯匠的堅持", "こだわり", "cat-commit.jpg"),
                   k(u("story", "#process"), "湯咖哩的工序", "スープができるまで", "cat-process.jpg"), k(u("company"), "公司資訊", "会社概要")]),
        ("catering", []),
    ]


def header(slug, lang):
    ja = lang == "ja"
    other = "ja" if lang == "zh" else "zh"
    p = PAGES[slug].get("parent")
    cur = p or slug
    if p and PAGES[p].get("parent"):
        cur = PAGES[p]["parent"]
    items = []
    for s, kids in tree(lang):
        mega = ""
        if kids:
            cards = "".join(
                f'<li><a href="{h}">' + (f'<span class="mega__img"><img src="img/{img}" alt="" loading="lazy" width="640" height="480"></span>' if img else "")
                + f'<span class="mega__l">{e(t(lb, lang))}<i aria-hidden="true">›</i></span></a></li>' for h, lb, img in kids)
            mega = (f'<div class="mega"><div class="mega__in"><div class="mega__head"><p class="mega__t">{e(t(PAGES[s]["t"], lang))}</p>'
                    f'<p class="mega__en">{e(PAGES[s]["en"])}</p><a class="mega__all" href="{url(s, lang)}">{"一覧を見る" if ja else "看全部"}<i aria-hidden="true">›</i></a></div>'
                    f'<ul class="mega__list">{cards}</ul></div></div>')
        cur_attr = ' aria-current="page"' if s == cur else ""
        items.append(f'<li class="gnav__item{" has-mega" if kids else ""}"><a class="gnav__a" href="{url(s, lang)}"{cur_attr}>'
                     f'<span>{e(navl(s, lang))}</span><small>{e(PAGES[s]["en"])}</small></a>{mega}</li>')
    cart = f'<a class="hd__cart" href="{url("cart", lang)}" aria-label="{"カート" if ja else "購物車"}">{ICON["cart"]}<span class="hd__bt">{"カート" if ja else "購物車"}</span><b class="badge" data-cart-count hidden>0</b></a>'
    return f'''
<a class="skip" href="#main">{"本文へ" if ja else "跳至主要內容"}</a>
<div class="util">
  <p class="util__l">{"北海道スープカレー専門店　台中・大里" if ja else "北海道湯咖哩專門店　台中・大里"}</p>
  <p class="util__r"><a href="{url("faq", lang)}">{e(t(PAGES["faq"]["t"], lang))}</a><a href="{url("sitemap", lang)}">{e(t(PAGES["sitemap"]["t"], lang))}</a>
  <span class="util__tel">TEL {tel()}</span>
  <a class="util__lang" href="{url(slug, other)}" hreflang="{"zh-Hant-TW" if other == "zh" else "ja"}">{"中文" if other == "zh" else "日本語"}</a></p>
</div>
<header class="hd">
  <div class="hd__in">
    <a class="logo" href="{url("home", lang)}" aria-label="札幌湯匠 SAPPORO SOUP CURRY">
      <img class="logo__mark" src="img/logo-bear.png" alt="" width="44" height="43">
      <span class="logo__txt"><b>札幌湯匠</b><small>SAPPORO SOUP CURRY</small></span>
    </a>
    <input type="checkbox" id="nav-t" class="nav-t">
    <nav class="gnav" aria-label="{"メインメニュー" if ja else "主選單"}">
      <ul class="gnav__list">{"".join(items)}</ul>
      <ul class="gnav__util"><li><a href="{url("faq", lang)}">{e(t(PAGES["faq"]["t"], lang))}</a></li><li><a href="{url("sitemap", lang)}">{e(t(PAGES["sitemap"]["t"], lang))}</a></li>
      <li><a href="{url(slug, other)}">{"中文" if other == "zh" else "日本語"}</a></li><li class="gnav__tel">TEL {tel()}</li></ul>
    </nav>
    <div class="hd__act">
      <a class="hd__store" href="{url("store", lang)}">{ICON["pin"]}<span class="hd__bt">{"店舗を探す" if ja else "找門市"}</span></a>
      {cart}
      <label for="nav-t" class="burger" aria-label="{"メニュー" if ja else "選單"}"><span></span><em>MENU</em></label>
    </div>
  </div>
</header>'''


def footer(lang):
    ja = lang == "ja"
    S, CO, SH = C.STORE, C.COMPANY, C.SHIPPING
    legal = [e(CO["name"])]
    if CO["tax_id"]:
        legal.append(("統一番号 " if ja else "統一編號 ") + e(CO["tax_id"]))
    if CO["food_license"]:
        legal.append(("食品業者登録番号 " if ja else "食品業者登錄字號 ") + e(CO["food_license"]))
    social = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{n}</a></li>'
                     for n, u in (("LINE", S["line_url"]), ("Instagram", S["instagram"]), ("Facebook", S["facebook"])) if u)
    cols = []
    loose = []
    for s, kids in tree(lang):
        if kids:
            li = "".join(f'<li><a href="{h}">{e(t(lb, lang))}</a></li>' for h, lb, _ in kids)
            cols.append(f'<div class="ft__col"><p class="ft__h"><a href="{url(s, lang)}">{e(t(PAGES[s]["t"], lang))}</a></p><ul>{li}</ul></div>')
        else:
            loose.append(s)
    other = "".join(f'<li><a href="{url(s, lang)}">{e(t(PAGES[s]["t"], lang))}</a></li>' for s in [x for x in loose if x != "home"] + ["faq", "sitemap"])
    cols.append(f'<div class="ft__col"><p class="ft__h">{"サポート" if ja else "其他"}</p><ul>{other}</ul></div>')
    cta = [("store", ICON["pin"], "店舗を探す" if ja else "找門市", "台中大里店・催事への出店" if ja else "台中大里店・百貨催事"),
           ("shop", ICON["cart"], "オンラインショップ" if ja else "線上訂購", "冷凍スープカレーを宅配で" if ja else "冷凍湯咖哩調理包宅配到家"),
           ("catering", ICON["bowl"], "法人・団体のご注文" if ja else "團體・企業訂購", "会議・イベントのお弁当" if ja else "會議餐盒、活動聚餐")]
    cta_html = "".join(f'<a class="fcta__i" href="{url(s, lang)}"><span class="fcta__ic">{ic}</span><span><b>{e(a)}</b><small>{e(b)}</small></span><i aria-hidden="true">›</i></a>' for s, ic, a, b in cta)
    pay = "ECPay（綠界）安全決済" if ja else "綠界科技 ECPay 安全付款"
    ship = SH["carrier"] or ("冷凍配送" if ja else "冷凍宅配")
    return f'''
<nav class="fcta" aria-label="{"ご案内" if ja else "服務導覽"}">{cta_html}</nav>
<footer class="ft">
  <div class="ft__in">
    <div class="ft__brand">
      <a href="{url("home", lang)}" class="ft__logo"><img src="img/logo-mark.png" alt="YUSHO SOUP CURRY HOKKAIDO" width="96" height="105"></a>
      <div>
        <p class="ft__name">{e(S["name_ja"] if ja else S["name_zh"])}</p>
        <p>{e(S["address_ja"] if ja else S["address_zh"])}</p>
        <p>TEL {tel()}</p>
        {f'<p>{e(S["hours"])}</p>' if S["hours"] else ""}
        {f'<ul class="ft__social">{social}</ul>' if social else ""}
      </div>
    </div>
    <nav class="ft__map" aria-label="{"サイトマップ" if ja else "網站導覽"}">{"".join(cols)}</nav>
  </div>
  <div class="ft__base">
    <ul class="ft__legal"><li><a href="{url("privacy", lang)}">{e(t(PAGES["privacy"]["t"], lang))}</a></li><li><a href="{url("terms", lang)}">{e(t(PAGES["terms"]["t"], lang))}</a></li><li><a href="{url("sitemap", lang)}">{e(t(PAGES["sitemap"]["t"], lang))}</a></li><li>{"決済" if ja else "付款"}：{pay}</li><li>{"配送" if ja else "配送"}：{e(ship)}</li></ul>
    <p>{" ／ ".join(legal)}　© {YEAR} SAPPORO SOUP CURRY</p>
  </div>
</footer>'''


def floating(lang):
    ja = lang == "ja"
    S = C.STORE
    fourth = (f'<a href="{e(S["line_url"])}" target="_blank" rel="noopener">{ICON["chat"]}<span>LINE</span></a>' if S["line_url"]
              else f'<a href="{url("menu", lang)}">{ICON["bowl"]}<span>{"メニュー" if ja else "菜單"}</span></a>')
    return f'''
<nav class="mbar" aria-label="{"クイックメニュー" if ja else "快速選單"}">
  <a href="tel:{S["phone_intl"]}">{ICON["phone"]}<span>{"電話" if ja else "電話"}</span></a>
  <a href="{S["map_url"]}" target="_blank" rel="noopener">{ICON["pin"]}<span>{"地図" if ja else "導航"}</span></a>
  {fourth}
  <a href="{url("cart", lang)}" class="mbar__cart">{ICON["cart"]}<span>{"カート" if ja else "購物車"}</span><b class="badge" data-cart-count hidden>0</b></a>
</nav>
<button type="button" class="totop" aria-label="{"ページ上部へ" if ja else "回到頁首"}" hidden>{ICON["up"]}</button>
<div class="toast" role="status" aria-live="polite" hidden></div>'''


def site_data(lang):
    ja = lang == "ja"
    prods = [dict(id=p["id"], name=t(p["short"], lang), price=C.FROZEN_PRICES[p["id"]]["price"],
                  max=C.FROZEN_PRICES[p["id"]]["max_qty"], img="img/" + p["img"], net=t(p["net"], lang).split("（")[0],
                  url=url("p-" + p["id"], lang)) for p in FROZEN]
    tx = dict(
        added="已加入購物車：{n}" if not ja else "カートに追加しました：{n}",
        toCart="查看購物車" if not ja else "カートを見る",
        empty="購物車目前是空的。" if not ja else "カートに商品がありません。",
        toShop="前往線上商店" if not ja else "ショップへ",
        remove="移除" if not ja else "削除", qty="數量" if not ja else "数量",
        subtotal="商品小計" if not ja else "小計", shipping="運費" if not ja else "送料", total="合計" if not ja else "合計",
        free="免運" if not ja else "無料", shipTbd="訂單確認時通知" if not ja else "ご注文確認時にご案内",
        freeLeft="再買 {n} 即可免運" if not ja else "あと {n} で送料無料",
        checkout="前往結帳" if not ja else "ご注文手続きへ", copied="已複製" if not ja else "コピーしました",
        copyFail="請手動選取文字複製" if not ja else "テキストを選択してコピーしてください",
        orderNo="訂單編號" if not ja else "注文番号",
    )
    return dict(mode=MODE, lang=lang, products=prods, ship=dict(fee=C.SHIPPING["fee"], free=C.SHIPPING["free_over"]),
                phone=C.STORE["phone"], t=tx, shopUrl=url("shop", lang), cartUrl=url("cart", lang), checkoutUrl=url("checkout", lang))


def page(slug, lang, body, desc, extra_head=""):
    ja = lang == "ja"
    title = ("札幌湯匠｜北海道スープカレー専門店" if ja else "札幌湯匠｜北海道湯咖哩專門店") if slug == "home" \
        else f'{t(PAGES[slug]["t"], lang)}｜札幌湯匠'
    css = open(os.path.join(ROOT, "src", "style.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "src", "site.js"), encoding="utf-8").read()
    canon = ""
    if C.SITE_URL and slug not in NOINDEX:
        base = C.SITE_URL.rstrip("/")
        canon = (f'<link rel="canonical" href="{base}/{url(slug, lang)}">'
                 f'<link rel="alternate" hreflang="zh-Hant-TW" href="{base}/{url(slug, "zh")}">'
                 f'<link rel="alternate" hreflang="ja" href="{base}/{url(slug, "ja")}">'
                 f'<meta property="og:url" content="{base}/{url(slug, lang)}">'
                 f'<meta property="og:image" content="{base}/img/hero-three-bowls.jpg">')
    robots = '<meta name="robots" content="noindex">' if slug in NOINDEX else ""
    ga = ""
    if C.GA_ID:
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={C.GA_ID}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{C.GA_ID}',{{anonymize_ip:true}});</script>")
    head = f'''<title>{e(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">{robots}
<meta name="theme-color" content="#182338">
<meta property="og:type" content="website"><meta property="og:site_name" content="札幌湯匠"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:locale" content="{"ja_JP" if ja else "zh_TW"}">{canon}
<link rel="icon" href="img/logo-bear.png"><link rel="apple-touch-icon" href="img/logo-bear.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{css}</style>{extra_head}{ga}'''
    data = json.dumps(site_data(lang), ensure_ascii=False).replace("</", "<\\/")
    content = (f'<div class="site site--{slug.split("-")[0]}" lang="{"ja" if ja else "zh-Hant-TW"}">'
               f'{header(slug, lang)}<main id="main">{body}</main>{footer(lang)}{floating(lang)}</div>'
               f'<script type="application/json" id="ys-data">{data}</script><script>{js}</script>')
    if ARTIFACT and slug == "home" and lang == "zh":
        return head + "\n" + content + "\n"
    return (f'<!doctype html><html lang="{"ja" if ja else "zh-Hant-TW"}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">{head}</head>'
            f'<body>{content}</body></html>\n')


def page_head(slug, lang, lead=""):
    ja = lang == "ja"
    ttl = t(PAGES[slug]["t"], lang)
    chain, p = [], PAGES[slug].get("parent")
    while p:
        chain.insert(0, p)
        p = PAGES[p].get("parent")
    mid = "".join(f'<a href="{url(c, lang)}">{e(t(PAGES[c]["t"], lang))}</a><i>›</i>' for c in chain)
    return f'''<section class="ph">
  <div class="ph__in">
    <p class="crumb"><a href="{url("home", lang)}">{"トップ" if ja else "首頁"}</a><i>›</i>{mid}<span>{e(ttl)}</span></p>
    <h1 class="ph__t split">{e(ttl)}</h1>
    <p class="ph__en">{e(PAGES[slug]["en"])}</p>
    {f'<p class="ph__lead">{e(lead)}</p>' if lead else ""}
  </div>
</section>'''


def jsonld(d):
    return f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>'


def jsonld_restaurant():
    S = C.STORE
    d = {"@context": "https://schema.org", "@type": "Restaurant", "name": "札幌湯匠 Sapporo Soup Curry",
         "servesCuisine": ["湯咖哩", "Soup Curry"], "telephone": S["phone_intl"],
         "address": {"@type": "PostalAddress", "streetAddress": "德芳路二段105號1樓", "addressLocality": "大里區",
                     "addressRegion": "台中市", "postalCode": S["postal"], "addressCountry": "TW"}}
    if C.SITE_URL:
        d["url"] = C.SITE_URL
    return jsonld(d)


# ───────── 共用區塊 ─────────
TIME = [
    dict(h=8, v="8", unit=L("小時", "時間"), name=L("雙重高湯", "ダブル高湯"),
         note=L("舒康老母雞燉煮 8 小時，再與日本昆布、鰹節共同熬製，形成乳白色、濃郁而不膩的高湯。", "親鶏を8時間煮込み、日本の昆布・鰹節と合わせた白濁の高湯。")),
    dict(h=1.2, v="72", unit=L("分鐘", "分"), name=L("焦糖洋蔥", "飴色玉ねぎ"),
         note=L("台灣在地洋蔥，低溫慢炒 72 分鐘，釋放自然甜味。", "台湾産の玉ねぎを低温で72分炒め、自然な甘みを引き出します。")),
    dict(h=72, v="72", unit=L("小時", "時間"), name=L("低溫熟成", "低温熟成"),
         note=L("三天三夜低溫熟成，讓二十三種香料與湯底融為一體。", "三日三晩の低温熟成で、23種のスパイスとスープをなじませます。")),
]


def time_ruler(lang):
    ja = lang == "ja"
    rows = "".join(f'''<li class="ruler__row" style="--w:{r["h"] / 72 * 100:.2f}%">
  <p class="ruler__name"><span class="ruler__i">{i + 1}</span>{e(t(r["name"], lang))}</p>
  <p class="ruler__val"><b data-to="{r["v"]}">{r["v"]}</b>{e(t(r["unit"], lang))}</p>
  <div class="ruler__track"><span class="ruler__bar"></span></div>
  <p class="ruler__note">{e(t(r["note"], lang))}</p>
</li>''' for i, r in enumerate(TIME))
    ticks = "".join(f'<span style="left:{h / 72 * 100:.2f}%">{h}h</span>' for h in (0, 24, 48, 72))
    return f'''<figure class="ruler" aria-label="{"工程にかかる時間" if ja else "各工序所需時間（同一比例尺）"}">
  <ol class="ruler__rows">{rows}</ol>
  <div class="ruler__ticks" aria-hidden="true">{ticks}</div>
  <figcaption>{"三つの工程を同じ物差しで。いちばん長いのは、待つ時間です。" if ja else "三道工序，以同一把尺繪製。最長的一段，是等待。"}</figcaption>
</figure>'''


def store_dl(lang):
    ja = lang == "ja"
    S = C.STORE
    hours = e(S["hours"]) if S["hours"] else (
        f'<a class="u" href="{S["map_url"]}" target="_blank" rel="noopener">{"Googleマップでご確認ください" if ja else "請見 Google 地圖最新營業時間"}</a>')
    line = (f'<tr><th>LINE</th><td><a class="u" href="{e(S["line_url"])}" target="_blank" rel="noopener">{"友だち追加" if ja else "加入好友"}</a></td></tr>'
            if S["line_url"] else "")
    return f'''<table class="tbl">
  <tr><th>{"住所" if ja else "地址"}</th><td>{e(S["address_ja"] if ja else S["address_zh"])}</td></tr>
  <tr><th>{"電話" if ja else "電話"}</th><td>{tel()}</td></tr>
  <tr><th>{"営業時間" if ja else "營業時間"}</th><td>{hours}</td></tr>
  <tr><th>{"駐車場" if ja else "停車"}</th><td>{e(S["parking_ja"] if ja else S["parking_zh"])}</td></tr>
  <tr><th>{"お持ち帰り" if ja else "外帶"}</th><td>{"全メニュー可" if ja else "全品項皆可外帶"}</td></tr>{line}
</table>'''


def tile(d, lang):
    ja = lang == "ja"
    img = (f'<img src="img/{d["img"]}" alt="" loading="lazy" width="900" height="660">' if d.get("img")
           else f'<span class="tile__noimg">{"準備中" if ja else "照片準備中"}</span>')
    chips = chip("看板メニュー" if ja else "明星商品", "orange") if d.get("star") else ""
    return f'''<li class="tile">
  <div class="tile__img">{img}</div>
  <div class="tile__body">
    {f'<p class="tile__chips">{chips}</p>' if chips else ""}
    <p class="tile__en">{e(d.get("en", ""))}</p>
    <h3 class="tile__name">{e(t(d["name"], lang))}</h3>
    <p class="tile__desc">{e(t(d["desc"], lang))}</p>
    <p class="tile__price">{price(C.MENU_PRICES.get(d["id"]), lang)}</p>
  </div>
</li>'''


def qty_form(p, lang, compact=False):
    ja = lang == "ja"
    mx = C.FROZEN_PRICES[p["id"]]["max_qty"]
    return f'''<form class="atc{" atc--compact" if compact else ""}" data-id="{p["id"]}">
  <div class="qty"><button type="button" data-step="-1" aria-label="{"減らす" if ja else "減少"}">−</button><input type="number" name="qty" value="1" min="1" max="{mx}" inputmode="numeric" aria-label="{"数量" if ja else "數量"}"><button type="button" data-step="1" aria-label="{"増やす" if ja else "增加"}">+</button></div>
  <button type="submit" class="atc__btn">{ICON["cart"]}<span>{"カートに入れる" if ja else "加入購物車"}</span></button>
</form>'''


def pack_tile(p, lang, full=False):
    ja = lang == "ja"
    return f'''<li class="ptile">
  <a class="ptile__img" href="{url("p-" + p["id"], lang)}"><img src="img/{p["img"]}" alt="{e(t(p["name"], lang))}" loading="lazy" width="800" height="1092"></a>
  <p class="tile__chips">{chip("要冷凍" if ja else "需冷凍", "navy")}{chip(t(p["net"], lang).split("（")[0])}</p>
  <h3 class="tile__name"><a href="{url("p-" + p["id"], lang)}">{e(t(p["short"], lang))}</a></h3>
  <p class="tile__en">{e(p["en"])}</p>
  <p class="tile__price">{yen(C.FROZEN_PRICES[p["id"]]["price"], "税込" if ja else "含稅")}</p>
  {qty_form(p, lang, compact=True) if full else ""}
</li>'''


def news_list(lang, limit=None, cats=None):
    ja = lang == "ja"
    rows = "".join(f'''<li class="news__item"{f' data-c="c{cats.index(n["tag"]["zh"])}"' if cats else ""}><time>{n["date"]}</time>{chip(t(n["tag"], lang), "navy" if i == 0 else "")}
  <div><p class="news__t">{e(t(n["title"], lang))}</p><p class="news__b">{e(t(n["body"], lang))}{f'<small>（{e(n["source"])}）</small>' if n.get("source") else ""}</p></div></li>'''
                   for i, n in enumerate(NEWS[:limit] if limit else NEWS))
    return f'<ul class="news">{rows}</ul>'


def ctab(items, label):
    """頁內分類分頁（黏在頁首下方，捲動時自動標示目前區塊）"""
    li = "".join(f'<li><a href="{h}">{e(x)}</a></li>' for h, x in items)
    return f'<nav class="ctab" aria-label="{e(label)}" data-ctab><ul>{li}</ul></nav>'


def notes(lines):
    return '<ul class="notes">' + "".join(f"<li>{e(x)}</li>" for x in lines) + "</ul>"


# ───────── 商品介紹（比照富帆商店：多種分類索引＋分類列表＋商品列表） ─────────
PCATS = [("soup", L("湯咖哩", "スープカレー"), L("スープカレー", "湯咖哩"), "cat-soup.jpg"),
         ("aged", L("熟成咖哩", "熟成カレー"), L("じゅくせいカレー", "熟成咖哩"), "cat-aged.jpg"),
         ("bento", L("玉子燒弁當", "玉子焼き弁当"), L("たまごやきべんとう", "玉子燒弁當"), "cat-bento.jpg"),
         ("frozen", L("冷凍調理包", "冷凍スープカレー"), L("れいとうパック", "冷凍調理包"), "cat-frozen.jpg")]
PING = [("beef", L("牛肉", "牛肉"), "ぎゅうにく"), ("pork", L("豬肉", "豚肉"), "ぶたにく"), ("chicken", L("雞肉", "鶏肉"), "とりにく"),
        ("sea", L("海鮮", "魚介"), "ぎょかい"), ("veg", L("蔬菜・湯底", "野菜・スープ"), "やさい")]
PBUY = [("dine", L("門市內用", "店内飲食"), L("台中大里店", "台中大里店")), ("togo", L("外帶", "お持ち帰り"), L("全品項皆可外帶", "全メニュー対応")),
        ("popup", L("百貨催事", "催事会場"), L("日本展等催事會場", "物産展などの催事会場")), ("online", L("線上宅配", "オンライン宅配"), L("冷凍宅配到家", "冷凍でお届け"))]
PTAG = [("star", L("明星商品", "看板メニュー")), ("aged72", L("三段熟成", "三段熟成")), ("tamago", L("職人手作玉子燒", "職人の玉子焼き")), ("frozen", L("冷凍宅配", "冷凍配送"))]
_ING = {"soup-beef-rib": "beef", "soup-karaage": "chicken", "soup-pork-cutlet": "pork", "soup-chicken-leg": "chicken", "soup-wagyu-hamburg": "beef",
        "soup-ayu": "sea", "soup-chicken-cutlet": "chicken", "soup-vegetable": "veg", "aged-aged-pork": "pork", "aged-aged-beef": "beef", "aged-aged-ebi": "sea",
        "bento-negishio-pork": "pork", "bento-chashu": "pork", "bento-tuna-shirasu": "sea", "bento-salmon-shirasu": "sea", "bento-gyubara": "beef",
        "bento-unagi": "sea", "frozen-beef-rib": "beef", "frozen-chicken-leg": "chicken", "frozen-soup": "veg"}


def catalog(lang):
    out = []
    for d in SOUP_CURRY:
        out.append(dict(k="soup-" + d["id"], cat="soup", buy=["dine", "togo"], tags=["star"] if d.get("star") else [], name=d["name"], en=d.get("en", ""),
                        desc=d["desc"], img=d.get("img"), fit="cut", price=C.MENU_PRICES.get(d["id"]), spec=L("每碗附十種蔬菜", "野菜10種入り"),
                        more=(url("menu", lang) + "#soup", L("門市菜單", "店舗メニュー")), pid=None))
    for d in AGED_CURRY:
        out.append(dict(k="aged-" + d["id"], cat="aged", buy=["dine", "togo"], tags=["aged72"], name=d["name"], en="Aged Curry",
                        desc=d["desc"], img="aged-curry-cutlet.jpg" if d["id"] == "aged-pork" else None, fit="photo", price=C.MENU_PRICES.get(d["id"]),
                        spec=L("24・48・72 小時三段熟成咖哩醬", "24・48・72時間の三段熟成ルー"), more=(url("menu", lang) + "#aged", L("門市菜單", "店舗メニュー")), pid=None))
    for b in BENTO:
        out.append(dict(k="bento-" + b["id"], cat="bento", buy=["popup"], tags=["tamago"], name=b["name"], en="Tamagoyaki Bento",
                        desc=L(b["desc"]["zh"] + "。" + BENTO_TAG["zh"], b["desc"]["ja"] + "。" + BENTO_TAG["ja"]), img=b["img"], fit="photo", price=b["price"],
                        spec=L("百貨催事會場供應", "催事会場でご用意"), more=(url("bento", lang) + "#bento-" + b["id"], L("百貨催事弁當", "催事のお弁当")), pid=None))
    for f in FROZEN:
        out.append(dict(k="frozen-" + f["id"], cat="frozen", buy=["online", "popup"], tags=["frozen"], name=L(f["short"]["zh"], f["name"]["ja"].replace("（冷凍・スープのみ）", "（スープのみ）").replace("（冷凍）", "")), en=f["en"],
                        desc=f.get("note") or f["short"], img=f["img"], fit="pack", price=C.FROZEN_PRICES[f["id"]]["price"],
                        spec=L(t(f["net"], "zh").split("（")[0] + "／包", t(f["net"], "ja").split("（")[0] + "／袋"), more=(url("p-" + f["id"], lang), L("商品詳細（成分・營養標示）", "商品詳細（原材料・栄養成分）")), pid=f["id"]))
    for x in out:
        x["ing"] = _ING[x["k"]]
    return out


def _lab(lst, key, lang):
    for row in lst:
        if row[0] == key:
            return t(row[1], lang)
    return key


def pimg(x, lang, size=""):
    ja = lang == "ja"
    if not x["img"]:
        return f'<span class="pimg pimg--none{size}"><span>{"写真準備中" if ja else "照片準備中"}</span></span>'
    return f'<span class="pimg pimg--{x["fit"]}{size}"><img src="img/{x["img"]}" alt="" loading="lazy"></span>'


def pcard(x, lang):
    ja = lang == "ja"
    sub = x["name"]["zh"] if ja else x["name"]["ja"]
    tags = "".join(f'<span class="chip{" chip--orange" if g == "star" else ""}">{e(_lab(PTAG, g, lang))}</span>' for g in x["tags"])
    q = " ".join([x["name"]["zh"], x["name"]["ja"], x["en"]]).lower()
    cta = ("数量を選んでカートへ" if ja else "選擇數量・加入購物車") if x["pid"] else ("詳しく見る" if ja else "查看詳情")
    return f'''<li class="pc" data-cat="{x["cat"]}" data-ing="{x["ing"]}" data-buy="{" ".join(x["buy"])}" data-tags="{" ".join(x["tags"])}" data-price="{x["price"] if x["price"] is not None else ""}" data-q="{e(q)}">
  <button type="button" class="pc__a" data-qv="{x["k"]}" aria-haspopup="dialog">
    {pimg(x, lang)}
    <span class="pc__b">
      <span class="pc__tags">{tags}</span>
      <span class="pc__name">{e(t(x["name"], lang))}</span>
      <span class="pc__sub">{e(sub)}</span>
      <span class="pc__spec">{e(t(x["spec"], lang))}</span>
      <span class="pc__price">{price(x["price"], lang)}</span>
      <span class="pc__cta">{cta}<i aria-hidden="true">›</i></span>
    </span>
  </button>
</li>'''


def ptemplate(x, lang):
    ja = lang == "ja"
    sub = x["name"]["zh"] if ja else x["name"]["ja"]
    buy = "・".join(_lab(PBUY, b, lang) for b in x["buy"])
    form = ""
    if x["pid"]:
        p = next(f for f in FROZEN if f["id"] == x["pid"])
        form = f'<p class="qv__h">{"数量をお選びください" if ja else "請選擇數量"}</p>{qty_form(p, lang)}'
    return f'''<template id="qv-{x["k"]}"><div class="qv__grid">
  {pimg(x, lang, " pimg--lg")}
  <div class="qv__body">
    <p class="qv__cat">{e(_lab(PCATS, x["cat"], lang))}<span>{e(x["en"])}</span></p>
    <h2 class="qv__name" id="qv-t">{e(t(x["name"], lang))}</h2>
    <p class="qv__sub">{e(sub)}</p>
    <p class="qv__desc">{e(t(x["desc"], lang))}</p>
    <dl class="qv__dl"><div><dt>{"規格" if not ja else "内容"}</dt><dd>{e(t(x["spec"], lang))}</dd></div><div><dt>{"主な食材" if ja else "主食材"}</dt><dd>{e(_lab(PING, x["ing"], lang))}</dd></div><div><dt>{"ご購入方法" if ja else "購買方式"}</dt><dd>{e(buy)}</dd></div></dl>
    <p class="qv__price">{price(x["price"], lang)}</p>
    {form}
    <a class="qv__more" href="{x["more"][0]}">{e(t(x["more"][1], lang))}<i aria-hidden="true">›</i></a>
  </div>
</div></template>'''


def catcards(lang, items):
    ja = lang == "ja"
    n = {c[0]: sum(1 for x in items if x["cat"] == c[0]) for c in PCATS}
    return '<ul class="ccat">' + "".join(f'''<li><a href="{url("products", lang)}#cat={c}"><span class="ccat__img"><img src="img/{img}" alt="" loading="lazy" width="640" height="480"></span>
  <span class="ccat__b"><b>{e(t(nm, lang))}</b><small>{e(t(rd, lang))}</small><span class="ccat__n">{n[c]} {"品" if ja else "項"}</span></span>
  <span class="ccat__more">{"もっと見る" if ja else "查看更多"}<i aria-hidden="true">›</i></span></a></li>''' for c, nm, rd, img in PCATS) + "</ul>"


def products(lang):
    ja = lang == "ja"
    items = catalog(lang)
    P = url("products", lang)
    cnt = lambda key, v: sum(1 for x in items if (v in x[key] if isinstance(x[key], list) else x[key] == v))
    tabs = [("#by-cat", "カテゴリー" if ja else "品項分類"), ("#by-ing", "食材別" if ja else "主食材分類"), ("#by-buy", "ご購入方法" if ja else "購買方式"),
            ("#by-tag", "タグ" if ja else "商品標籤"), ("#list", "商品一覧" if ja else "商品列表")]
    ing_idx = "".join(f'<li><a href="{P}#ing={k_}"><b>{e(t(nm, lang))}</b><small>{rd}</small><span>{cnt("ing", k_)}</span></a></li>' for k_, nm, rd in PING)
    buy_idx = "".join(f'<li><a href="{P}#buy={k_}"><b>{e(t(nm, lang))}</b><small>{e(t(ds, lang))}</small><span>{cnt("buy", k_)}</span></a></li>' for k_, nm, ds in PBUY)
    tag_idx = "".join(f'<li><a href="{P}#tag={k_}"><b>#{e(t(nm, lang))}</b><span>{cnt("tags", k_)}</span></a></li>' for k_, nm in PTAG)

    def grp(title, key, rows):
        li = f'<li><a href="#" data-k="{key}" data-v="">{"すべて" if ja else "全部"}</a></li>' + "".join(
            f'<li><a href="#{key}={k_}" data-k="{key}" data-v="{k_}">{e(t(nm, lang))}<span>{c_}</span></a></li>' for k_, nm, c_ in rows)
        return f'<div class="pgrp"><p class="pgrp__h">{e(title)}</p><ul>{li}</ul></div>'
    side = (grp("カテゴリー" if ja else "品項分類", "cat", [(c[0], c[1], cnt("cat", c[0])) for c in PCATS])
            + grp("食材別" if ja else "主食材", "ing", [(r[0], r[1], cnt("ing", r[0])) for r in PING])
            + grp("ご購入方法" if ja else "購買方式", "buy", [(r[0], r[1], cnt("buy", r[0])) for r in PBUY])
            + grp("タグ" if ja else "商品標籤", "tag", [(r[0], r[1], cnt("tags", r[0])) for r in PTAG]))
    labels = {"cat": {c[0]: t(c[1], lang) for c in PCATS}, "ing": {r[0]: t(r[1], lang) for r in PING},
              "buy": {r[0]: t(r[1], lang) for r in PBUY}, "tag": {r[0]: t(r[1], lang) for r in PTAG}}
    body = page_head("products", lang, "スープカレー、熟成カレー、玉子焼き弁当、冷凍スープカレー。カテゴリー・食材・ご購入方法から探せます。" if ja
                     else "湯咖哩、熟成咖哩、玉子燒弁當與冷凍調理包，可依品項、主食材、購買方式或標籤查找。") + ctab(tabs, "商品の探し方" if ja else "商品分類") + f'''
<section class="sec anchor" id="by-cat">
  {sh("カテゴリー" if ja else "品項分類", "Category")}
  {catcards(lang, items)}
</section>
<section class="sec sec--tint">
  <div class="pidx">
    <div class="pidx__g anchor" id="by-ing"><h2 class="pidx__h">{"食材別" if ja else "主食材分類"}<small>By Ingredient</small></h2><ul class="pidx__l pidx__l--ing">{ing_idx}</ul></div>
    <div class="pidx__g anchor" id="by-buy"><h2 class="pidx__h">{"ご購入方法" if ja else "購買方式"}<small>Where to Buy</small></h2><ul class="pidx__l">{buy_idx}</ul></div>
    <div class="pidx__g anchor" id="by-tag"><h2 class="pidx__h">{"タグ" if ja else "商品標籤"}<small>Tags</small></h2><ul class="pidx__l pidx__l--tag">{tag_idx}</ul></div>
  </div>
</section>
<section class="sec anchor" id="list">
  {sh("商品一覧" if ja else "商品列表", "Product List")}
  <div class="plist" data-plist data-labels="{e(json.dumps(labels, ensure_ascii=False))}">
    <aside class="pside" aria-label="{"絞り込み" if ja else "分類列表"}">
      <form class="psearch" role="search" data-psearch><input type="search" name="q" placeholder="{"商品名で検索" if ja else "搜尋商品名稱"}" aria-label="{"商品名で検索" if ja else "搜尋商品名稱"}" autocomplete="off"><button type="submit" aria-label="{"検索" if ja else "搜尋"}">{ICON["search"]}</button></form>
      {side}
    </aside>
    <div class="pmain">
      <div class="pbar">
        <p class="pbar__n">{"全" if ja else "共"} <b data-pcount>{len(items)}</b> {"品" if ja else "項商品"}</p>
        <div class="pbar__chips" data-pchips></div>
        <label class="pbar__sort"><span>{"並び替え" if ja else "排序"}</span><select data-psort><option value="rec">{"おすすめ順" if ja else "推薦排序"}</option><option value="asc">{"価格の安い順" if ja else "價格由低到高"}</option><option value="desc">{"価格の高い順" if ja else "價格由高到低"}</option></select></label>
      </div>
      <p class="pq" data-pq hidden></p>
      <ul class="pgrid" data-pgrid>{"".join(pcard(x, lang) for x in items)}</ul>
      <div class="pempty" data-pempty hidden><p>{"条件に合う商品がありません。" if ja else "沒有符合條件的商品。"}</p><button type="button" class="btn btn--line" data-preset><span>{"条件をクリア" if ja else "清除條件"}</span></button></div>
    </div>
  </div>
</section>
<section class="sec">
  {notes(["価格はすべて税込です。", "写真はイメージです。", "店舗メニューは台中大里店、玉子焼き弁当は催事会場でのご提供です。", "冷凍スープカレーはオンラインショップでご注文いただけます。"] if ja else
         ["價格皆含稅。", "圖片僅供參考。", "湯咖哩與熟成咖哩於台中大里店供應；玉子燒弁當於百貨催事會場供應。", "冷凍調理包可於線上訂購、冷凍宅配到府。"])}
</section>
{"".join(ptemplate(x, lang) for x in items)}
<dialog class="qv" id="qv" aria-labelledby="qv-t"><button type="button" class="qv__x" data-qv-close aria-label="{"閉じる" if ja else "關閉"}">×</button><div class="qv__in" data-qv-in></div></dialog>'''
    desc = ("札幌湯匠の商品紹介：スープカレー、熟成カレー、玉子焼き弁当、冷凍スープカレーをカテゴリー・食材・ご購入方法から。" if ja
            else "札幌湯匠商品介紹：湯咖哩、熟成咖哩、玉子燒弁當、冷凍調理包，依品項、主食材、購買方式與標籤分類查找。")
    return body, desc, ""


def bento_card(b, lang):
    ja = lang == "ja"
    main, sub = (b["name"]["ja"], b["name"]["zh"]) if ja else (b["name"]["zh"], b["name"]["ja"])
    return f'''<li class="bt">
  <figure class="bt__img"><img src="img/{b["img"]}" alt="{e(main)}" loading="lazy" width="900" height="900"><span class="bt__stamp" aria-hidden="true">旨</span></figure>
  <div class="bt__body">
    <p class="bt__sub" lang="{"zh-Hant-TW" if ja else "ja"}">{e(sub)}</p>
    <h3 class="bt__name">{e(main)}</h3>
    <p class="bt__desc">{e(t(b["desc"], lang))}</p>
    <p class="bt__price">{price(b["price"], lang)}</p>
  </div>
</li>'''


def bento_rail(lang):
    ja = lang == "ja"
    cards = "".join(f'''<li class="rail__item"><a href="{url("bento", lang)}#bento-{b["id"]}">
  <span class="rail__img"><img src="img/{b["img"]}" alt="" loading="lazy" width="900" height="900"></span>
  <span class="rail__name">{e(t(b["name"], lang))}</span>{price(b["price"], lang)}</a></li>''' for b in BENTO)
    return f'''<div class="rail" data-rail>
  <ul class="rail__track" tabindex="0" aria-label="{"玉子焼き弁当" if ja else "玉子燒弁當"}">{cards}</ul>
  <div class="rail__ui"><span class="rail__bar"><i></i></span>
    <button type="button" class="rail__btn" data-dir="-1" aria-label="{"前へ" if ja else "上一個"}">‹</button><button type="button" class="rail__btn" data-dir="1" aria-label="{"次へ" if ja else "下一個"}">›</button></div>
</div>'''


# ───────── 首頁 ─────────
def home(lang):
    ja = lang == "ja"
    stars = [d for d in SOUP_CURRY if d.get("star")]
    slides = [
        f'''<div class="slide slide--navy is-on">
  <figure class="slide__img"><img src="img/hero-three-bowls.jpg" alt="{"唐揚げ、カツ、牛リブのスープカレー" if ja else "唐揚雞、炸排與牛肋湯咖哩"}" width="2000" height="1398" fetchpriority="high"></figure>
  <div class="slide__panel">
    <h1 class="slide__v split">{"時間を、<br>スープに。" if ja else "把時間<br>熬進湯裡"}</h1>
    <div class="slide__side">
      <p class="slide__kicker">SAPPORO<br>SOUP CURRY</p>
      <p class="slide__lead">{"ダブル高湯、23種のスパイス、72時間の熟成。" if ja else "雙重高湯、23 種香料、72 小時熟成。"}</p>
      {btn(url("menu", lang), "メニューを見る" if ja else "查看菜單", "white")}
    </div>
  </div>
</div>''',
        f'''<div class="slide slide--orange">
  <figure class="slide__img slide__img--packs"><img src="img/pack-beef-rib.jpg" alt="" width="800" height="1092"><img src="img/pack-chicken-leg.jpg" alt="" width="800" height="1092"><img src="img/pack-vegetable.jpg" alt="" width="800" height="1092"></figure>
  <div class="slide__panel">
    <p class="slide__v slide__v--2 split">{"どこで食べても、<br>ちょうどいい。" if ja else "在哪吃，<br>都剛剛好。"}</p>
    <div class="slide__side">
      <p class="slide__kicker">READY-TO-COOK</p>
      <p class="slide__lead">{"お店と同じスープを冷凍で。牛リブ・チキンレッグ・スープのみの三種。" if ja else "與門市相同的湯底，冷凍宅配到家。牛肋、雞腿、純湯咖哩三款。"}</p>
      <p class="slide__price">NT$ <b>199</b> {"から" if ja else "起"}</p>
      {btn(url("shop", lang), "オンラインショップ" if ja else "線上商店", "navy")}
    </div>
  </div>
</div>''',
        f'''<div class="slide slide--wood">
  <figure class="slide__img"><img src="img/takeout-box.jpg" alt="{"テイクアウトボックス" if ja else "湯匠外帶餐盒"}" loading="lazy" width="640" height="890"></figure>
  <div class="slide__panel">
    <p class="slide__v slide__v--2 split">{"お持ち帰りも、<br>お店の味で。" if ja else "湯匠外帶餐盒"}</p>
    <div class="slide__side">
      <p class="slide__kicker">CURRY TO GO</p>
      <p class="slide__lead">{"全メニューお持ち帰りいただけます。スープ・ライス・具材を分けてお詰めします。" if ja else "全品項皆可外帶。湯、飯與配料分裝，帶回家仍保持口感。"}</p>
      <p class="slide__tel">TEL {tel()}</p>
      {btn(url("store", lang), "店舗情報" if ja else "門市資訊", "navy")}
    </div>
  </div>
</div>''',
        f'''<div class="slide slide--navy">
  <figure class="slide__img"><img src="img/booth-noren.jpg" alt="{"百貨店の催事ブース" if ja else "百貨催事攤位"}" loading="lazy" width="1600" height="1200"></figure>
  <div class="slide__panel">
    <p class="slide__v slide__v--2 split">{"催事限定、<br>玉子焼き弁当。" if ja else "百貨催事限定<br>玉子燒弁當"}</p>
    <div class="slide__side">
      <p class="slide__kicker">POP-UP<br>BENTO</p>
      <p class="slide__lead">{"職人が手焼きした玉子焼きに、豚・牛・鰻・しらすを合わせた6種。" if ja else "職人手作玉子燒，搭配豚肉、牛肉、鰻魚、吻仔魚等六款主菜。"}</p>
      <p class="slide__price">NT$ <b>180</b> {"から" if ja else "起"}</p>
      {btn(url("bento", lang), "催事のお弁当" if ja else "看催事弁當", "white")}
    </div>
  </div>
</div>''',
    ]
    dots = "".join(f'<button type="button" class="car__dot" aria-label="{i + 1}"{" aria-current=\"true\"" if i == 0 else ""}></button>' for i in range(len(slides)))
    packs = "".join(pack_tile(p, lang, full=True) for p in FROZEN)
    first = NEWS[0]
    picks = [(url("bento", lang), "cat-bento.jpg", "催事" if ja else "百貨催事", "玉子焼き弁当" if ja else "玉子燒弁當", "NT$180 から・全6種" if ja else "NT$180 起，共六款"),
             (url("shop", lang), "cat-frozen.jpg", "通販" if ja else "線上訂購", "冷凍スープカレー" if ja else "冷凍湯咖哩調理包", "お店の味をご家庭で" if ja else "門市湯底，宅配到家"),
             (url("menu", lang) + "#togo", "cat-togo.jpg", "テイクアウト" if ja else "外帶", "全メニューお持ち帰り可" if ja else "全品項皆可外帶", "スープとライスを分けてお詰め" if ja else "湯、飯與配料分裝"),
             (url("catering", lang), "cat-process.jpg", "法人・団体" if ja else "團體・企業", "まとめてのご注文" if ja else "團體訂購", "会議・イベントのお弁当" if ja else "會議餐盒、活動聚餐")]
    pick = "".join(f'''<li><a class="pick__a" href="{h}"><span class="pick__img"><img src="img/{img}" alt="" loading="lazy" width="640" height="480"></span>
  <span class="pick__b"><span class="chip chip--orange">{e(c)}</span><b>{e(ti)}</b><small>{e(sub)}</small></span><i aria-hidden="true">›</i></a></li>''' for h, img, c, ti, sub in picks)
    mcat = "".join(f'''<li class="mcat__i{" mcat__i--lg" if i == 0 else ""}"><a href="{h}"><span class="mcat__img"><img src="img/{img}" alt="" loading="lazy" width="640" height="480"></span>
  <span class="mcat__l"><b>{e(t(lb, lang))}</b><i aria-hidden="true">›</i></span></a></li>''' for i, (h, lb, img) in enumerate([]))
    body = f'''
<section class="car" aria-roledescription="carousel" aria-label="{"特集" if ja else "主打"}">
  <div class="car__track">{"".join(slides)}</div>
  <div class="car__ui"><button type="button" class="car__nav" data-dir="-1" aria-label="{"前へ" if ja else "上一張"}">‹</button><div class="car__dots">{dots}</div><button type="button" class="car__nav" data-dir="1" aria-label="{"次へ" if ja else "下一張"}">›</button></div>
</section>
<a class="ribbon" href="{url("news", lang)}">
  <span class="ribbon__tag">{e(t(first["tag"], lang))}</span><time>{first["date"]}</time>
  <span class="ribbon__t">{e(t(first["title"], lang))}</span><i aria-hidden="true">›</i>
</a>

<section class="sec">
  {sh("ピックアップ" if ja else "注目焦點", "Pick Up")}
  <ul class="pick">{pick}</ul>
</section>

<section class="sec">
  {sh("商品紹介" if ja else "商品介紹", "Products", url("products", lang), "すべての商品" if ja else "商品總覽")}
  {catcards(lang, catalog(lang))}
</section>

<section class="sec">
  {sh("お知らせ" if ja else "最新消息", "News", url("news", lang), "一覧を見る" if ja else "看全部消息")}
  {news_list(lang, 3)}
</section>

<section class="gift">
  <div class="gift__in">
    <div class="gift__head">
      <p class="gift__en">Online Shop</p>
      <h2 class="gift__t">{"冷凍スープカレー" if ja else "冷凍湯咖哩調理包"}</h2>
      <p>{"お店と同じスープを、冷凍でご家庭へ。" if ja else "與門市相同的湯底，冷凍宅配到家。"}</p>
      {btn(url("shop", lang), "商品一覧" if ja else "前往線上商店", "navy")}
    </div>
    <ul class="tiles tiles--3 tiles--packs">{packs}</ul>
  </div>
</section>

<section class="store">
  <figure class="store__img"><img src="img/restaurant-table.jpg" alt="{"店内でのお食事" if ja else "門市用餐"}" loading="lazy" width="1100" height="1466"></figure>
  <div class="store__card">
    {sh("店舗情報" if ja else "門市資訊", "Store", url("store", lang), "詳しく" if ja else "門市一覽")}
    <p class="store__name">{e(C.STORE["name_ja"] if ja else C.STORE["name_zh"])}</p>
    {store_dl(lang)}
    <div class="actions">{btn(C.STORE["map_url"], "Googleマップ" if ja else "Google 地圖導航", "navy", ext=True)}{btn(url("store", lang) + "#popup", "催事への出店" if ja else "百貨催事出店", "line")}</div>
  </div>
</section>'''
    desc = ("札幌湯匠は台中・大里のスープカレー専門店。ダブル高湯、23種のスパイス、72時間熟成。冷凍スープカレーの通販も。" if ja
            else "札幌湯匠是台中大里的北海道湯咖哩專門店。雙重高湯、23 種香料、72 小時熟成；門市用餐、外帶與冷凍湯咖哩宅配。")
    return body, desc, jsonld_restaurant()


# ───────── 品牌故事 ─────────
def story(lang):
    ja = lang == "ja"
    if ja:
        paras = ["札幌湯匠のはじまりは、札幌の路地裏にあった一軒のスープカレー店です。",
                 "にぎやかさはなく、温かな灯りとスープの香りだけ。人は腰を下ろすと自然にペースを落とし、静かに一杯を食べ終えていました。",
                 "記憶に残ったのは刺激ではなく、スープの層と温度、そしてゆっくり味わってはじめてわかる風味でした。",
                 "台湾に戻った私たちは、手間を惜しまないことを選びました。スープを時間をかけて煮込み、配合がなじむのを待つ。何度もやり直したのは、「ちょうどいい」に近づくためです。",
                 "心を込めて煮込んだスープは、心を込めて味わう価値がある。忙しい毎日のなかに、静かな時間を少しだけ。"]
    else:
        paras = ["札幌湯匠的起點，來自一間札幌巷弄裡的湯咖哩店。",
                 "沒有喧鬧，只有暖燈與湯的香氣。人坐下來，自然放慢節奏，安靜把一碗湯吃完。",
                 "記住的不是刺激，而是湯裡的層次、溫度，與需要慢慢品嚐才懂的風味。",
                 "回到台灣後，我們選擇費工，而不是省事。讓湯慢慢熬煮，讓香料與風味在時間裡自然融合。有些配方重來多次，只為接近「剛剛好」。",
                 "一碗用心熬出的湯，值得被專心品嚐。若你想在忙碌裡，留一段安靜給自己，這裡會是一個選擇。"]
    craft = "".join(f'<li><p class="craft__n"><b>{c["num"]}</b>{e(t(c["unit"], lang))}</p><h3>{e(t(c["title"], lang))}</h3><p>{e(t(c["body"], lang))}</p></li>' for c in CRAFT)
    commits = "".join(f'<li><span class="cm__n">{i + 1:02d}</span><h3>{e(t(c["title"], lang))}</h3><p>{e(t(c["body"], lang))}</p></li>'
                      for i, c in enumerate(COMMITMENTS))
    tabs = [("#story", "ブランドストーリー" if ja else "品牌故事"), ("#commitment", "こだわり" if ja else "湯匠的堅持"),
            ("#process", "スープができるまで" if ja else "湯咖哩的工序"), (url("company", lang), "会社概要" if ja else "公司資訊")]
    body = page_head("story", lang) + ctab(tabs, "ページ内" if ja else "頁內導覽") + f'''
<section class="tate-sec anchor" id="story">
  <div class="tate">{"".join(f"<p>{e(p)}</p>" for p in paras)}</div>
  <figure class="tate-sec__img"><img src="img/bowls-wood-light.jpg" alt="" loading="lazy" width="1100" height="1479">{seal("湯匠")}</figure>
</section>
<section class="quote">
  <figure class="quote__img">{STEAM}<img src="img/steam-bowl.jpg" alt="{"湯気の立つスープカレー" if ja else "冒著熱氣的湯咖哩"}" loading="lazy" width="1024" height="1536"></figure>
  <div class="quote__txt">
    <p class="quote__v split">{"湯気が立ちのぼると、<br>まわりの音は遠くなる。<br>目の前の一杯だけが、<br>そこに残る。" if ja else "熱氣升起的那一刻，<br>外界的聲音，<br>退成遠遠的白噪音。<br>只剩下眼前這一碗。"}</p>
    <p class="quote__by">{"札幌湯匠　ブランドストーリーより" if ja else "摘自　札幌湯匠品牌故事"}</p>
  </div>
</section>
<section class="mission anchor" id="commitment">
  <div class="mission__in">
    {sh("一杯を、時間と技術に見合うものに" if ja else "把一碗湯咖哩，做到對得起時間與專業", "Our Mission", light=True)}
    <ol class="cm">{commits}</ol>
  </div>
</section>
<section class="sec anchor" id="process">
  {sh("スープができるまで" if ja else "湯咖哩的工序", "The Process")}
  <ul class="craft">{craft}</ul>
  {time_ruler(lang)}
</section>
<section class="sec">
  <a class="band" href="{url("company", lang)}"><span class="band__en">Company</span><b>{"会社概要" if ja else "公司資訊"}</b><span>{e(C.COMPANY["name"])}</span><i aria-hidden="true">›</i></a>
</section>'''
    return body, ("札幌湯匠のブランドストーリー。" if ja else "札幌湯匠的品牌故事、使命與湯咖哩製作工序。"), ""


# ───────── 菜單 ─────────
def menu(lang):
    ja = lang == "ja"
    steps = [(L("選擇湯咖哩", "スープカレーを選ぶ"), L("八款主菜，每碗附十種蔬菜。", "8種のメイン。どれも野菜10種入り。")),
             (L("選擇辣度", "辛さを選ぶ"), L("甘口・辛口・超辛", "甘口・辛口・激辛")),
             (L("選擇飯量", "ライスの量"), L("藜麥越光米飯　小 150g／普通 200g／大 300g（+NT$30）", "キヌア入りコシヒカリ　小150g／普通200g／大盛300g（+NT$30）")),
             (L("加點配料", "トッピング"), L("炙燒起司 +NT$30、德式香腸 +NT$50 等", "炙りチーズ +NT$30、ソーセージ +NT$50 など"))]
    st = "".join(f'<li><span class="step__n">{i + 1}</span><h3>{e(t(a, lang))}</h3><p>{e(t(b, lang))}</p></li>' for i, (a, b) in enumerate(steps))
    aged = "".join(f'<tr><th><b>{e(t(d["name"], lang))}</b><span>{e(t(d["desc"], lang))}</span></th><td>{price(C.MENU_PRICES.get(d["id"]), lang)}</td></tr>' for d in AGED_CURRY)
    tabs = [("#soup", "スープカレー" if ja else "湯咖哩"), ("#order", "ご注文方法" if ja else "點餐方式"), ("#aged", "熟成カレー" if ja else "熟成咖哩"),
            ("#togo", "お持ち帰り" if ja else "外帶"), ("#bento", "催事弁当" if ja else "催事弁當"), ("#frozen", "冷凍" if ja else "冷凍調理包")]
    packs = "".join(pack_tile(p, lang) for p in FROZEN)
    body = page_head("menu", lang, "スープカレー、熟成カレー、お持ち帰り、催事のお弁当、冷凍スープカレーのご案内です。" if ja else "湯咖哩、熟成咖哩、外帶、百貨催事弁當與冷凍調理包，一次看完。") + ctab(tabs, "カテゴリー" if ja else "菜單分類") + f'''
<section class="sec anchor" id="soup">
  {sh("スープカレー" if ja else "湯咖哩", "Soup Curry")}
  <p class="veg"><span>{"共通の野菜" if ja else "每碗共通蔬菜"}</span>{e(t(VEG, lang))}</p>
  <ul class="tiles tiles--4">{"".join(tile(d, lang) for d in SOUP_CURRY)}</ul>
</section>
<section class="sec sec--tint anchor" id="order">
  {sh("ご注文方法" if ja else "點餐方式", "How to Order")}
  <ol class="steps">{st}</ol>
</section>
<section class="sec anchor" id="aged">
  {sh("熟成カレー" if ja else "熟成咖哩", "Aged Curry")}
  <div class="aged">
    <figure><img src="img/aged-curry-cutlet.jpg" alt="" loading="lazy" width="1100" height="1466"></figure>
    <div>
      <p class="aged__lead">{"玄米油で100℃の低温炒め。インド・タイ・日本のスパイスを合わせ、24・48・72時間の三段階で熟成させたルー。" if ja else "玄米油 100°C 低溫拌炒，融合印度、泰國與日本的香料；咖哩醬經 24、48、72 小時三段熟成，濃稠醇厚。"}</p>
      <table class="mtbl">{aged}</table>
    </div>
  </div>
</section>
<section class="sec anchor" id="togo">
  {sh("お持ち帰り" if ja else "外帶", "Curry to Go")}
  <div class="togo togo--wide"><img src="img/takeout-box.jpg" alt="" loading="lazy" width="640" height="890">
  <div><p class="togo__t">{"全メニュー、お持ち帰りいただけます。" if ja else "全品項皆可外帶"}</p><p>{"スープ・ライス・具材を分けてお詰めします。お電話でご予約いただくと、お待たせせずにお渡しできます。" if ja else "外帶餐盒將湯、飯與配料分裝，帶回家仍保持口感。來電預訂，到店即可取餐。"}</p><p class="togo__tel">TEL {tel()}</p></div></div>
</section>
<section class="sec anchor" id="bento">
  {sh("催事限定　玉子焼き弁当" if ja else "百貨催事限定　玉子燒弁當", "Pop-up Bento", url("bento", lang), "詳しく" if ja else "看全部")}
  {bento_rail(lang)}
</section>
<section class="sec anchor" id="frozen">
  {sh("冷凍スープカレー" if ja else "冷凍湯咖哩調理包", "Ready-to-cook", url("shop", lang), "オンラインショップ" if ja else "線上商店")}
  <ul class="tiles tiles--3 tiles--packs">{packs}</ul>
</section>
<section class="sec">
  {notes(["価格はすべて税込です。", "写真はイメージです。", "野菜の内容は季節により変わることがあります。", "アレルギーをお持ちの方は、ご注文前にスタッフへお申し付けください。冷凍スープカレーの原材料は各商品ページに記載しています。"] if ja else
         ["價格皆含稅。", "圖片僅供參考。", "蔬菜依季節調整，以門市實際供應為準。", "對食材過敏者，請於點餐前洽詢店員；冷凍調理包成分與過敏原請見各商品頁。"])}
</section>'''
    return body, ("札幌湯匠のメニュー：スープカレー8種、熟成カレー、お持ち帰り、催事弁当、冷凍スープカレー。" if ja else "札幌湯匠菜單：八款湯咖哩、熟成咖哩、外帶、百貨催事弁當與冷凍調理包。"), ""


# ───────── 線上商店 ─────────
def nutrition(p):
    n = p["nut"]
    rows = "".join(f"<tr><th scope='row'>{e(a)}</th><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in n["rows"])
    return f'''<table class="nut">
  <caption>營養標示</caption>
  <thead><tr><td colspan="3">每一份量 {n["serving"]} 公克<br>本包裝含 1 份</td></tr>
  <tr><th scope="col"><span class="sr">項目</span></th><th scope="col">每份</th><th scope="col">每 100 公克</th></tr></thead>
  <tbody>{rows}</tbody></table>'''


def ship_note(lang):
    ja = lang == "ja"
    S = C.SHIPPING
    rows = []
    if S["fee"] is not None:
        fee = f"NT${S['fee']:,}" + (f"（{'NT$' + format(S['free_over'], ',')} {'以上で無料' if ja else '以上免運'}）" if S["free_over"] else "")
        rows.append(("送料" if ja else "運費", fee))
    else:
        rows.append(("送料" if ja else "運費", "ご注文確認時にご案内します" if ja else "訂單確認時通知"))
    if S["carrier"]: rows.append(("配送" if ja else "配送方式", S["carrier"]))
    if S["ship_days"]: rows.append(("発送" if ja else "出貨", S["ship_days"]))
    rows.append(("温度帯" if ja else "溫層", "冷凍（-18℃）"))
    rows.append(("お届け地域" if ja else "配送範圍", "台湾本島" if ja else "台灣本島"))
    return "".join(f"<tr><th>{e(a)}</th><td>{e(b)}</td></tr>" for a, b in rows)


def shop(lang):
    ja = lang == "ja"
    body = page_head("shop", lang, "お店と同じスープを、冷凍でご家庭へ。" if ja else "與門市相同的湯底，冷凍宅配到家。") + f'''
<section class="sec">
  {sh("冷凍スープカレー" if ja else "冷凍湯咖哩調理包", "Ready-to-cook")}
  <ul class="tiles tiles--3 tiles--packs tiles--shop">{"".join(pack_tile(p, lang, full=True) for p in FROZEN)}</ul>
</section>
<section class="sec sec--tint">
  {sh("配送・お支払い" if ja else "配送與付款", "Delivery & Payment")}
  <div class="two">
    <table class="tbl">{ship_note(lang)}</table>
    <table class="tbl"><tr><th>{"お支払い" if ja else "付款方式"}</th><td>{"ECPay（綠界）の決済ページにて。利用できる方法は決済画面に表示されます。" if ja else "綠界科技 ECPay 安全付款頁面（可用方式以付款頁面顯示為準）"}</td></tr>
    <tr><th>{"お電話" if ja else "電話訂購"}</th><td>{tel()}</td></tr><tr><th>{"返品" if ja else "退換貨"}</th><td><a class="u" href="{url("terms", lang)}">{e(t(PAGES["terms"]["t"], lang))}</a></td></tr></table>
  </div>
</section>'''
    return body, ("札幌湯匠の冷凍スープカレー通販：牛リブ、チキンレッグ、スープのみ。" if ja else "札幌湯匠線上商店：冷凍湯咖哩調理包（牛肋、雞腿、純湯咖哩）宅配到家。"), ""


def product(p):
    def build_one(lang):
        ja = lang == "ja"
        heat = "".join(f"<li>{e(h)}</li>" for h in t(HEAT, lang))
        others = "".join(pack_tile(o, lang) for o in FROZEN if o["id"] != p["id"])
        pr = C.FROZEN_PRICES[p["id"]]["price"]
        body = page_head("p-" + p["id"], lang) + f'''
<section class="sec">
  <article class="pd">
    <div class="pd__img"><img src="img/{p["img"]}" alt="{e(t(p["name"], lang))}" width="800" height="1092"></div>
    <div class="pd__body">
      <p class="tile__chips">{chip("要冷凍" if ja else "需冷凍", "navy")}{chip("-18℃")}{chip("非即食品" if ja else "非即食")}</p>
      <p class="pd__en">{e(p["en"])}</p>
      <h2 class="pd__t">{e(t(p["short"], lang))}</h2>
      <p class="pd__meta">{e(t(p["note"], lang))}</p>
      <p class="pd__price">{yen(pr, "税込" if ja else "含稅")}</p>
      <table class="tbl tbl--sm"><tr><th>{"内容量" if ja else "淨重"}</th><td>{e(t(p["net"], lang))}</td></tr><tr><th>{"保存" if ja else "保存"}</th><td>{e(t(p["storage"], lang))}</td></tr><tr><th>{"送料" if ja else "運費"}</th><td>{e(ship_note_short(lang))}</td></tr></table>
      {qty_form(p, lang)}
      <p class="pd__tel">{"お電話でのご注文" if ja else "電話訂購"}　{tel()}</p>
      <details class="pd__label" open>
        <summary>{"商品表示・栄養成分" if ja else "商品標示・營養標示"}</summary>
        <div class="pd__label-in">
          <table class="tbl tbl--sm">
            <tr><th>品名</th><td>{e(p["name"]["zh"])}</td></tr>
            <tr><th>成分</th><td>{e(p["ing"])}</td></tr>
            <tr><th>淨重</th><td>{e(p["net"]["zh"])}</td></tr>
            <tr><th>保存方式</th><td>{e(p["storage"]["zh"])}</td></tr>
            <tr><th>有效日期</th><td>{e(p["expiry"]["zh"])}</td></tr>
            <tr><th>原產地</th><td>{e(p["origin"]["zh"])}</td></tr>
            <tr><th>製造商</th><td>{e(p["maker"])}</td></tr>
            <tr><th>負責廠商</th><td>{e(p["responsible"])}<br>{e(C.STORE["address_zh"])}<br>{e(C.STORE["phone"])}</td></tr>
            <tr><th>過敏原</th><td>{e(p["allergen"]["zh"])}</td></tr>
            <tr><th>{"温め方" if ja else "食用方式"}</th><td><ul class="heat">{heat}</ul></td></tr>
          </table>
          {nutrition(p)}
        </div>
      </details>
    </div>
  </article>
  <p class="fine">{"非即食品です。十分に加熱してお召し上がりください。写真はイメージです。" if ja else "本產品非即食，請充分加熱後食用。圖片僅供參考，以實際商品為準。"}　<a class="u" href="{url("terms", lang)}">{e(t(PAGES["terms"]["t"], lang))}</a></p>
</section>
<section class="sec">
  {sh("ほかの商品" if ja else "其他商品", "More")}
  <ul class="tiles tiles--3 tiles--packs tiles--two">{others}</ul>
</section>'''
        ld = {"@context": "https://schema.org", "@type": "Product", "name": p["name"]["zh"], "image": "img/" + p["img"],
              "brand": {"@type": "Brand", "name": "札幌湯匠"},
              "offers": {"@type": "Offer", "priceCurrency": "TWD", "price": pr, "availability": "https://schema.org/InStock"}}
        return body, f'{t(p["name"], lang)}　NT${pr}（{"税込" if ja else "含稅"}）。{t(p["net"], lang)}。', jsonld(ld)
    return build_one


def ship_note_short(lang):
    S = C.SHIPPING
    ja = lang == "ja"
    if S["fee"] is None:
        return "ご注文確認時にご案内" if ja else "訂單確認時通知"
    s = f"NT${S['fee']:,}"
    if S["free_over"]:
        s += f"（NT${S['free_over']:,} {'以上で無料' if ja else '以上免運'}）"
    return s


# ───────── 購物車・結帳・完成 ─────────
def cart(lang):
    ja = lang == "ja"
    body = page_head("cart", lang) + f'''
<section class="sec">
  <ol class="flow"><li aria-current="step">{"カート" if ja else "購物車"}</li><li>{"お届け先" if ja else "填寫資料"}</li><li>{"お支払い" if ja else "付款"}</li><li>{"完了" if ja else "完成"}</li></ol>
  <div id="cart-root" class="cart"><noscript><p>{"カートのご利用には JavaScript が必要です。お電話でもご注文いただけます：" if ja else "購物車需要 JavaScript。也可以來電訂購："}{C.STORE["phone"]}</p></noscript></div>
</section>'''
    return body, "購物車", ""


CITIES = ['台北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '苗栗縣', '台中市', '彰化縣', '南投縣', '雲林縣',
          '嘉義市', '嘉義縣', '台南市', '高雄市', '屏東縣', '宜蘭縣', '花蓮縣', '台東縣']


def checkout(lang):
    ja = lang == "ja"
    ecpay = MODE == "ecpay"
    opts = "".join(f'<option>{c}</option>' for c in CITIES)
    times = "".join(f'<option>{e(x)}</option>' for x in C.SHIPPING["delivery_times"])
    action = 'action="api/checkout.php" method="post"' if ecpay else 'action="#" method="post"'
    paylink = (not ecpay) and C.ECPAY_PAYLINK
    if ecpay:
        note = ""
    elif paylink:
        note = f'<p class="note">{"送信後に注文番号が表示されます。送料と合計金額を確認後、ECPay（クレジットカード・ATM・コンビニ・Apple Pay）でお支払いいただけます。" if ja else "送出後會產生訂單編號。我們與您確認運費與總金額後，即可透過綠界線上付款（信用卡、ATM、超商代碼、Apple Pay）。"}</p>'
    else:
        note = f'<p class="note">{"現在オンライン決済は準備中です。送信後に注文内容と注文番号が表示されますので、お電話でご確認ください。" if ja else "線上付款開通中。送出後會產生訂單編號與訂單內容，請來電確認運費與付款方式，我們即為您出貨。"}</p>'
    pay_html = ""
    if paylink:
        pay_html = f'''<div class="co__pay">
      <p class="co__pay-h">{"お支払い（ECPay）" if ja else "線上付款（綠界 ECPay）"}</p>
      <ol class="co__pay-steps">
        <li>{"上記の注文内容をお電話または LINE でお知らせください。送料込みの合計金額をご案内します。" if ja else "請來電或傳 LINE 告知上方訂單內容，我們會回覆含運費的總金額。"}</li>
        <li>{"下のボタンから ECPay の決済ページへ進み、「金額」に合計金額、「備考」に注文番号を入力してください。" if ja else "點下方按鈕前往綠界付款頁，「金額」填總金額，「備註」填上方訂單編號。"}</li>
        <li>{"入金を確認後、発送いたします。" if ja else "確認入帳後，我們即為您出貨。"}</li>
      </ol>
      <a class="btn btn--navy co__pay-btn" href="{e(paylink)}" target="_blank" rel="noopener"><span>{"ECPay で支払う" if ja else "前往綠界付款"}</span><i aria-hidden="true">›</i></a>
      <p class="fine">{"決済は ECPay（綠界科技）のページで行われ、当店はカード情報をお預かりしません。" if ja else "付款於綠界科技頁面進行，本店不經手、不保存您的信用卡資料。"}</p>
    </div>'''

    submit = ("ECPay の決済ページへ" if ja else "前往綠界安全付款") if ecpay else ("注文内容を確定する" if ja else "產生訂單")
    body = page_head("checkout", lang) + f'''
<section class="sec">
  <ol class="flow"><li>{"カート" if ja else "購物車"}</li><li aria-current="step">{"お届け先" if ja else "填寫資料"}</li><li>{"お支払い" if ja else "付款"}</li><li>{"完了" if ja else "完成"}</li></ol>
  {note}
  <div class="co">
    <form id="co-form" class="co__form" {action} novalidate>
      <input type="hidden" name="items" id="co-items"><input type="hidden" name="lang" value="{lang}">
      <div class="hp" aria-hidden="true"><label>Website<input name="website" tabindex="-1" autocomplete="off"></label></div>
      <fieldset><legend>{"お届け先" if ja else "收件資料"}</legend>
        <label class="f"><span>{"お名前" if ja else "收件人姓名"}<em>*</em></span><input id="f-name" name="name" required maxlength="50" autocomplete="name"></label>
        <label class="f"><span>{"電話番号" if ja else "手機／電話"}<em>*</em></span><input id="f-phone" name="phone" required inputmode="tel" pattern="[0-9+\\- ]{{9,15}}" autocomplete="tel" placeholder="0912345678"></label>
        <label class="f"><span>Email<em>*</em></span><input id="f-email" name="email" type="email" required autocomplete="email"></label>
        <div class="f2">
          <label class="f"><span>{"県市" if ja else "縣市"}<em>*</em></span><select id="f-city" name="city" required><option value="">{"選択" if ja else "請選擇"}</option>{opts}</select></label>
          <label class="f"><span>{"住所" if ja else "地址"}<em>*</em></span><input id="f-address" name="address" required minlength="5" maxlength="200" autocomplete="street-address"></label>
        </div>
        <label class="f"><span>{"配達時間帯" if ja else "希望到貨時段"}</span><select id="f-time" name="delivery_time">{times}</select></label>
      </fieldset>
      <fieldset><legend>{"領収書" if ja else "發票"}</legend>
        <div class="radios"><label><input type="radio" name="invoice_type" value="personal" checked> {"個人" if ja else "個人"}</label><label><input type="radio" name="invoice_type" value="company"> {"法人（統一番号）" if ja else "公司（統一編號）"}</label></div>
        <div class="f2 co__company" hidden>
          <label class="f"><span>{"統一番号" if ja else "統一編號"}</span><input id="f-taxid" name="tax_id" inputmode="numeric" pattern="[0-9]{{8}}" maxlength="8"></label>
          <label class="f"><span>{"宛名" if ja else "發票抬頭"}</span><input id="f-title" name="invoice_title" maxlength="100"></label>
        </div>
      </fieldset>
      <fieldset><legend>{"備考" if ja else "備註"}</legend>
        <label class="f"><span class="sr">{"備考" if ja else "備註"}</span><textarea id="f-note" name="note" rows="3" maxlength="500" placeholder="{"ご要望があればご記入ください" if ja else "例如：送禮、指定到貨日"}"></textarea></label>
      </fieldset>
      <label class="agree"><input type="checkbox" id="f-agree" name="agree" value="1" required> <span>{"" if ja else "我已閱讀並同意"}<a class="u" href="{url("terms", lang)}" target="_blank">{e(t(PAGES["terms"]["t"], lang))}</a>{"・" if ja else "與"}<a class="u" href="{url("privacy", lang)}" target="_blank">{e(t(PAGES["privacy"]["t"], lang))}</a>{"に同意します" if ja else ""}</span></label>
      <p class="co__err" role="alert" hidden></p>
      <button type="submit" class="buy"><b>{e(submit)}</b><i aria-hidden="true">›</i></button>
      <p class="fine">{"冷凍食品のため、お客様都合による返品はお受けできません。" if ja else "冷凍食品不適用七日解除權，商品如有瑕疵請於收到後 24 小時內聯繫。"}</p>
    </form>
    <aside class="co__sum" id="co-summary" aria-live="polite"></aside>
  </div>
  <div class="co__done" id="co-done" hidden>
    <p class="co__done-k">{"注文番号" if ja else "訂單編號"}</p><p class="co__done-no" id="co-no"></p>
    <p>{"以下の内容をお電話（またはLINE）でお伝えください。送料とお支払い方法をご案内し、発送いたします。" if ja else "請來電（或傳 LINE）告知以下訂單內容，我們會確認運費與付款方式後為您出貨。"}</p>
    <p class="co__done-tel">TEL {tel()}</p>
    <textarea id="co-text" readonly rows="10" aria-label="{"注文内容" if ja else "訂單內容"}"></textarea>
    <div class="co__done-act"><button type="button" class="btn btn--navy" id="co-copy"><span>{"注文内容をコピー" if ja else "複製訂單內容"}</span><i aria-hidden="true">›</i></button>
    {btn(e(C.STORE["line_url"]), "LINE", "line", ext=True) if C.STORE["line_url"] else ""}</div>
    {pay_html}
  </div>
</section>'''
    return body, "結帳", ""


def complete(lang):
    ja = lang == "ja"
    body = page_head("complete", lang) + f'''
<section class="sec">
  <ol class="flow flow--done"><li>{"カート" if ja else "購物車"}</li><li>{"お届け先" if ja else "填寫資料"}</li><li>{"お支払い" if ja else "付款"}</li><li aria-current="step">{"完了" if ja else "完成"}</li></ol>
  <div class="done" id="done" data-paid="{"お支払いが完了しました。ご注文ありがとうございます。" if ja else "付款完成，感謝您的訂購。"}"
       data-await="{"お支払い情報を受け付けました。ECPay の案内に従い、期限内にお支払いください。入金確認後に発送します。" if ja else "已取得繳費資訊，請依綠界頁面的說明於期限內完成付款；確認入帳後即為您出貨。"}"
       data-failed="{"お支払いが完了しませんでした。カートから再度お手続きいただくか、お電話でご連絡ください。" if ja else "付款未完成。您可以返回購物車重新結帳，或來電由我們協助。"}">
    {seal("湯匠")}
    <p class="done__msg" id="done-msg">{"ご注文ありがとうございます。" if ja else "感謝您的訂購。"}</p>
    <p class="done__no" id="done-no" hidden></p>
    <p>{"ご不明な点は、注文番号を添えてお電話ください。" if ja else "如有任何問題，請來電並告知訂單編號。"}　TEL {tel()}</p>
    <div class="actions">{btn(url("shop", lang), "ショップへ戻る" if ja else "回到線上商店", "navy")}{btn(url("home", lang), "トップへ" if ja else "回到首頁", "line")}</div>
  </div>
</section>'''
    return body, "訂單完成", ""


# ───────── 消息・FAQ・門市・團體・法務・404 ─────────
def news(lang):
    ja = lang == "ja"
    tags = []
    for n in NEWS:
        if n["tag"]["zh"] not in [x["zh"] for x in tags]:
            tags.append(n["tag"])
    btns = f'<li><button type="button" aria-pressed="true" data-f="all">{"すべて" if ja else "全部"}<span>{len(NEWS)}</span></button></li>' + "".join(
        f'<li><button type="button" aria-pressed="false" data-f="c{i}">{e(t(g, lang))}<span>{sum(1 for n in NEWS if n["tag"]["zh"] == g["zh"])}</span></button></li>' for i, g in enumerate(tags))
    body = page_head("news", lang) + f'''<section class="sec">
  <ul class="nfil" role="group" aria-label="{"カテゴリー" if ja else "分類"}">{btns}</ul>
  {news_list(lang, cats=[x["zh"] for x in tags])}
</section>'''
    return body, ("札幌湯匠のお知らせ。" if ja else "札幌湯匠最新消息、百貨活動與媒體報導。"), ""


def faq(lang):
    ja = lang == "ja"
    blocks = ""
    q_ld = []
    for cat, qs in FAQ:
        items = "".join(f'<details class="qa"><summary><span class="qa__q">Q</span>{e(t(q, lang))}</summary><p><span class="qa__a">A</span>{e(t(a, lang))}</p></details>' for q, a in qs)
        blocks += f'<div class="faq__cat">{sh(e(t(cat, lang)), "Q & A", tag="h2")}{items}</div>'
        q_ld += [{"@type": "Question", "name": t(q, lang), "acceptedAnswer": {"@type": "Answer", "text": t(a, lang)}} for q, a in qs]
    body = page_head("faq", lang) + f'''<section class="sec"><div class="faq">{blocks}</div>
  <p class="fine">{"そのほかのご質問はお電話でどうぞ。" if ja else "其他問題，歡迎來電詢問。"}　TEL {tel()}</p></section>'''
    return body, ("札幌湯匠のよくあるご質問。" if ja else "札幌湯匠常見問題：外帶、辣度、停車、冷凍調理包加熱與保存、付款與退換貨。"), jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": q_ld})


def store(lang):
    ja = lang == "ja"
    S = C.STORE
    svc = [("內用" if not ja else "店内飲食", True), ("外帶" if not ja else "お持ち帰り", True), ("電話預訂外帶" if not ja else "電話で予約", True)]
    svc_html = "".join(f'<li>{e(x)}</li>' for x, ok in svc if ok)
    body = page_head("store", lang, "店舗の所在地・営業時間・アクセスのご案内です。" if ja else "門市地址、營業時間、交通與停車資訊。") + f'''
<section class="sec">
  {sh("店舗一覧" if ja else "門市一覽", "Store List")}
  <p class="area"><b>{"台中市" if ja else "台中市"}</b><span>{"1店舗" if ja else "共 1 間"}</span></p>
  <article class="shopcard anchor" id="dali">
    <figure class="shopcard__img"><img src="img/set-tray.jpg" alt="" loading="lazy" width="1080" height="790"></figure>
    <div class="shopcard__body">
      <h3 class="shopcard__name">{e(S["name_ja"] if ja else S["name_zh"])}</h3>
      <ul class="svc">{svc_html}</ul>
      {store_dl(lang)}
      <div class="actions">{btn(S["map_url"], "Googleマップ" if ja else "Google 地圖導航", "navy", ext=True)}{btn(url("menu", lang), "メニュー" if ja else "菜單介紹", "line")}</div>
    </div>
  </article>
</section>
<section class="sec anchor" id="popup">
  {sh("百貨店の催事" if ja else "百貨催事出店", "Pop-up Events", url("news", lang), "お知らせ" if ja else "最新消息")}
  <div class="evt">
    <img src="img/booth-noren.jpg" alt="" loading="lazy" width="1600" height="1200">
    <div class="evt__txt"><p>{"百貨店の日本物産展や期間限定イベントにも出店しています。会場でスープを仕込み、冷凍スープカレーと玉子焼き弁当をご用意します。会期は「お知らせ」でご案内します。" if ja else "我們也參加百貨公司日本展與期間限定活動，在現場熬湯，也帶上冷凍調理包與玉子燒弁當。檔期會在最新消息公告。"}</p>
    {btn(url("bento", lang), "催事のお弁当" if ja else "催事弁當", "line")}</div>
    <img class="evt__sub" src="img/event-booth-2.jpg" alt="" loading="lazy" width="1400" height="788">
  </div>
</section>'''
    return body, ("札幌湯匠 台中大里店の住所・電話・アクセス。" if ja else "札幌湯匠台中大里店：地址、電話、停車資訊、外帶與 Google 地圖導航；百貨催事出店資訊。"), jsonld_restaurant()


def company(lang):
    ja = lang == "ja"
    CO, S = C.COMPANY, C.STORE
    rows = [("会社名" if ja else "公司名稱", e(CO["name"])),
            ("ブランド" if ja else "品牌", "札幌湯匠　SAPPORO SOUP CURRY"),
            ("事業内容" if ja else "營業項目", "北海道スープカレー専門店の運営<br>冷凍スープカレーの製造・販売<br>百貨店催事への出店" if ja
             else "北海道湯咖哩專門店經營<br>冷凍湯咖哩調理包販售<br>百貨公司催事出店"),
            ("店舗" if ja else "門市", f'{e(S["name_ja"] if ja else S["name_zh"])}<br>{e(S["address_ja"] if ja else S["address_zh"])}'),
            ("電話" if ja else "聯絡電話", tel())]
    if CO["tax_id"]:
        rows.append(("統一番号" if ja else "統一編號", e(CO["tax_id"])))
    if CO["food_license"]:
        rows.append(("食品業者登録番号" if ja else "食品業者登錄字號", e(CO["food_license"])))
    tr_ = "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in rows)
    body = page_head("company", lang) + f'''
<section class="sec">
  {sh("会社概要" if ja else "公司資訊", "Company Profile")}
  <table class="tbl tbl--co">{tr_}</table>
</section>'''
    return body, ("札幌湯匠の会社概要。" if ja else "札幌湯匠餐飲有限公司公司資訊。"), ""


def sitemap(lang):
    ja = lang == "ja"
    blocks = []
    for s_, kids in tree(lang):
        if s_ == "home":
            continue
        li = "".join(f'<li><a href="{h}">{e(t(lb, lang))}</a></li>' for h, lb, _ in kids)
        blocks.append(f'<div class="smap__b"><h2><a href="{url(s_, lang)}">{e(t(PAGES[s_]["t"], lang))}</a></h2>{f"<ul>{li}</ul>" if li else ""}</div>')
    extra = "".join(f'<li><a href="{url(x, lang)}">{e(t(PAGES[x]["t"], lang))}</a></li>' for x in ["faq", "privacy"])
    blocks.append(f'<div class="smap__b"><h2>{"その他" if ja else "其他"}</h2><ul>{extra}</ul></div>')
    body = page_head("sitemap", lang) + f'<section class="sec"><div class="smap"><div class="smap__b"><h2><a href="{url("home", lang)}">{e(t(PAGES["home"]["t"], lang))}</a></h2></div>{"".join(blocks)}</div></section>'
    return body, ("札幌湯匠公式サイトのサイトマップ。" if ja else "札幌湯匠官方網站網站地圖。"), ""


def bento(lang):
    ja = lang == "ja"
    lo = min(b["price"] for b in BENTO)
    cards = "".join(bento_card(b, lang).replace('<li class="bt">', f'<li class="bt" id="bento-{b["id"]}">', 1) for b in BENTO)
    lead = ("百貨店の日本物産展など、催事会場でご用意しているお弁当です。" if ja
            else "在百貨公司日本展等催事會場供應的弁當與商品。")
    body = page_head("bento", lang, lead) + f'''
<section class="popup">
  <figure class="popup__img"><img src="img/booth-noren.jpg" alt="{"湯咖哩ののれんを掲げた催事ブース" if ja else "掛著湯咖哩布簾的催事攤位"}" width="1600" height="1200" fetchpriority="high"></figure>
  <div class="popup__txt">
    <p class="popup__k">DEPARTMENT STORE POP-UP</p>
    <p class="popup__v split">{"会場で人気、<br>毎日つくりたて。" if ja else "現場熱賣<br>× 每日現煮"}</p>
    <p>{"札幌湯匠は百貨店の日本物産展や期間限定イベントに出店しています。会場ではスープを仕込み、冷凍スープカレーもご用意。どのお弁当にも、職人が手焼きした玉子焼きを詰めています。" if ja else "札幌湯匠參加百貨公司日本展與期間限定活動，會場現場熬湯，也帶上冷凍湯咖哩調理包。每一盒弁當，都放上職人手作的玉子燒。"}</p>
    <ul class="facts facts--ink"><li><b data-to="{len(BENTO)}">{len(BENTO)}</b>{"種のお弁当" if ja else "款弁當"}</li><li><b data-to="{lo}">{lo}</b>{"元から" if ja else "元起"}</li></ul>
  </div>
</section>

<section class="sec">
  {sh("玉子焼き弁当" if ja else "玉子燒弁當", "Tamagoyaki Bento")}
  <p class="bento__tag">{e(t(BENTO_TAG, lang))}</p>
  <ul class="bento">{cards}</ul>
</section>

<section class="sec">
  {sh("会場ではこちらも" if ja else "會場也有", "Also at the Booth")}
  <div class="also">
    <div class="also__item">
      <p class="also__k">{"単品" if ja else "單點"}</p>
      <h3 class="also__t">{"厚焼き玉子" if ja else "厚燒玉子"}</h3>
      <dl class="also__dl"><div><dt>{"プレーン" if ja else "原味"}</dt><dd>{yen(280)}</dd></div><div><dt>{"明太子" if ja else "明太子"}</dt><dd>{yen(330)}</dd></div></dl>
      <p class="fine">{"ほかの味は会場によって異なります。" if ja else "其他口味依各檔期現場供應。"}</p>
    </div>
    <div class="also__item also__item--navy">
      <p class="also__k">{"冷凍" if ja else "冷凍"}</p>
      <h3 class="also__t">{"冷凍スープカレー" if ja else "冷凍湯咖哩調理包"}</h3>
      <p>{"お店と同じスープを冷凍で。会場でもオンラインショップでもお求めいただけます。" if ja else "與門市相同的湯底。會場可現場購買，也能在線上商店訂購宅配。"}</p>
      {btn(url("shop", lang), "オンラインショップ" if ja else "前往線上商店", "white")}
    </div>
  </div>
</section>

<section class="sec">
  {sh("会場の様子" if ja else "會場一景", "At the Booth")}
  <div class="gal">
    <figure><img src="img/bento-table.jpg" alt="{"会場に並ぶ玉子焼き弁当" if ja else "會場陳列的玉子燒弁當"}" loading="lazy" width="1400" height="1050"></figure>
    <figure><img src="img/bento-table-2.jpg" alt="{"鰻、豚、しらすの弁当" if ja else "鰻魚、豚肉與吻仔魚弁當"}" loading="lazy" width="1400" height="1050"></figure>
  </div>
</section>

<section class="sec">
  <div class="popinfo">
    {seal("催事")}
    <div>
      <p class="popinfo__t">{"ご案内" if ja else "購買須知"}</p>
      <ul class="list">
        <li>{"お弁当は催事会場でご用意しています。会期と会場は「お知らせ」でご案内します。" if ja else "弁當於百貨催事會場供應，檔期與地點會在最新消息公告。"}</li>
        <li>{"内容と価格は会期によって異なる場合があります。会場の表示をご確認ください。" if ja else "各檔期供應品項與價格可能不同，以會場現場標示為準。"}</li>
        <li>{"店舗での販売やまとまったご注文は、お電話でお問い合わせください。" if ja else "門市是否供應、或需要大量訂購，請來電洽詢。"}</li>
      </ul>
      <p class="popinfo__tel">TEL {tel()}</p>
      <div class="actions">{btn(url("news", lang), "お知らせ" if ja else "查看最新檔期", "navy")}{btn(url("catering", lang), "団体のご注文" if ja else "團體訂餐", "line")}</div>
    </div>
  </div>
</section>'''
    ld = {"@context": "https://schema.org", "@type": "Menu", "name": "札幌湯匠 玉子燒弁當",
          "hasMenuSection": {"@type": "MenuSection", "name": "玉子燒弁當", "hasMenuItem": [
              {"@type": "MenuItem", "name": b["name"]["zh"], "description": b["desc"]["zh"],
               "offers": {"@type": "Offer", "price": b["price"], "priceCurrency": "TWD"}} for b in BENTO]}}
    desc = ("札幌湯匠の催事限定・玉子焼き弁当6種（NT$180から）。百貨店の日本物産展に出店しています。" if ja
            else f"札幌湯匠百貨催事限定玉子燒弁當六款，NT${lo} 起：蔥鹽豚五花、豚叉燒、雙色鮪魚吻仔魚、鮭魚吻仔魚、牛腹肉、鰻魚。")
    return body, desc, jsonld(ld)


def catering(lang):
    ja = lang == "ja"
    items = [L("會議與教育訓練餐盒", "会議・研修のお弁当"), L("公司活動、聚餐", "社内イベント・懇親会"),
             L("冷凍調理包大量訂購（禮盒、員工福利）", "冷凍スープカレーの大口注文")]
    need = [L("日期與時間", "日時"), L("數量", "数量"), L("取餐或配送地址", "受取／お届け先"),
            L("特殊需求（素食、過敏、分裝）", "ご要望（ベジ・アレルギー・個包装）"), L("是否需要統一編號", "統一番号の要否")]
    li = lambda xs: "".join(f"<li>{e(t(x, lang))}</li>" for x in xs)
    body = page_head("catering", lang, "スープ・ライス・具材を分けてお詰めします。" if ja else "外帶餐盒將湯、飯與配料分裝，送到現場仍保持口感。") + f'''
<section class="sec">
  <div class="cat">
    <div>{sh("こんな時に" if ja else "適合的場合", "Occasions")}<ul class="list">{li(items)}</ul></div>
    <div>{sh("お問い合わせ時に" if ja else "洽詢時請提供", "Details")}<ul class="list">{li(need)}</ul></div>
    <div class="cat__call">{seal("湯匠")}<p class="cat__k">{"ご相談・お見積もり" if ja else "洽詢與報價"}</p><p class="cat__tel">{tel()}</p>
    <p>{"数量・日時に応じてお見積もりいたします。" if ja else "依數量與日期提供報價。"}</p>
    {btn(e(C.STORE["line_url"]), "LINE", "white", ext=True) if C.STORE["line_url"] else ""}</div>
  </div>
</section>'''
    return body, ("札幌湯匠の団体・法人向けご注文。" if ja else "札幌湯匠團體訂餐與企業訂購：會議餐盒、活動聚餐、冷凍調理包大量訂購。"), ""


def JA_NOTE(lang):
    return '<p class="note">このページは繁体字中国語のみのご案内です。</p>' if lang == "ja" else ""


def legal_page(slug, lang, secs, desc, updated=False):
    body = page_head(slug, lang) + '<section class="sec"><div class="legal">' + JA_NOTE(lang) + "".join(
        f'<h2>{e(h)}</h2>' + "".join(f"<p>{e(p)}</p>" for p in ps) for h, ps in secs) + \
        (f'<p class="fine">最後更新：{datetime.date.today():%Y-%m-%d}</p>' if updated else "") + "</div></section>"
    return body, desc, ""


def terms(lang):
    S = C.SHIPPING
    secs = [
        ("訂購與付款", ["冷凍調理包可透過本網站線上訂購或電話訂購。線上付款由綠界科技（ECPay）處理，本網站不經手、不保存您的信用卡資料；可使用的付款方式以綠界付款頁面顯示為準。",
                    "訂單成立以付款完成為準；ATM 或超商代碼繳費者，以綠界確認入帳為準。電話訂購之付款方式將由門市人員說明。"]),
        ("配送", [x for x in [
            "本產品以冷凍方式配送，以維持 -18℃ 保存條件。配送範圍為台灣本島。",
            f"配送方式：{S['carrier']}" if S["carrier"] else None,
            f"運費：{ship_note_short('zh')}",
            f"出貨時間：{S['ship_days']}" if S["ship_days"] else None,
            "收到商品後請立即放入冷凍庫保存。"] if x]),
        ("發票", ["本公司依法開立發票。需要統一編號者，請於結帳時填寫統一編號與抬頭。"]),
        ("退換貨", ["本產品為冷凍食品，屬《通訊交易解除權合理例外情事適用準則》所定「易於腐敗、保存期限較短」之商品，不適用七日解除權。",
                  "若商品於運送過程中有破損、退冰或與訂購內容不符，請於收到商品後 24 小時內拍照並來電聯繫，我們將為您處理補寄或退款。"]),
        ("食用提醒", ["本產品非即食，請充分加熱後食用。開封後請盡快食用完畢，請勿重複冷凍。", "成分與過敏原資訊請見各商品頁。"]),
        ("聯絡我們", [f"{C.COMPANY['name']}　{C.STORE['address_zh']}　電話 {C.STORE['phone']}"]),
    ]
    return legal_page("terms", lang, secs, "札幌湯匠線上商店購物須知：付款、冷凍配送、發票、退換貨。")


def privacy(lang):
    secs = [
        ("適用範圍", ["本政策說明札幌湯匠（以下稱本公司）官方網站如何蒐集、處理及利用您的個人資料。"]),
        ("蒐集的資料", ["線上訂購時，我們會蒐集收件人姓名、電話、Email、地址、希望到貨時段、發票資訊與備註，用於處理訂單。",
                     "付款資料（如信用卡號）由綠界科技（ECPay）依其隱私權政策蒐集與處理，本公司不經手、不保存。",
                     "購物車內容僅儲存在您的瀏覽器中，用於結帳。"]),
        ("利用目的與期間", ["上述資料僅用於訂單處理、出貨、開立發票、售後服務與必要之聯繫，並依法令規定之期間保存。本公司不會將您的資料出售，或提供給與訂單無關的第三方；物流業者僅取得配送所需資料。"]),
        ("資料安全", ["訂單資料存放於受存取控管的伺服器，僅授權人員可透過後台查看。"]),
        ("Cookie 與網站分析", ["本網站可能使用 Google Analytics 了解網站瀏覽情形，相關資料以匿名方式統計。您可透過瀏覽器設定拒絕 Cookie。"]),
        ("您的權利", ["依《個人資料保護法》第 3 條，您可請求查詢、閱覽、製給複製本、補充或更正、停止蒐集處理利用或刪除您的個人資料。請來電與我們聯繫。"]),
        ("聯絡方式", [f"{C.COMPANY['name']}　{C.STORE['address_zh']}　電話 {C.STORE['phone']}"]),
    ]
    return legal_page("privacy", lang, secs, "札幌湯匠官方網站隱私權政策。", updated=True)


def notfound(lang):
    ja = lang == "ja"
    body = page_head("404", lang) + f'''<section class="sec"><div class="done">{seal("湯匠")}
  <p class="done__msg">{"お探しのページは見つかりませんでした。" if ja else "您要找的頁面不存在，可能已移動或刪除。"}</p>
  <div class="actions">{btn(url("home", lang), "トップへ" if ja else "回到首頁", "navy")}{btn(url("menu", lang), "お品書き" if ja else "看菜單", "line")}{btn(url("shop", lang), "ショップ" if ja else "線上商店", "line")}</div></div></section>'''
    return body, "404", ""


BUILDERS = dict(home=home, products=products, story=story, company=company, sitemap=sitemap, menu=menu, bento=bento, shop=shop, store=store, catering=catering, news=news, faq=faq,
                cart=cart, checkout=checkout, complete=complete, terms=terms, privacy=privacy)
BUILDERS["404"] = notfound
for _p in FROZEN:
    BUILDERS["p-" + _p["id"]] = product(_p)


def build():
    global MODE, ARTIFACT
    # dist＝Cloudways（PHP 後端）；dist-artifact＝claude.ai；dist-pages＝GitHub Pages（純靜態，結帳改電話／LINE 確認）
    for out, artifact, kind in (("dist", False, "cloudways"), ("dist-artifact", True, "artifact"), ("dist-pages", False, "pages")):
        ARTIFACT = artifact
        MODE = "ecpay" if (kind == "cloudways" and C.CHECKOUT_MODE == "ecpay" and C.SHIPPING["fee"] is not None) else "contact"
        d = os.path.join(ROOT, out)
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "src", "img"), os.path.join(d, "img"))
        for slug, fn in BUILDERS.items():
            for lang in ("zh", "ja"):
                body, desc, extra = fn(lang)
                with open(os.path.join(d, url(slug, lang)), "w", encoding="utf-8") as f:
                    f.write(page(slug, lang, body, desc, extra))
        if kind == "pages":
            with open(os.path.join(d, ".nojekyll"), "w") as f:
                f.write("")
            if C.PAGES_DOMAIN:
                with open(os.path.join(d, "CNAME"), "w") as f:
                    f.write(C.PAGES_DOMAIN.strip() + "\n")
            with open(os.path.join(d, "robots.txt"), "w") as f:
                f.write("User-agent: *\nAllow: /\n" + (f"Sitemap: {C.SITE_URL.rstrip('/')}/sitemap.xml\n" if C.SITE_URL else ""))
            if C.SITE_URL:
                base = C.SITE_URL.rstrip("/")
                urls = "".join(f"<url><loc>{base}/{url(s, l)}</loc></url>" for s in BUILDERS if s not in NOINDEX for l in ("zh", "ja"))
                with open(os.path.join(d, "sitemap.xml"), "w") as f:
                    f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
        if kind == "cloudways":
            # 後端（Cloudways）：api/、admin/ 與伺服器端價格表
            shutil.copytree(os.path.join(ROOT, "backend", "api"), os.path.join(d, "api"))
            shutil.copytree(os.path.join(ROOT, "backend", "admin"), os.path.join(d, "admin"))
            shop_json = dict(products=[dict(id=p["id"], name_zh=p["short"]["zh"], price=C.FROZEN_PRICES[p["id"]]["price"],
                                            max_qty=C.FROZEN_PRICES[p["id"]]["max_qty"]) for p in FROZEN],
                             shipping_fee=C.SHIPPING["fee"], free_shipping_over=C.SHIPPING["free_over"])
            with open(os.path.join(d, "api", "shop.json"), "w", encoding="utf-8") as f:
                json.dump(shop_json, f, ensure_ascii=False, indent=1)
            with open(os.path.join(d, "robots.txt"), "w") as f:
                f.write("User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\n" + (f"Sitemap: {C.SITE_URL.rstrip('/')}/sitemap.xml\n" if C.SITE_URL else ""))
            if C.SITE_URL:
                base = C.SITE_URL.rstrip("/")
                urls = "".join(f"<url><loc>{base}/{url(s, l)}</loc></url>" for s in BUILDERS if s not in NOINDEX for l in ("zh", "ja"))
                with open(os.path.join(d, "sitemap.xml"), "w") as f:
                    f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
            with open(os.path.join(d, ".htaccess"), "w") as f:
                f.write("# Cloudways (Apache)\nRewriteEngine On\nRewriteCond %{HTTPS} !=on\nRewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]\n"
                        "ErrorDocument 404 /404.html\n"
                        "<IfModule mod_expires.c>\nExpiresActive On\nExpiresByType image/jpeg \"access plus 30 days\"\nExpiresByType image/webp \"access plus 30 days\"\nExpiresByType image/png \"access plus 30 days\"\n</IfModule>\n"
                        "Header always set X-Content-Type-Options \"nosniff\"\nHeader always set Referrer-Policy \"strict-origin-when-cross-origin\"\nHeader always set X-Frame-Options \"SAMEORIGIN\"\n")
        print(f"✓ {out} ({MODE}): {len([x for x in os.listdir(d) if x.endswith('.html')])} pages")


if __name__ == "__main__":
    build()
