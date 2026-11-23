# -*- coding: utf-8 -*-
"""
札幌湯匠 網站設定檔 —— 日常更新只需要改這個檔案，然後執行：  python3 build.py

所有值為 None 的欄位：網站上不會顯示（或改顯示替代說明），不會出現假資料。
"""

SITE_URL = "https://www.yushosoupcurry.com"                       # 正式網址（例："https://www.example.com"）；用於 canonical / sitemap
PAGES_DOMAIN = "www.yushosoupcurry.com"                   # GitHub Pages 自訂網域（例："www.example.com"）；設定後會產生 CNAME 檔

# ───────── 公司與門市（來源：顧客手冊、品牌手冊） ─────────
COMPANY = {
    "name": "札幌湯匠餐飲有限公司",
    "tax_id": None,                 # 統一編號
    "food_license": None,           # 食品業者登錄字號（網路販售食品依法須標示）
}

STORE = {
    "name_zh": "札幌湯匠 台中大里店",
    "name_ja": "札幌湯匠 台中大里店",
    "address_zh": "台中市大里區德芳路二段105號1樓",
    "address_ja": "台中市大里区徳芳路二段105号1階",
    "postal": "412",
    "phone": "04-2406-6728",
    "phone_intl": "+886-4-2406-6728",
    "hours": None,                  # 例："11:00–14:30、17:00–20:30（週一公休）"
    "line_url": None,               # 例："https://lin.ee/xxxx"
    "instagram": None,
    "facebook": None,
    "parking_zh": "開車可停國光花市停車場",
    "parking_ja": "お車は國光花市の駐車場をご利用いただけます",
    "map_url": "https://www.google.com/maps/search/?api=1&query=%E5%8F%B0%E4%B8%AD%E5%B8%82%E5%A4%A7%E9%87%8C%E5%8D%80%E5%BE%B7%E8%8A%B3%E8%B7%AF%E4%BA%8C%E6%AE%B5105%E8%99%9F",
}

# ───────── 冷凍調理包 線上商店 ─────────
# 價格（含稅）。max_qty = 單筆訂單每款上限。
FROZEN_PRICES = {
    "beef-rib":    {"price": 339, "max_qty": 20},
    "chicken-leg": {"price": 309, "max_qty": 20},
    "soup":        {"price": 199, "max_qty": 20},
}

SHIPPING = {
    "fee": None,                    # 冷凍運費（整數），例：180。None = 尚未設定 → 線上付款停用，改為電話確認
    "free_over": None,              # 滿額免運門檻（整數），例：1500；不需要就保持 None
    "carrier": None,                # 例："黑貓宅急便 冷凍配送"
    "ship_days": None,              # 例："付款後 3 個工作天內出貨"
    "delivery_times": ["不指定", "上午（13 時前）", "下午（14–18 時）"],
}

# 結帳方式：
#   "ecpay"   → 上傳到 Cloudways 後使用：購物車送到 api/checkout.php，轉綠界付款（需設定 private_html/yusho-config.php）
#   "contact" → 無後端時（claude.ai）：顧客填寫資料後取得訂單內容，再以電話／LINE 確認
CHECKOUT_MODE = "ecpay"
# 綠界「收款連結」（金額由消費者填寫，備註欄填訂單編號）：網站放 GitHub Pages、沒有後端時使用
ECPAY_PAYLINK = "https://p.ecpay.com.tw/7EFFF16"

# ───────── 門市菜單價格（來源：門市菜單看板；None = 顯示「依門市公告」） ─────────
MENU_PRICES = {
    "beef-rib": None,
    "karaage": 399,
    "pork-cutlet": 439,
    "chicken-leg": 390,
    "wagyu-hamburg": 439,
    "ayu": None,
    "chicken-cutlet": 390,
    "vegetable": 350,
    "aged-pork": None,
    "aged-beef": None,
    "aged-ebi": None,
}

GA_ID = None                        # Google Analytics 4，例："G-XXXXXXX"
