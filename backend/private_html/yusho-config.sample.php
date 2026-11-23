<?php
/**
 * 札幌湯匠 後端設定（範本）
 * 上傳到 Cloudways 時，複製為 private_html/yusho-config.php（不要放在 public_html）。
 * 本檔含金鑰與密碼雜湊，請勿提交到公開的 Git。
 */
return [
    // 'stage' = 綠界測試環境（不會扣款）；確認流程無誤後改為 'prod'，並換成正式特店資料
    'mode' => 'stage',

    // 綠界特店資料（綠界廠商後台 → 系統開發管理 → 系統介接設定）
    // 以下為綠界官方公開的「測試環境」特店資料，僅能在 stage 使用
    'merchant_id' => '3002607',
    'hash_key'    => 'pwFHCqoQZGmho4w6',
    'hash_iv'     => 'EkRm7iFT261dpevs',
    'choose_payment' => 'ALL',          // ALL / Credit / ATM / CVS …（依綠界合約開通的付款方式）

    'site_url' => 'https://www.example.com',   // 正式網址（綠界通知會打到這裡，必須是 https 公開網址）

    // 運費與商品價格在網站的 config.py 設定（build.py 會產生 api/shop.json），這裡不需要重複設定。

    // 訂單資料庫：預設 SQLite 檔案放在 private_html；要用 Cloudways MySQL 可改成 mysql DSN
    'db_dsn'  => 'sqlite:' . __DIR__ . '/yusho-orders.sqlite',
    'db_user' => null,
    'db_pass' => null,

    // 後台登入（/admin/）。密碼雜湊產生方式：php -r "echo password_hash('你的密碼', PASSWORD_DEFAULT);"
    'admin_user' => 'yusho',
    'admin_password_hash' => '',

    // 付款成功通知信（Cloudways 需先開啟 SMTP 附加元件）
    'notify_email' => null,
    'mail_from' => null,
];
