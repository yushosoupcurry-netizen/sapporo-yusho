<?php
/**
 * 綠界 OrderResultURL（消費者付款後，瀏覽器被帶回本站）。
 * 只用來顯示結果；訂單狀態以 ReturnURL 的伺服器通知為準。
 */
declare(strict_types=1);
require __DIR__ . '/_lib.php';

$post = $_POST;
$lang = ($post['CustomField1'] ?? 'zh') === 'ja' ? 'ja' : 'zh';
$page = $lang === 'ja' ? 'ja-order-complete.html' : 'order-complete.html';
$no = preg_replace('/[^A-Za-z0-9]/', '', (string)($post['MerchantTradeNo'] ?? ''));
$valid = ecpay_verify($post);
$code = (string)($post['RtnCode'] ?? '');
// 1 = 付款成功；2 = ATM 取號成功；10100073 = 超商代碼取號成功（之後付款時，綠界會再通知 ReturnURL）
$s = !$valid ? 'failed' : ($code === '1' ? 'paid' : (in_array($code, ['2', '10100073'], true) ? 'await' : 'failed'));
header('Location: ' . site_url($page) . '?no=' . rawurlencode($no) . '&s=' . $s, true, 303);
