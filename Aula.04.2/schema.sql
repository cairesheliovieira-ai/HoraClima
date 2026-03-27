-- ============================================================
-- StoreMaster v2 — Schema SQL
-- Banco de dados: SQLite 3
-- Linguagem: SQL (DDL — Data Definition Language)
-- ============================================================
-- Este arquivo define a estrutura completa do banco de dados.
-- É executado automaticamente na inicialização pelo app.py.
-- ============================================================

-- Tabela de usuários com suporte a múltiplos perfis
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'seller' CHECK(role IN ('admin','seller')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categorias de produtos com cor e ícone personalizados
CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT UNIQUE NOT NULL,
    color TEXT NOT NULL DEFAULT '#6366f1',
    icon  TEXT NOT NULL DEFAULT '📦'
);

-- Catálogo de produtos com preço de custo e estoque mínimo
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    price       REAL    NOT NULL CHECK(price >= 0),
    cost        REAL    NOT NULL DEFAULT 0 CHECK(cost >= 0),
    stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
    min_stock   INTEGER NOT NULL DEFAULT 5  CHECK(min_stock >= 0),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Histórico de vendas vinculado a produtos e usuários
CREATE TABLE IF NOT EXISTS sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    quantity   INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL    NOT NULL CHECK(unit_price >= 0),
    total      REAL    NOT NULL CHECK(total >= 0),
    sold_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimizar consultas frequentes do dashboard
CREATE INDEX IF NOT EXISTS idx_sales_sold_at     ON sales(sold_at);
CREATE INDEX IF NOT EXISTS idx_sales_product     ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
