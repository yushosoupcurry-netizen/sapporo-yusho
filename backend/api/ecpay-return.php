<?php
/**
 * 綠界 ReturnURL（伺服器對伺服器的付款結果通知）。
 * 驗證 CheckMacValue、特店編號與金額後更新訂單；必須回傳 1|OK。
 */
declare(strict_types=1);
require __DIR__ . '/_lib.php';

header('Content-Type: text/plain; charset=UTF-8');
$post = $_POST;

if (!ecpay_verify($post)) { echo '0|CheckMacValue Error'; exit; }
if (($post['MerchantID'] ?? '') !== (string)cfg('merchant_id')) { echo '0|MerchantID Error'; exit; }

$no = (string)($post['MerchantTradeNo'] ?? '');
$st = db()->prepare('SELECT * FROM orders WHERE order_no = ?');
$st->execute([$no]);
$o = $st->fetch();
if (!$o) { echo '0|Order Not Found'; exit; }
if ((int)($post['TradeAmt'] ?? -1) !== (int)$o['total']) { echo '0|Amount Mismatch'; exit; }

// 正式環境不接受「模擬付款」
$simulated = ($post['SimulatePaid'] ?? '0') === '1';
if ($simulated && cfg('mode') === 'prod') { echo '1|OK'; exit; }

if ($o['status'] === 'pending' || $o['status'] === 'failed') {
    $paid = ($post['RtnCode'] ?? '') === '1';
    $up = db()->prepare('UPDATE orders SET status=?, trade_no=?, payment_type=?, paid_at=?, ecpay_raw=?, updated_at=? WHERE order_no=?');
    $up->execute([
        $paid ? 'paid' : 'failed',
        (string)($post['TradeNo'] ?? ''),
        (string)($post['PaymentType'] ?? ''),
        $paid ? (string)($post['PaymentDate'] ?? now()) : '',
        json_encode($post, JSON_UNESCAPED_UNICODE),
        now(),
        $no,
    ]);
    if ($paid) {
        $st->execute([$no]);
        notify_paid($st->fetch());
    }
}
echo '1|OK';
