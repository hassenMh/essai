from app.database.connection import db


SCHEMA_SQL = """
-- Users
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    full_name   TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('admin','cashier')),
    email       TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    color       TEXT    DEFAULT '#4CAF50',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    phone       TEXT,
    email       TEXT,
    address     TEXT,
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode         TEXT    UNIQUE,
    name            TEXT    NOT NULL,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    supplier_id     INTEGER REFERENCES suppliers(id)  ON DELETE SET NULL,
    purchase_price  REAL    NOT NULL DEFAULT 0,
    sale_price      REAL    NOT NULL DEFAULT 0,
    stock_quantity  REAL    NOT NULL DEFAULT 0,
    min_stock       REAL    NOT NULL DEFAULT 5,
    unit_type       TEXT    NOT NULL DEFAULT 'piece' CHECK(unit_type IN ('piece','kg','litre')),
    expiry_date     TEXT,
    description     TEXT,
    image_path      TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Sales
CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    subtotal        REAL    NOT NULL DEFAULT 0,
    discount        REAL    NOT NULL DEFAULT 0,
    tax             REAL    NOT NULL DEFAULT 0,
    total           REAL    NOT NULL DEFAULT 0,
    payment_method  TEXT    NOT NULL DEFAULT 'cash' CHECK(payment_method IN ('cash','card','other')),
    amount_paid     REAL    NOT NULL DEFAULT 0,
    change_given    REAL    NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'completed' CHECK(status IN ('completed','cancelled','refunded')),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Sale Items
CREATE TABLE IF NOT EXISTS sale_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    REAL    NOT NULL,
    unit_price  REAL    NOT NULL,
    discount    REAL    NOT NULL DEFAULT 0,
    total       REAL    NOT NULL
);

-- Stock Movements
CREATE TABLE IF NOT EXISTS stock_movements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    movement_type   TEXT    NOT NULL CHECK(movement_type IN ('in','out','adjustment','return')),
    quantity        REAL    NOT NULL,
    reference       TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    category    TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Product Returns
CREATE TABLE IF NOT EXISTS product_returns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER REFERENCES sales(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    quantity    REAL    NOT NULL,
    amount      REAL    NOT NULL,
    reason      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- User Logs
CREATE TABLE IF NOT EXISTS user_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    action      TEXT    NOT NULL,
    details     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT    NOT NULL UNIQUE,
    value       TEXT,
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_barcode    ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_category   ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale     ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sales_created       ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_stock_movements_prod ON stock_movements(product_id);
"""

DEFAULT_CATEGORIES = [
    ("Produits laitiers",  "Lait, fromage, beurre",    "#2196F3"),
    ("Yaourts",            "Yaourts et desserts",       "#9C27B0"),
    ("Boulangerie",        "Pain et viennoiseries",     "#FF9800"),
    ("Pâtisseries",        "Gâteaux et douceurs",       "#E91E63"),
    ("Boissons",           "Eau, jus, sodas",           "#00BCD4"),
    ("Fruits et légumes",  "Produits frais",            "#4CAF50"),
    ("Produits ménagers",  "Entretien et nettoyage",    "#607D8B"),
    ("Épicerie",           "Conserves et condiments",   "#FF5722"),
    ("Autres",             "Divers",                    "#9E9E9E"),
]

DEFAULT_SETTINGS = [
    ("store_name",    "Mon Magasin"),
    ("store_address", "Adresse"),
    ("store_phone",   "+216 XX XXX XXX"),
    ("currency",      "TND"),
    ("tax_rate",      "0"),
    ("theme",         "dark"),
    ("low_stock_threshold", "5"),
    ("receipt_footer", "Merci pour votre visite !"),
]


def init_schema():
    conn = db.get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    _seed_defaults()


def _seed_defaults():
    existing = db.fetchone("SELECT id FROM users LIMIT 1")
    if existing:
        return

    import bcrypt
    pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    db.execute(
        "INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
        ("admin", pw, "Administrateur", "admin"),
    )

    for name, desc, color in DEFAULT_CATEGORIES:
        db.execute(
            "INSERT OR IGNORE INTO categories (name, description, color) VALUES (?,?,?)",
            (name, desc, color),
        )

    for key, val in DEFAULT_SETTINGS:
        db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)",
            (key, val),
        )
