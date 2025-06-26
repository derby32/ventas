import os
import db


def setup_module():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    db.add_role("cajero")
    db.add_user("juan", "cajero", "pass")
    db.add_store("barra1")
    db.add_item("gin", "liters")
    db.set_inventory("barra1", "gin", 10.0)
    db.add_product("gin-tonic", 5.0)
    db.add_recipe("gin-tonic", "gin", 0.05)


def test_sale_and_delivery():
    code = "deadbeef"
    db.create_sale("gin-tonic", "barra1", code)
    assert db.mark_delivered(code)


def test_authenticate():
    assert db.authenticate("admin", "admin")
    assert db.authenticate("juan", "pass")
    assert not db.authenticate("juan", "wrong")


def test_session_cycle():
    token = "abcd"
    db.create_session("juan", token)
    assert db.get_user_by_session(token) == "juan"
    db.delete_session(token)
    assert db.get_user_by_session(token) is None

