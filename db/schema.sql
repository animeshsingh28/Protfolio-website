-- Postgres schema for the contact form (api/contact.py).
-- Run once in the Neon SQL editor (or psql "$DATABASE_URL" -f db/schema.sql).
-- Column sizes mirror MAX_LENGTHS in api/contact.py and the inputs' maxlength
-- in sections/contact.html; change all three together.
CREATE TABLE IF NOT EXISTS contact_submissions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    subject VARCHAR(150) NOT NULL,
    message VARCHAR(5000) NOT NULL,
    ip_hash CHAR(64) NOT NULL,
    user_agent VARCHAR(255),
    status TEXT NOT NULL DEFAULT 'received'
        CHECK (status IN ('received', 'emailed', 'email_failed', 'rejected')),
    email_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contact_created_at ON contact_submissions (created_at);
CREATE INDEX IF NOT EXISTS idx_contact_email ON contact_submissions (email);
CREATE INDEX IF NOT EXISTS idx_contact_ip_created ON contact_submissions (ip_hash, created_at);
