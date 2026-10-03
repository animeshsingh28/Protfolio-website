<?php

header('Content-Type: application/json; charset=UTF-8');

$cfg = require __DIR__ . '/config.php';
require __DIR__ . '/db.php';
require __DIR__ . '/mailer.php';

function respond(int $statusCode, array $data): void
{
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function clean_text(string $value): string
{
    $value = trim($value);
    $value = preg_replace('/\R/u', PHP_EOL, $value) ?? $value;
    $value = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $value) ?? $value;
    return $value;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(405, [
        'success' => false,
        'message' => 'Method not allowed',
    ]);
}

$contentType = $_SERVER['CONTENT_TYPE'] ?? '';
$rawBody = file_get_contents('php://input');
$input = [];

if (stripos($contentType, 'application/json') !== false) {
    $decoded = json_decode($rawBody, true);
    if (!is_array($decoded)) {
        respond(400, [
            'success' => false,
            'message' => 'Invalid JSON payload',
        ]);
    }
    $input = $decoded;
} elseif (stripos($contentType, 'application/x-www-form-urlencoded') !== false || stripos($contentType, 'multipart/form-data') !== false || $contentType === '') {
    $input = $_POST;
} else {
    respond(415, [
        'success' => false,
        'message' => 'Unsupported payload type',
    ]);
}

$name = clean_text((string)($input['name'] ?? ''));
$email = clean_text((string)($input['email'] ?? ''));
$subject = clean_text((string)($input['subject'] ?? ''));
$message = clean_text((string)($input['message'] ?? ''));
$honeypot = clean_text((string)($input['company_website'] ?? ''));
$formStartedAt = (int)($input['form_started_at'] ?? 0);


if ($honeypot !== '') {
    respond(429, [
        'success' => false,
        'message' => 'blocked_honeypot',
    ]);
}

$now = time();
if ($formStartedAt <= 0 || ($now - $formStartedAt) < (int)$cfg['security']['min_fill_seconds']) {
    respond(429, [
        'success' => false,
        'message' => 'blocked_fill_time',
    ]);
}

if ($name === '' || $email === '' || $subject === '' || $message === '') {
    respond(400, [
        'success' => false,
        'message' => 'All fields are required',
    ]);
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(400, [
        'success' => false,
        'message' => 'Invalid email address',
    ]);
}

if (mb_strlen($name) > 100 || mb_strlen($email) > 254 || mb_strlen($subject) > 150 || mb_strlen($message) > 5000) {
    respond(400, [
        'success' => false,
        'message' => 'Input exceeds allowed limits',
    ]);
}

$requestId = bin2hex(random_bytes(16));
$ip = (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
$ipHash = hash('sha256', $ip);
$userAgent = clean_text(substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 255));

try {
    $pdo = contact_pdo($cfg);

    $recentCount = contact_count_recent_by_ip(
        $pdo,
        $ipHash,
        (int)$cfg['security']['rate_limit_window_seconds']
    );

    if ($recentCount >= (int)$cfg['security']['rate_limit_max_requests']) {
        respond(429, [
            'success' => false,
            'message' => 'Too many requests. Please try again later.',
        ]);
    }

    contact_insert_submission($pdo, [
        'request_id' => $requestId,
        'name' => $name,
        'email' => $email,
        'subject' => $subject,
        'message' => $message,
        'ip_hash' => $ipHash,
        'user_agent' => $userAgent,
        'status' => 'received',
    ]);

    $mailResult = contact_send_mail($cfg, [
        'name' => $name,
        'email' => $email,
        'subject' => $subject,
        'message' => $message,
    ], $requestId);

    if ($mailResult['ok']) {
        contact_update_status($pdo, $requestId, 'emailed', true);
        respond(200, [
            'success' => true,
            'message' => 'Message received. I will get back to you soon.',
            'requestId' => $requestId,
        ]);
    }

    contact_update_status($pdo, $requestId, 'email_failed', false);
    respond(500, [
        'success' => false,
        'message' => 'Submission saved, but notification failed. Please try again later.',
        'requestId' => $requestId,
    ]);
} catch (Throwable $error) {
    respond(500, [
        'success' => false,
        'message' => 'Server error',
    ]);
}
