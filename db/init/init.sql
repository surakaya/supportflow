USE supportflow;

INSERT INTO companies (name, api_key)
VALUES ('Test Company', 'test_api_key_123')
ON DUPLICATE KEY UPDATE name = VALUES(name);
