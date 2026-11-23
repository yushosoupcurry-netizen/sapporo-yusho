<?php
/**
 * 札幌湯匠 訂單後台：登入、訂單列表、明細、更新狀態與物流單號、匯出 CSV。
 * 帳號密碼設定在 private_html/yusho-config.php（admin_user / admin_password_hash）。
 */
declare(strict_types=1);
require __DIR__ . '/../api/_lib.php';

session_name('yusho_admin');
session_set_cookie_params(['httponly' => true, 'samesite' => 'Strict', 'secure' => !empty($_SERVER['HTTPS'])]);
session_start();
header('X-Frame-Options: DENY');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');

$a = $_GET['a'] ?? 'list';
if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(16));
$csrf = $_SESSION['csrf'];
$checkCsrf = function () use ($csrf) {
    if (!hash_equals($csrf, (string)($_POST['csrf'] ?? ''))) { http_response_code(400); exit('Bad request'); }
};

const STATUS = ['pending' => '待付款', 'await' => '待繳費', 'paid' => '已付款', 'shipped' => '已出貨', 'completed' => '已完成', 'failed' => '付款失敗', 'cancelled' => '已取消'];

// ── 登入 ──
if ($a === 'logout') { session_destroy(); header('Location: ./'); exit; }
if (empty($_SESSION['admin'])) {
    $err = '';
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $checkCsrf();
        $_SESSION['tries'] = ($_SESSION['tries'] ?? 0) + 1;
        if ($_SESSION['tries'] > 5) { sleep(3); }
        $okUser = hash_equals((string)cfg('admin_user'), (string)($_POST['user'] ?? ''));
        $okPass = password_verify((string)($_POST['pass'] ?? ''), (string)cfg('admin_password_hash'));
        if ($okUser && $okPass) {
            session_regenerate_id(true);
            $_SESSION['admin'] = true; $_SESSION['tries'] = 0;
            header('Location: ./'); exit;
        }
        $err = '帳號或密碼不正確。';
    }
    page('登入', '<form method="post" class="login"><h1>札幌湯匠 訂單後台</h1>'
        . ($err ? '<p class="err">' . h($err) . '</p>' : '')
        . '<label>帳號<input name="user" autocomplete="username" required></label>'
        . '<label>密碼<input name="pass" type="password" autocomplete="current-password" required></label>'
        . '<input type="hidden" name="csrf" value="' . h($csrf) . '"><button>登入</button></form>');
}

// ── 更新訂單 ──
if ($a === 'update' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $checkCsrf();
    $status = $_POST['status'] ?? '';
    if (!isset(STATUS[$status])) exit('Bad status');
    $st = db()->prepare('UPDATE orders SET status=?, tracking_no=?, admin_note=?, updated_at=? WHERE order_no=?');
    $st->execute([$status, mb_substr(trim((string)$_POST['tracking_no']), 0, 60), mb_substr((string)$_POST['admin_note'], 0, 2000), now(), (string)$_POST['no']]);
    header('Location: ?a=view&no=' . rawurlencode((string)$_POST['no']) . '&saved=1'); exit;
}

// ── 匯出 CSV ──
if ($a === 'csv') {
    header('Content-Type: text/csv; charset=UTF-8');
    header('Content-Disposition: attachment; filename="yusho-orders-' . date('Ymd') . '.csv"');
    $out = fopen('php://output', 'w');
    fwrite($out, "\xEF\xBB\xBF");
    fputcsv($out, ['訂單編號', '建立時間', '狀態', '商品', '小計', '運費', '總額', '收件人', '電話', 'Email', '縣市', '地址', '到貨時段', '發票', '統編', '抬頭', '備註', '綠界交易編號', '付款方式', '付款時間', '物流單號']);
    foreach (db()->query('SELECT * FROM orders ORDER BY id DESC') as $o) {
        $items = implode('、', array_map(fn($i) => "{$i['name']}×{$i['qty']}", json_decode($o['items_json'], true)));
        fputcsv($out, [$o['order_no'], $o['created_at'], STATUS[$o['status']] ?? $o['status'], $items, $o['subtotal'], $o['shipping'], $o['total'], $o['name'], $o['phone'], $o['email'],
            $o['city'], $o['address'], $o['delivery_time'], $o['invoice_type'] === 'company' ? '公司' : '個人', $o['tax_id'], $o['invoice_title'], $o['note'], $o['trade_no'], $o['payment_type'], $o['paid_at'], $o['tracking_no']]);
    }
    exit;
}

// ── 訂單明細 ──
if ($a === 'view') {
    $st = db()->prepare('SELECT * FROM orders WHERE order_no=?');
    $st->execute([(string)($_GET['no'] ?? '')]);
    $o = $st->fetch() ?: exit('Not found');
    $rows = '';
    foreach (json_decode($o['items_json'], true) as $i) $rows .= '<tr><td>' . h($i['name']) . '</td><td>' . (int)$i['qty'] . '</td><td>NT$' . number_format($i['price']) . '</td><td>NT$' . number_format($i['line']) . '</td></tr>';
    $opts = '';
    foreach (STATUS as $k => $v) $opts .= '<option value="' . $k . '"' . ($k === $o['status'] ? ' selected' : '') . '>' . $v . '</option>';
    $info = [
        '建立時間' => $o['created_at'], '狀態' => STATUS[$o['status']] ?? $o['status'], '收件人' => $o['name'], '電話' => $o['phone'], 'Email' => $o['email'],
        '地址' => $o['city'] . $o['address'], '到貨時段' => $o['delivery_time'] ?: '不指定',
        '發票' => $o['invoice_type'] === 'company' ? "公司｜{$o['tax_id']}｜{$o['invoice_title']}" : '個人', '顧客備註' => $o['note'],
        '綠界交易編號' => $o['trade_no'], '付款方式' => $o['payment_type'], '付款時間' => $o['paid_at'],
    ];
    $dl = '';
    foreach ($info as $k => $v) $dl .= '<tr><th>' . h($k) . '</th><td>' . nl2br(h((string)$v)) . '</td></tr>';
    page('訂單 ' . $o['order_no'], '<p><a href="./">← 訂單列表</a></p><h1>訂單 ' . h($o['order_no']) . '</h1>'
        . (isset($_GET['saved']) ? '<p class="ok">已儲存。</p>' : '')
        . '<table class="items"><tr><th>商品</th><th>數量</th><th>單價</th><th>小計</th></tr>' . $rows
        . '<tr><td colspan="3">運費</td><td>NT$' . number_format((int)$o['shipping']) . '</td></tr><tr class="tot"><td colspan="3">總額</td><td>NT$' . number_format((int)$o['total']) . '</td></tr></table>'
        . '<table class="info">' . $dl . '</table>'
        . '<form method="post" action="?a=update" class="upd"><h2>處理訂單</h2><input type="hidden" name="csrf" value="' . h($csrf) . '"><input type="hidden" name="no" value="' . h($o['order_no']) . '">'
        . '<label>狀態<select name="status">' . $opts . '</select></label><label>物流單號<input name="tracking_no" value="' . h($o['tracking_no']) . '"></label>'
        . '<label>內部備註<textarea name="admin_note" rows="3">' . h($o['admin_note']) . '</textarea></label><button>儲存</button></form>');
}

// ── 訂單列表 ──
$filter = $_GET['status'] ?? '';
$sql = 'SELECT * FROM orders' . (isset(STATUS[$filter]) ? ' WHERE status = ?' : '') . ' ORDER BY id DESC LIMIT 500';
$st = db()->prepare($sql);
$st->execute(isset(STATUS[$filter]) ? [$filter] : []);
$rows = '';
foreach ($st as $o) {
    $rows .= '<tr><td><a href="?a=view&no=' . h($o['order_no']) . '">' . h($o['order_no']) . '</a></td><td>' . h(substr($o['created_at'], 0, 16)) . '</td><td>' . h($o['name'])
        . '</td><td>' . h($o['phone']) . '</td><td class="r">NT$' . number_format((int)$o['total']) . '</td><td><span class="st st-' . h($o['status']) . '">' . h(STATUS[$o['status']] ?? $o['status']) . '</span></td></tr>';
}
$tabs = '<a href="./"' . ($filter === '' ? ' class="on"' : '') . '>全部</a>';
foreach (STATUS as $k => $v) $tabs .= '<a href="?status=' . $k . '"' . ($filter === $k ? ' class="on"' : '') . '>' . $v . '</a>';
page('訂單列表', '<div class="bar"><h1>訂單列表</h1><a class="btn" href="?a=csv">匯出 CSV</a></div><nav class="tabs">' . $tabs . '</nav>'
    . ($rows ? '<table class="list"><tr><th>訂單編號</th><th>建立時間</th><th>收件人</th><th>電話</th><th class="r">總額</th><th>狀態</th></tr>' . $rows . '</table>' : '<p>目前沒有訂單。</p>')
    . '<p class="mode">金流環境：' . (cfg('mode') === 'prod' ? '正式' : '測試（綠界測試環境，不會實際扣款）') . '</p>');

function page(string $title, string $body): never
{
    $nav = !empty($_SESSION['admin']) ? '<header><b>札幌湯匠 後台</b><a href="./">訂單</a><a href="?a=logout">登出</a></header>' : '';
    echo '<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
        . '<title>' . h($title) . '｜札幌湯匠後台</title><style>
body{margin:0;background:#ecebe7;color:#1a202b;font:14px/1.7 "Noto Sans TC",system-ui,sans-serif}header{background:#182338;color:#fff;display:flex;gap:24px;align-items:center;padding:12px 24px}
header a{color:#fff;opacity:.8}main{max-width:1080px;margin:0 auto;padding:24px}h1{font-size:22px;margin:0 0 16px}h2{font-size:16px}a{color:#182338}
table{width:100%;border-collapse:collapse;background:#fff;margin-bottom:24px}th,td{border:1px solid #d3d1cb;padding:8px 12px;text-align:left;vertical-align:top}th{background:#f3f2ee;font-weight:500;white-space:nowrap}
.r{text-align:right}.tot td{font-weight:700}.info th{width:9em}.bar{display:flex;justify-content:space-between;align-items:center}.btn,button{background:#182338;color:#fff;border:0;padding:10px 20px;cursor:pointer;text-decoration:none;font:inherit}
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px}.tabs a{padding:6px 12px;background:#fff;text-decoration:none;border:1px solid #d3d1cb}.tabs a.on{background:#182338;color:#fff}
.st{display:inline-block;padding:2px 8px;font-size:12px;background:#e2e0db}.st-paid{background:#c45f2a;color:#fff}.st-shipped,.st-completed{background:#182338;color:#fff}.st-failed,.st-cancelled{background:#999;color:#fff}
form.upd,form.login{background:#fff;padding:20px;display:grid;gap:12px;max-width:520px}label{display:grid;gap:4px}input,select,textarea{font:inherit;padding:8px;border:1px solid #bbb}
.login{margin:12vh auto}.err{color:#b00020}.ok{background:#e6f2e6;padding:8px 12px}.mode{color:#5a616d;font-size:12px}.list{overflow-x:auto}
</style></head><body>' . $nav . '<main>' . $body . '</main></body></html>';
    exit;
}
