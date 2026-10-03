<?php

function contact_pdo(array $cfg): PDO
{
    $dsn = 'mysql:host=' . $cfg['db']['host'] . ';dbname=' . $cfg['db']['name'] . ';charset=utf8mb4';

    return new PDO(
        $dsn,
        $cfg['db']['user'],
        $cfg['db']['pass'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
}

function contact_insert_submission(PDO $pdo, array $data): void
{
    $sql = 'INSERT INTO contact_submissions
        (request_id, name, email, subject, message, ip_hash, user_agent, status)
        VALUES
        (:request_id, :name, :email, :subject, :message, :ip_hash, :user_agent, :status)';

    $stmt = $pdo->prepare($sql);
    $stmt->execute($data);
}

function contact_update_status(PDO $pdo, string $requestId, string $status, bool $markSent = false): void
{
    if ($markSent) {
        $sql = 'UPDATE contact_submissions SET status = :status, email_sent_at = NOW() WHERE request_id = :request_id';
    } else {
        $sql = 'UPDATE contact_submissions SET status = :status WHERE request_id = :request_id';
    }

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        'status' => $status,
        'request_id' => $requestId,
    ]);
}

function contact_count_recent_by_ip(PDO $pdo, string $ipHash, int $windowSeconds): int
{
    $sql = 'SELECT COUNT(*) AS c FROM contact_submissions
        WHERE ip_hash = :ip_hash
        AND created_at >= DATE_SUB(NOW(), INTERVAL :window_seconds SECOND)';

    $stmt = $pdo->prepare($sql);
    $stmt->bindValue(':ip_hash', $ipHash, PDO::PARAM_STR);
    $stmt->bindValue(':window_seconds', $windowSeconds, PDO::PARAM_INT);
    $stmt->execute();

    $row = $stmt->fetch();
    return (int)($row['c'] ?? 0);
}
