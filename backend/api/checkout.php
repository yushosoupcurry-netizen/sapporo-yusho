<?php
/**
 * 結帳：驗證表單 → 以伺服器價格重新計算金額 → 建立訂單 → 自動送往綠界付款頁。
 * 價格只信任 products.json 與伺服器設定的運費，不信任瀏覽器送來的金額。
 */
declare(strict_types=1);
require __DIR__ . '/_lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Location: ' . site_url('cart.html')); exit; }

$lang = ($_POST['lang'] ?? 'zh') === 'ja' ? 'ja' : 'zh';
$cartPage = site_url($lang === 'ja' ? 'ja-checkout.html' : 'checkout.html');
$fail = fn(string $m) => message_page($lang === 'ja' ? 'ご注文を完了できませんでした' : '無法送出訂單', $m, $cartPage, $lang === 'ja' ? '戻る' : '返回結帳頁');

// 防機器人：隱藏欄位有值即拒絕
if (!empty($_POST['website'])) $fail('Invalid request.');

// ── 商品 ──
$raw = json_decode((string)($_POST['items'] ?? '[]'), true);
if (!is_array($raw) || !$raw) $fail('購物車是空的。');
$items = [];
$subtotal = 0;
$catalog = products();
foreach ($raw as $row) {
    $id = (string)($row['id'] ?? '');
    $qty = (int)($row['qty'] ?? 0);
    if (!isset($catalog[$id]) || $qty < 1 || $qty > (int)$catalog[$id]['max_qty']) $fail('商品或數量不正確，請重新確認購物車。');
    $p = $catalog[$id];
    $line = $p['price'] * $qty;
    $subtotal += $line;
    $items[] = ['id' => $id, 'name' => $p['name_zh'], 'price' => $p['price'], 'qty' => $qty, 'line' => $line];
}
$shipping = shipping_for($subtotal);
if ($shipping === null) $fail('線上付款尚未開放（運費尚未設定）。請來電訂購。');
$total = $subtotal + $shipping;

// ── 收件資料 ──
$f = fn(string $k, int $max) => trim(mb_substr((string)($_POST[$k] ?? ''), 0, $max));
$name = $f('name', 50);
$phone = preg_replace('/[^\d+]/', '', $f('phone', 30));
$email = $f('email', 200);
$city = $f('city', 10);
$address = $f('address', 200);
$delivery = $f('delivery_time', 20);
$invType = in_array($_POST['invoice_type'] ?? '', ['personal', 'company'], true) ? $_POST['invoice_type'] : 'personal';
$taxId = preg_replace('/\D/', '', $f('tax_id', 8));
$invTitle = $f('invoice_title', 100);
$note = $f('note', 500);

$errors = [];
if ($name === '') $errors[] = '請填寫收件人姓名。';
if (!preg_match('/^(09\d{8}|0\d{8,9}|\+?886\d{8,9})$/', $phone)) $errors[] = '請填寫正確的電話號碼。';
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) $errors[] = '請填寫正確的 Email。';
$cities = ['台北市','新北市','基隆市','桃園市','新竹市','新竹縣','苗栗縣','台中市','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','台南市','高雄市','屏東縣','宜蘭縣','花蓮縣','台東縣'];
if (!in_array($city, $cities, true)) $errors[] = '請選擇縣市（冷凍宅配目前僅限台灣本島）。';
if (mb_strlen($address) < 5) $errors[] = '請填寫完整地址。';
if ($invType === 'company' && (strlen($taxId) !== 8 || $invTitle === '')) $errors[] = '公司發票請填寫 8 碼統一編號與抬頭。';
if (empty($_POST['agree'])) $errors[] = '請勾選同意購物須知與隱私權政策。';
if ($errors) $fail(implode("\n", $errors));

// ── 建立訂單 ──
$tz = new DateTimeZone('Asia/Taipei');
$nowDt = new DateTimeImmutable('now', $tz);
$orderNo = 'YS' . $nowDt->format('ymdHis') . str_pad((string)random_int(0, 9999), 4, '0', STR_PAD_LEFT);
$ts = now();
$stmt = db()->prepare('INSERT INTO orders (order_no,status,lang,items_json,subtotal,shipping,total,name,phone,email,city,address,delivery_time,invoice_type,tax_id,invoice_title,note,consent_at,ip,created_at,updated_at)
 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
$stmt->execute([$orderNo, 'pending', $lang, json_encode($items, JSON_UNESCAPED_UNICODE), $subtotal, $shipping, $total, $name, $phone, $email, $city, $address,
    $delivery, $invType, $taxId, $invTitle, $note, $ts, client_ip(), $ts, $ts]);

// ── 綠界參數 ──
$itemName = implode('#', array_map(fn($i) => "{$i['name']} x {$i['qty']}", $items));
if ($shipping > 0) $itemName .= "#冷凍運費 x 1";
$params = [
    'MerchantID' => (string)cfg('merchant_id'),
    'MerchantTradeNo' => $orderNo,
    'MerchantTradeDate' => $nowDt->format('Y/m/d H:i:s'),
    'PaymentType' => 'aio',
    'TotalAmount' => (string)$total,
    'TradeDesc' => '札幌湯匠冷凍調理包',
    'ItemName' => mb_substr($itemName, 0, 200),
    'ReturnURL' => site_url('api/ecpay-return.php'),
    'OrderResultURL' => site_url('api/ecpay-result.php'),
    'ClientBackURL' => site_url($lang === 'ja' ? 'ja-shop.html' : 'shop.html'),
    'ChoosePayment' => (string)(cfg('choose_payment') ?: 'ALL'),
    'EncryptType' => '1',
    'CustomField1' => $lang,
];
$params['CheckMacValue'] = ecpay_mac($params, cfg('hash_key'), cfg('hash_iv'));

header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: no-store');
$fields = '';
foreach ($params as $k => $v) $fields .= '<input type="hidden" name="' . h($k) . '" value="' . h($v) . '">';
echo '<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>前往付款｜札幌湯匠</title>'
    . '<style>body{margin:0;background:#ecebe7;font-family:system-ui,sans-serif;color:#1a202b;display:grid;place-items:center;min-height:100vh}button{background:#182338;color:#fff;border:0;padding:14px 28px;font-size:15px;letter-spacing:.12em;cursor:pointer}</style></head><body>'
    . '<form id="f" method="post" action="' . h(ecpay_endpoint()) . '">' . $fields
    . '<p>正在前往綠界安全付款頁面…<br>訂單編號 ' . h($orderNo) . '</p><button type="submit">前往付款</button></form>'
    . '<script>document.getElementById("f").submit()</script></body></html>';
