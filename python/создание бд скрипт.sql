-- Создание базы данных
CREATE DATABASE IF NOT EXISTS auth_system;
USE auth_system;

-- Таблица пользователей
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    patronymic VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- Таблица ролей
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица разрешений
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- например: 'users:create', 'products:read'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ресурсов
CREATE TABLE resources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- например: 'users', 'products', 'orders'
    description TEXT
);

-- Связь ролей и разрешений
CREATE TABLE role_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    resource_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    UNIQUE KEY unique_role_permission_resource (role_id, permission_id, resource_id)
);

-- Индивидуальные разрешения пользователей
CREATE TABLE user_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    resource_id INT NOT NULL,
    is_granted BOOLEAN DEFAULT TRUE, -- TRUE = разрешено, FALSE = запрещено
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_permission_resource (user_id, permission_id, resource_id)
);

-- Связь пользователей и ролей
CREATE TABLE user_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (user_id, role_id)
);

-- Таблица сессий
CREATE TABLE sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Заполнение тестовыми данными
-- Ресурсы
INSERT INTO resources (name, code) VALUES 
('Пользователи', 'users'),
('Роли', 'roles'),
('Разрешения', 'permissions'),
('Товары', 'products'),
('Заказы', 'orders');

-- Разрешения
INSERT INTO permissions (name, code) VALUES 
('Создание', 'create'),
('Чтение', 'read'),
('Обновление', 'update'),
('Удаление', 'delete'),
('Управление', 'manage');

-- Роли
INSERT INTO roles (name, description) VALUES 
('Администратор', 'Полный доступ ко всем ресурсам'),
('Менеджер', 'Управление товарами и заказами'),
('Пользователь', 'Базовый пользователь');

-- Назначение разрешений для ролей
-- Администратор (полный доступ ко всем ресурсам)
INSERT INTO role_permissions (role_id, permission_id, resource_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'Администратор'),
    p.id,
    r.id
FROM permissions p, resources r
WHERE p.code IN ('create', 'read', 'update', 'delete', 'manage');

-- Менеджер (управление товарами и заказами)
INSERT INTO role_permissions (role_id, permission_id, resource_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'Менеджер'),
    p.id,
    r.id
FROM permissions p, resources r
WHERE p.code IN ('create', 'read', 'update')
AND r.code IN ('products', 'orders');

-- Пользователь (только чтение своих данных)
INSERT INTO role_permissions (role_id, permission_id, resource_id) VALUES 
((SELECT id FROM roles WHERE name = 'Пользователь'), 
 (SELECT id FROM permissions WHERE code = 'read'),
 (SELECT id FROM resources WHERE code = 'products'));

-- Создание тестовых пользователей
INSERT INTO users (email, password_hash, first_name, last_name, patronymic, is_active) VALUES 
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6NqC2e1tF6', 'Админ', 'Админов', 'Админович', TRUE),
('manager@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6NqC2e1tF6', 'Менеджер', 'Менеджеров', 'Менеджерович', TRUE),
('user@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6NqC2e1tF6', 'Пользователь', 'Пользователев', 'Пользователевич', TRUE);

-- Назначение ролей пользователям
INSERT INTO user_roles (user_id, role_id) VALUES 
(1, (SELECT id FROM roles WHERE name = 'Администратор')),
(2, (SELECT id FROM roles WHERE name = 'Менеджер')),
(3, (SELECT id FROM roles WHERE name = 'Пользователь'));

-- Индивидуальное разрешение (пример: запрет менеджеру на удаление)
INSERT INTO user_permissions (user_id, permission_id, resource_id, is_granted) VALUES 
(2, (SELECT id FROM permissions WHERE code = 'delete'), 
 (SELECT id FROM resources WHERE code = 'products'), FALSE);