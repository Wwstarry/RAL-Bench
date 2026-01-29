import dataset


def test_transactions_rollback_and_commit_visibility():
    db = dataset.connect("sqlite:///:memory:")
    t = db["tx"]

    db.begin()
    t.insert({"name": "a"})
    assert t.count() == 1  # visible inside tx
    db.rollback()
    assert t.count() == 0  # not visible after rollback

    db.begin()
    t.insert_many([{"name": "b"}, {"name": "c"}], chunk_size=1)
    db.commit()
    assert t.count() == 2


def test_transactions_with_schema_change_inside_begin():
    db = dataset.connect("sqlite:///:memory:")
    t = db["sch"]

    db.begin()
    # forces ALTER TABLE while "in transaction"
    t.insert({"newcol": "x"})
    assert t.count() == 1
    db.rollback()
    # insert should be rolled back even though DDL occurred
    assert t.count() == 0


def test_indexes_create_and_has_index_order_sensitive():
    db = dataset.connect("sqlite:///:memory:")
    t = db["idx"]
    t.insert_many([{"name": "a", "age": 1}, {"name": "b", "age": 2}])

    assert not t.has_index("name")
    t.create_index("name")
    assert t.has_index("name")

    assert not t.has_index(["name", "age"])
    t.create_index(["name", "age"])
    assert t.has_index(["name", "age"])
    assert not t.has_index(["age", "name"])


def test_database_query_named_params():
    db = dataset.connect("sqlite:///:memory:")
    t = db["q"]
    t.insert_many([{"name": "a"}, {"name": "b"}])

    rows = list(db.query('SELECT name FROM "q" WHERE name=:name', name="a"))
    assert rows == [{"name": "a"}]