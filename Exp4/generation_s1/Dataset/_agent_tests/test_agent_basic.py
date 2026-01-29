import dataset


def test_connect_and_lazy_table_and_columns():
    db = dataset.connect("sqlite:///:memory:")
    t = db["people"]
    assert "id" in t.columns  # created on access

    t.insert({"name": "a"})
    assert "name" in t.columns

    t.insert({"name": "b", "age": 3})
    cols = set(t.columns)
    assert {"id", "name", "age"}.issubset(cols)

    # first row should have age NULL/None
    r = t.find_one(name="a")
    assert r["name"] == "a"
    assert r.get("age") is None


def test_find_filters_in_and_null():
    db = dataset.connect("sqlite:///:memory:")
    t = db["t"]
    t.insert_many([{"name": "a", "age": 1}, {"name": "b", "age": None}, {"name": "c", "age": 2}])

    assert t.count() == 3
    assert t.count(name="a") == 1
    assert t.count(name=["a", "c"]) == 2
    assert t.count(age=None) == 1

    names = sorted([r["name"] for r in t.find(name=["a", "c"])])
    assert names == ["a", "c"]


def test_update_upsert_delete():
    db = dataset.connect("sqlite:///:memory:")
    t = db["items"]
    t.insert({"sku": "x", "price": 10})
    assert t.find_one(sku="x")["price"] == 10

    n = t.update({"sku": "x", "price": 11, "desc": "ok"}, keys="sku")
    assert n == 1
    r = t.find_one(sku="x")
    assert r["price"] == 11
    assert r["desc"] == "ok"

    # upsert updates
    u = t.upsert({"sku": "x", "price": 12}, keys="sku")
    assert t.find_one(sku="x")["price"] == 12

    # upsert inserts
    u2 = t.upsert({"sku": "y", "price": 5}, keys="sku")
    assert t.count() == 2
    assert t.find_one(sku="y")["price"] == 5

    d = t.delete(sku="x")
    assert d == 1
    assert t.find_one(sku="x") is None