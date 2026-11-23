<?php
/**
 * 札幌湯匠 線上訂購後端（Cloudways / 任何 PHP 8.1+ 主機）
 * 共用函式：設定讀取、資料庫、綠界 CheckMacValue、輸出工具。
 */
declare(strict_types=1);

if (basename($_SERVER['SCRIPT_FILENAME'] ?? '') === '_lib.php') { http_response_code(404); exit; }

function cfg(?string $key = null)
{
    static $c = null;
    if ($c === null) {
        $paths = array_filter([
            getenv('YUSHO_CONFIG') ?: null,
            __DIR__ . '/../../private_html/yusho-config.php',   // Cloudways：public_html 旁的 private_html（網址無法存取）
            __DIR__ . '/../private/yusho-config.php',
        ]);
        foreach ($paths as $p) {
            if (is_file($p)) { $c = require $p; break; }
        }
        if (!is_array($c)) {
            http_response_code(500);
            exit('Server configuration missing.');
        }
    }
    return $key === null ? $c : ($c[$key] ?? null);
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo) return $pdo;
    $pdo = new PDO(cfg('db_dsn'), cfg('db_user'), cfg('db_pass'), [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $auto = str_starts_with(cfg('db_dsn'), 'sqlite') ? 'INTEGER PRIMARY KEY AUTOINCREMENT' : 'INT AUTO_INCREMENT PRIMARY KEY';
    $pdo->exec("CREATE TABLE IF NOT EXISTS orders (
        id $auto,
        order_no VARCHAR(20) NOT NULL UNIQUE,
        status VARCHAR(16) NOT NULL DEFAULT 'pending',
        lang VARCHAR(5) NOT NULL DEFAULT 'zh',
        items_json TEXT NOT NULL,
        subtotal INT NOT NULL,
        shipping INT NOT NULL,
        total INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(30) NOT NULL,
        email VARCHAR(200) NOT NULL,
        city VARCHAR(20) NOT NULL,
        address VARCHAR(300) NOT NULL,
        delivery_time VARCHAR(30) NOT NULL DEFAULT '',
        invoice_type VARCHAR(20) NOT NULL DEFAULT 'personal',
        tax_id VARCHAR(8) NOT NULL DEFAULT '',
        invoice_title VARCHAR(200) NOT NULL DEFAULT '',
        note TEXT,
        trade_no VARCHAR(30) NOT NULL DEFAULT '',
        payment_type VARCHAR(40) NOT NULL DEFAULT '',
        paid_at VARCHAR(30) NOT NULL DEFAULT '',
        tracking_no VARCHAR(60) NOT NULL DEFAULT '',
        admin_note TEXT,
        ecpay_raw TEXT,
        consent_at VARCHAR(30) NOT NULL,
        ip VARCHAR(64) NOT NULL DEFAULT '',
        created_at VARCHAR(30) NOT NULL,
        updated_at VARCHAR(30) NOT NULL
    )");
    return $pdo;
}

function now(): string
{
    return (new DateTimeImmutable('now', new DateTimeZone('Asia/Taipei')))->format('Y-m-d H:i:s');
}

/** 綠界 CheckMacValue（SHA256；依綠界技術文件「檢查碼機制」） */
function ecpay_mac(array $params, string $hashKey, string $hashIV): string
{
    unset($params['CheckMacValue']);
    uksort($params, 'strcasecmp');
    $s = 'HashKey=' . $hashKey;
    foreach ($params as $k => $v) $s .= '&' . $k . '=' . $v;
    $s .= '&HashIV=' . $hashIV;
    $s = strtolower(urlencode($s));
    $s = str_replace(['%2d', '%5f', '%2e', '%21', '%2a', '%28', '%29'], ['-', '_', '.', '!', '*', '(', ')'], $s);
    return strtoupper(hash('sha256', $s));
}

function ecpay_verify(array $post): bool
{
    if (empty($post['CheckMacValue'])) return false;
    return hash_equals(ecpay_mac($post, cfg('hash_key'), cfg('hash_iv')), strtoupper((string)$post['CheckMacValue']));
}

function ecpay_endpoint(): string
{
    return cfg('mode') === 'prod'
        ? 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
        : 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5';
}

/** 商品與運費：由 build.py 依 config.py 產生的 shop.json（伺服器端唯一的價格依據） */
function shop(): array
{
    static $s = null;
    return $s ??= json_decode((string)file_get_contents(__DIR__ . '/shop.json'), true);
}

function products(): array
{
    $p = [];
    foreach (shop()['products'] as $row) $p[$row['id']] = $row;
    return $p;
}

function shipping_for(int $subtotal): ?int
{
    $fee = shop()['shipping_fee'] ?? null;
    if ($fee === null) return null;
    $free = shop()['free_shipping_over'] ?? null;
    return ($free !== null && $subtotal >= $free) ? 0 : (int)$fee;
}

function h(?string $s): string
{
    return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function site_url(string $path = ''): string
{
    return rtrim((string)cfg('site_url'), '/') . '/' . ltrim($path, '/');
}

function client_ip(): string
{
    return substr((string)($_SERVER['REMOTE_ADDR'] ?? ''), 0, 64);
}

function notify_paid(array $o): void
{
    $to = cfg('notify_email');
    if (!$to) return;
    $items = implode("\n", array_map(fn($i) => "・{$i['name']} × {$i['qty']}  NT\${$i['line']}", json_decode($o['items_json'], true)));
    $body = "札幌湯匠 新訂單（已付款）\n\n訂單編號：{$o['order_no']}\n金額：NT\${$o['total']}\n付款方式：{$o['payment_type']}\n\n{$items}\n\n"
        . "收件人：{$o['name']}\n電話：{$o['phone']}\nEmail：{$o['email']}\n地址：{$o['city']}{$o['address']}\n到貨時段：{$o['delivery_time']}\n備註：{$o['note']}\n\n"
        . "後台：" . site_url('admin/');
    $from = cfg('mail_from') ?: $to;
    @mail($to, '=?UTF-8?B?' . base64_encode("【札幌湯匠】新訂單 {$o['order_no']}") . '?=', $body,
        "From: {$from}\r\nContent-Type: text/plain; charset=UTF-8\r\n");
}

/** 極簡錯誤／訊息頁（與網站同色系） */
function message_page(string $title, string $msg, string $back = '/', string $backText = '返回'): never
{
    header('Content-Type: text/html; charset=UTF-8');
    echo '<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        . '<title>' . h($title) . '｜札幌湯匠</title><style>body{margin:0;background:#ecebe7;color:#1a202b;font-family:"Noto Sans TC",system-ui,sans-serif;line-height:1.9}'
        . 'main{max-width:560px;margin:12vh auto;padding:40px 28px;background:#fbfaf8;border-top:4px solid #182338}h1{font-size:22px;letter-spacing:.12em;margin:0 0 12px}'
        . 'a{display:inline-block;margin-top:20px;background:#182338;color:#fff;padding:12px 24px;text-decoration:none;letter-spacing:.14em}</style></head><body><main>'
        . '<h1>' . h($title) . '</h1><p>' . nl2br(h($msg)) . '</p><a href="' . h($back) . '">' . h($backText) . '</a></main></body></html>';
    exit;
}
