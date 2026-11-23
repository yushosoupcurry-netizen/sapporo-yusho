# 札幌湯匠 官方網站＋線上商店

## 網站內容

網站架構與商品分類比照富帆商店官網：主選單「首頁／最新消息／商品介紹／門市資訊／購物須知／關於湯匠／團體訂購」，商品可用多種分類交叉查找。

| 主選單 | 內容 |
|---|---|
| 商品介紹 | `products.html`：品項分類卡（湯咖哩／熟成咖哩／玉子燒弁當／冷凍調理包）→ 分類索引（主食材、購買方式、商品標籤）→ 商品列表（左側分類列表、搜尋、排序，點商品開啟快速檢視；冷凍調理包可在視窗內選數量加入購物車）。網址可帶條件，例如 `products.html#cat=soup&ing=beef` |
| 　└ 子頁 | 門市菜單・點餐方式（`menu.html`）、百貨催事弁當（`bento.html`）、線上訂購（`shop.html`）與 3 個商品頁 |
| 最新消息 | 依分類篩選 |
| 門市資訊 | 門市一覽（台中大里店）、百貨催事出店 |
| 購物須知 | 付款、配送、發票、退換貨 |
| 關於湯匠 | 品牌故事、湯匠的堅持、湯咖哩的工序、公司資訊 |
| 團體訂購 | 會議餐盒、活動聚餐、冷凍調理包大量訂購 |
| 其他 | 常見問題、網站地圖、隱私權政策、購物車、結帳、404 |
| 後端（Cloudways） | `api/checkout.php` 結帳→綠界、`api/ecpay-return.php` 付款通知、`api/ecpay-result.php` 付款後返回、`admin/` 訂單後台 |

商品的分類（主食材、購買方式、標籤）設定在 `build.py` 的 `PCATS`／`PING`／`PBUY`／`PTAG` 與 `_ING`；新增商品時在 `content.py` 加資料、在 `_ING` 指定主食材即可。

選單、下拉選單、頁尾與網站地圖頁都由 `build.py` 的 `tree()` 產生，改一處全站同步。

全站中文／日文。手機有底部快捷列（電話・導航・菜單／LINE・購物車）。

## 目前上線方式：GitHub Pages（www.yushosoupcurry.com）

- 儲存庫：`yushosoupcurry-netizen/sapporo-yusho`。推送到 `main` 後，GitHub Actions（`.github/workflows/pages.yml`）會自動執行 `python build.py`，把 `dist-pages/` 發布到網站，約 1～2 分鐘生效。
- **改網站的方法**：在 GitHub 網頁直接編輯檔案並 Commit，或請 Claude 修改後推送。常改的地方：
  - 價格、營業時間、LINE、運費、網域 → `config.py`
  - 文案、菜單、弁當、最新消息、常見問題 → `content.py`
  - 圖片 → `src/img/`
- DNS（Namecheap）：`@` 指向 GitHub 的 4 個 IP（185.199.108–111.153），`www` CNAME 指向 `yushosoupcurry-netizen.github.io`。SSL 由 GitHub 自動申請、續約。
- 付款：GitHub Pages 沒有後端，結帳後顯示訂單編號，並提供綠界「收款連結」（`config.py` 的 `ECPAY_PAYLINK`）。客人確認總金額後自行填寫金額、備註填訂單編號付款，請到綠界後台「一般訂單查詢」對帳。
- 之後搬到 Cloudways：照下方「上線步驟」上傳 `dist/`，填好運費即自動改用綠界完整金流（金額自動帶入、付款狀態回傳後台）。

## 檔案

| 路徑 | 用途 |
|---|---|
| `config.py` | **日常更新只改這裡**：營業時間、LINE、價格、運費、統一編號、食品業者登錄字號、網域 |
| `content.py` | 文案、菜單、催事弁當（`BENTO`）、商品標示、最新消息、常見問題 |
| `src/style.css`、`src/site.js`、`src/img/` | 樣式、購物車與動態、圖片 |
| `backend/` | PHP 後端原始碼（建置時複製到 dist/） |
| `build.py` | 產生網站：`python3 build.py` |
| `dist/` | **上傳到 Cloudways 的 public_html** |
| `dist-artifact/` | claude.ai 版（無後端，結帳改為電話確認） |
| `dist-pages/` | GitHub Pages 版（由 GitHub Actions 自動產生，不需手動上傳） |

## 上線步驟（Cloudways + Namecheap + 綠界）

1. **Cloudways**：建立 Server → Add Application 選 **Custom PHP**（PHP 8.1 以上）。
2. **設定**：`config.py` 填 `SITE_URL`、`SHIPPING["fee"]`（運費，填了才會開啟線上付款）、`COMPANY` 的統一編號與食品業者登錄字號 → 執行 `python3 build.py`。
3. **上傳**：SFTP 把 `dist/` 裡的所有檔案傳到 `public_html/`。
4. **後端設定**：把 `backend/private_html/yusho-config.sample.php` 複製成 `private_html/yusho-config.php`（在 public_html 旁邊，網址無法存取），填：
   - `site_url`：正式網址
   - `admin_password_hash`：`php -r "echo password_hash('你的密碼', PASSWORD_DEFAULT);"` 的輸出
   - 先保持 `mode => 'stage'` 與綠界測試特店資料
5. **網域**：Namecheap → Advanced DNS 的 `A Record`（@ 與 www）指到 Cloudways 伺服器 IP；Cloudways → Domain Management 加網域 → SSL 申請 Let's Encrypt。
6. **測試付款**：在網站下單，綠界測試頁使用測試信用卡 `4311-9522-2222-2222`（有效期限任一未來日期、安全碼 222）。到 `https://你的網域/admin/` 確認訂單變成「已付款」。
7. **正式收款**：綠界廠商後台 → 系統介接設定，取得正式 MerchantID／HashKey／HashIV，填入 `yusho-config.php` 並把 `mode` 改成 `'prod'`。
8. **通知信**（選用）：Cloudways 開啟 SMTP 附加元件後，在 `yusho-config.php` 填 `notify_email`，付款成功時會寄信通知。

## 已驗證

- 後端 22 項測試：伺服器端計價（顧客改不了價格）、滿額免運、未知商品與超量拒絕、表單驗證、防機器人欄位、偽造付款通知拒絕、金額不符拒絕、重複通知不重複處理、後台登入／CSRF／狀態更新／CSV 匯出、未登入無法匯出。
- 瀏覽器流程 19 項：輪播、加入購物車、徽章與提示、購物車改數量、結帳驗證、claude.ai 版產生訂單內容、Cloudways 版送出到綠界測試環境（金額 = 伺服器計算）、付款完成後清空購物車。
- 34 頁 × 手機／平板／電腦三種寬度：無水平捲動、無失效連結、無 JS 錯誤。
- CheckMacValue 與獨立實作比對一致；正式上線前仍需在綠界測試環境實際刷一次測試卡（第 6 步）。

## 上線前必須補齊

- [ ] **運費**（`SHIPPING["fee"]`）：未設定時線上付款不會開啟
- [ ] 統一編號、**食品業者登錄字號**（網路販售食品依法須標示）
- [ ] 營業時間、LINE 官方帳號、Instagram／Facebook
- [ ] 牛肋湯咖哩、午魚湯咖哩、三款熟成咖哩的門市價格
- [ ] 冷凍調理包成分中的「釀造豬」與實際包裝核對（疑似筆誤）
- [ ] 購物須知的退換貨處理方式（24 小時內聯繫、補寄或退款）是否符合實際作業
- [ ] 催事弁當日文品名：海報「葱塩豚バラー」網站改為「葱塩豚バラ」；鮭魚吻仔魚海報日文含「ツナ」，但中文品名與說明沒有鮪魚，網站改為「鮭・しらす玉子焼き弁当」。若實際有鮪魚，改 `content.py` 的 `BENTO`
- [ ] 催事會場的厚燒玉子單點價格（原味 NT$280、明太子 NT$330）讀自攤位照片，請確認
- [ ] 電子發票：目前結帳會收集統編與抬頭，發票由店家開立；若要自動開立，可再串接綠界電子發票
