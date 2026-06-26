"""Basic smoke tests — run with: python -m pytest tests/"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.database.schema import init_schema
from app.controllers.auth_controller import AuthController
from app.controllers.category_controller import CategoryController
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(config, "QR_CODES_DIR", tmp_path / "qr")
    monkeypatch.setattr(config, "PRODUCT_IMAGES_DIR", tmp_path / "img")
    monkeypatch.setattr(config, "RECEIPTS_DIR", tmp_path / "receipts")
    from app.database import connection
    connection.db._initialized = False
    connection.db._local = __import__("threading").local()
    init_schema()
    AuthController.login("admin", "admin123")
    yield
    connection.db.close()


def test_login_success():
    user = AuthController.login("admin", "admin123")
    assert user is not None
    assert user["role"] == "admin"


def test_login_failure():
    user = AuthController.login("admin", "wrongpassword")
    assert user is None


def test_create_category():
    cat_id = CategoryController.create("Test Cat", "desc", "#FF0000")
    assert cat_id > 0
    cats = CategoryController.get_all()
    names = [c["name"] for c in cats]
    assert "Test Cat" in names


def test_create_product():
    cat_id = CategoryController.create("Boissons Test", "test")
    pid = ProductController.create({
        "name": "Eau Minérale",
        "sale_price": 0.500,
        "purchase_price": 0.300,
        "category_id": cat_id,
        "stock_quantity": 100,
        "unit_type": "piece",
    })
    assert pid > 0
    p = ProductController.get_by_id(pid)
    assert p["name"] == "Eau Minérale"
    assert p["stock_quantity"] == 100


def test_create_sale():
    cat_id = CategoryController.create("Test Sale Cat")
    pid = ProductController.create({
        "name": "Produit Test",
        "sale_price": 1.500,
        "stock_quantity": 50,
        "unit_type": "piece",
    })
    sale = SaleController.create_sale(
        [{"product_id": pid, "quantity": 3, "unit_price": 1.500, "discount": 0}],
        "cash", 0, 0, 5.0,
    )
    assert sale["total"] == pytest.approx(4.5, abs=0.001)
    assert sale["change_given"] == pytest.approx(0.5, abs=0.001)

    p_after = ProductController.get_by_id(pid)
    assert p_after["stock_quantity"] == 47


def test_low_stock_alert():
    cat_id = CategoryController.create("Alert Cat")
    ProductController.create({
        "name": "Produit Faible",
        "sale_price": 1.0,
        "stock_quantity": 2,
        "min_stock": 10,
        "unit_type": "piece",
    })
    low = ProductController.get_low_stock()
    names = [p["name"] for p in low]
    assert "Produit Faible" in names
