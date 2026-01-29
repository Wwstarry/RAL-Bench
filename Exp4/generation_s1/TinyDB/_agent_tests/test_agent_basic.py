import os
import pytest

from tinydb import TinyDB, where, JSONStorage


def test_jsonstorage_missing_file_read_returns_empty(tmp_path):
    p = tmp_path / "db.json"
    s = JSONStorage(p)
    assert s.read() == {}


def test_jsonstorage_roundtrip(tmp_path):
    p = tmp_path / "db.json"
    s = JSONStorage(p)
    s.write({"a": {"1": {"_id": 1, "x": 2}}})
    assert s.read()["a"]["1"]["x"] == 2


def test_jsonstorage_invalid_json_raises(tmp_path):
    p = tmp_path / "db.json"
    p.write_text("{not valid", encoding="utf-8")
    s = JSONStorage(p)
    with pytest.raises(ValueError):
        s.read()


def test_insert_and_persist_reopen(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    id1 = t.insert({"title": "A"})
    id2 = t.insert({"title": "B"})
    assert (id1, id2) == (1, 2)
    db.close()

    db2 = TinyDB(p)
    t2 = db2.table("tasks")
    assert t2.get(id1)["title"] == "A"
    assert t2.get(id2)["title"] == "B"


def test_insert_multiple_and_all_have_ids(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    ids = t.insert_multiple([{"title": "A"}, {"title": "B"}])
    assert ids == [1, 2]
    docs = t.all()
    assert sorted([d["_id"] for d in docs]) == [1, 2]


def test_get_missing_returns_none(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    assert t.get(9999) is None


def test_update_by_doc_id_and_query_and_errors(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    a = t.insert({"title": "A", "status": "todo"})
    b = t.insert({"title": "B", "status": "todo"})

    assert t.update({"status": "doing"}, doc_ids=[a]) == 1
    assert t.get(a)["status"] == "doing"
    assert t.get(b)["status"] == "todo"

    assert t.update({"status": "done"}, query=(where("status") == "todo")) == 1
    assert t.get(b)["status"] == "done"

    with pytest.raises(ValueError):
        t.update({"x": 1})

    with pytest.raises(ValueError):
        t.update({"x": 1}, doc_ids=[a], query=(where("title") == "A"))


def test_remove_by_doc_id_and_query_and_errors(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    a = t.insert({"title": "A", "status": "todo"})
    b = t.insert({"title": "B", "status": "todo"})
    c = t.insert({"title": "C", "status": "done"})

    assert t.remove(doc_ids=[a]) == 1
    assert t.get(a) is None
    assert t.count() == 2

    assert t.remove(query=(where("status") == "todo")) == 1
    assert t.get(b) is None
    assert t.count() == 1

    with pytest.raises(ValueError):
        t.remove()

    with pytest.raises(ValueError):
        t.remove(doc_ids=[c], query=(where("status") == "done"))


def test_purge_drop_table_tables_listing(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    t.insert({"title": "A"})
    db.table("other").insert({"x": 1})

    assert db.tables() == ["other", "tasks"]

    t.purge()
    assert t.count() == 0
    assert "tasks" in db.tables()

    db.drop_table("tasks")
    assert "tasks" not in db.tables()
    assert "other" in db.tables()


def test_queries_nested_exists_composition_missing_field_semantics(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    t = db.table("tasks")
    t.insert({"title": "A", "status": "todo", "meta": {"priority": 1}})
    t.insert({"title": "B", "status": "done"})
    t.insert({"title": "C", "status": "todo", "meta": {"priority": 2}})

    q1 = (where("status") == "todo") & (where("meta")["priority"] == 1)
    res = t.search(q1)
    assert [d["title"] for d in res] == ["A"]

    assert t.contains(where("meta")["priority"].exists()) is True
    # Missing field comparisons should be False (so only 2 match priority>=1, not doc without meta)
    assert t.count(where("meta")["priority"] >= 1) == 2

    q_not_done = ~ (where("status") == "done")
    assert t.count(q_not_done) == 2

    q_or = (where("title") == "B") | (where("meta")["priority"] == 2)
    titles = sorted([d["title"] for d in t.search(q_or)])
    assert titles == ["B", "C"]


def test_task_helpers_create_and_analytics(tmp_path):
    p = tmp_path / "db.json"
    db = TinyDB(p)
    tasks = db.table("tasks")

    tasks.create_task(title="A", project="P1", status="todo", estimate=3)
    tasks.create_task(title="B", project="P1", status="done")
    tasks.create_task(title="C", project="P2", status="doing")
    tasks.create_task(title="D")  # no project, default todo

    counts = tasks.unfinished_per_project()
    assert counts["P1"] == 1
    assert counts["P2"] == 1
    assert counts["(none)"] == 1