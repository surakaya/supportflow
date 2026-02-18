CREATE DATABASE IF NOT EXISTS `supportflow`;
USE `supportflow`;

CREATE TABLE IF NOT EXISTS `companies` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `api_key` VARCHAR(64) NOT NULL UNIQUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `tickets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `company_id` INT NOT NULL,
    `message` TEXT NOT NULL,
    `category` VARCHAR(100),
    `urgency` ENUM('low', 'medium', 'high'),
    `priority` INT,
    `confidence` FLOAT,
    `idempotency_key` VARCHAR(64) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_company`
        FOREIGN KEY (`company_id`)
        REFERENCES `companies`(`id`)
        ON DELETE CASCADE,
    CONSTRAINT `uq_ticket_idempotency`
        UNIQUE (`company_id`, `idempotency_key`)
);
