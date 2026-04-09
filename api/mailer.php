<?php

function contact_mail_safe_header_text(string $value): string
{
    $value = trim($value);
    return str_replace(["\r", "\n"], ' ', $value);
}

function contact_send_mail(array $cfg, array $payload, string $requestId): array
{
    $to = contact_mail_safe_header_text((string)$cfg['mail']['to']);
    $from = contact_mail_safe_header_text((string)$cfg['mail']['from']);
    $fromName = contact_mail_safe_header_text((string)($cfg['mail']['from_name'] ?? 'Hornsloth Portfolio'));

    $senderName = contact_mail_safe_header_text((string)$payload['name']);
    $senderEmail = contact_mail_safe_header_text((string)$payload['email']);
    $senderSubject = contact_mail_safe_header_text((string)$payload['subject']);

    $subjectCore = $senderSubject !== '' ? $senderSubject : 'New Inquiry';
    if (!preg_match('/[A-Za-z0-9]/', $subjectCore)) {
        $subjectCore = 'New Inquiry';
    }
    $subject = 'Portfolio Contact | ' . $subjectCore;

    $bodyLines = [
        'New contact form submission',
        '',
        'Name: ' . $senderName,
        'Email: ' . $senderEmail,
        'Subject: ' . $subjectCore,
        'Request ID: ' . $requestId,
        '',
        'Message:',
        trim((string)$payload['message']),
    ];
    $body = implode(PHP_EOL, $bodyLines) . PHP_EOL;

    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'From: ' . $fromName . ' <' . $from . '>',
        'Reply-To: ' . $senderName . ' <' . $senderEmail . '>',
    ];

    $ok = mail($to, $subject, $body, implode("\r\n", $headers));

    return [
        'ok' => $ok,
        'error' => $ok ? null : 'mail_failed',
    ];
}
