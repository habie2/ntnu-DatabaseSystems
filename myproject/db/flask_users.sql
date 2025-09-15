-- Crear base de datos
DROP DATABASE IF EXISTS flask_users;
CREATE DATABASE flask_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flask_users;

-- Crear tabla de usuarios
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar usuario de prueba (contraseña: test123)
-- El hash corresponde a la contraseña "test123" generada con bcrypt
INSERT INTO users (username, email, password_hash)
VALUES ('usuario_demo', 'demo@email.com', 
        '$2b$12$H/.AZxVQJPRGBVvj8b9B6eY9AN7k1qAnV9jJcAGfYzyF.9p3S7f0a');
