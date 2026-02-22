-- Step-25: bootstrap admin user
-- Переменная :admin_password_hash передаётся через psql -v

INSERT INTO admin_users(email, full_name, is_active, created_at, password_hash)
VALUES ('admin@example.com', 'System Admin', true, now(), :'admin_password_hash')
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active,
    password_hash = EXCLUDED.password_hash;