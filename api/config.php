<?php

$config = [
    'db' => [
        'host' => getenv('CONTACT_DB_HOST') ?: 'localhost',
        'name' => getenv('CONTACT_DB_NAME') ?: 'REPLACE_DB_NAME',
        'user' => getenv('CONTACT_DB_USER') ?: 'REPLACE_DB_USER',
        'pass' => getenv('CONTACT_DB_PASS') ?: 'REPLACE_DB_PASS',
    ],
    'mail' => [
        'to' => getenv('CONTACT_MAIL_TO') ?: 'REPLACE_NOTIFICATION_EMAIL',
        'from' => getenv('CONTACT_MAIL_FROM') ?: 'REPLACE_SENDER_EMAIL',
        'from_name' => getenv('CONTACT_MAIL_FROM_NAME') ?: 'Hornsloth Portfolio',
        'smtp' => [
            'host' => getenv('CONTACT_SMTP_HOST') ?: 'smtp.zoho.in',
            'port' => (int)(getenv('CONTACT_SMTP_PORT') ?: 465),
            'secure' => getenv('CONTACT_SMTP_SECURE') ?: 'ssl',
            'username' => getenv('CONTACT_SMTP_USER') ?: 'REPLACE_SMTP_USERNAME',
            'password' => getenv('CONTACT_SMTP_PASS') ?: 'REPLACE_SMTP_PASSWORD',
            'timeout' => (int)(getenv('CONTACT_SMTP_TIMEOUT') ?: 20),
        ],
    ],
    'security' => [
        'min_fill_seconds' => 3,
        'rate_limit_window_seconds' => 300,
        'rate_limit_max_requests' => 5,
    ],
];

$localConfigPath = __DIR__ . '/config.local.php';
if (is_file($localConfigPath)) {
    $local = require $localConfigPath;
    if (is_array($local)) {
        $config = array_replace_recursive($config, $local);
    }
}

return $config;
