-- Crear base de datos
DROP DATABASE IF EXISTS flask_users;
CREATE DATABASE flask_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flask_users;

-- Crear tabla de usuarios
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email, password)
VALUES ('demo', 'demo@email.com', 'demopass');
