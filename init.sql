CREATE DATABASE IF NOT EXISTS videos;
USE videos;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE,
  password VARCHAR(255),
  is_admin TINYINT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS videos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255),
  path VARCHAR(512),
  owner VARCHAR(100)
);

INSERT INTO users (username, password, is_admin)
VALUES ('admin', 'password123', 1)
ON DUPLICATE KEY UPDATE username = username;
