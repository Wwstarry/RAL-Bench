import json
import pytest

from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select


def test_model_required_optional_defaults_and_serialization():
    class M(SQLModel):
        a: int
        b: int = 1
        c: str | None
        d: int | None
        e: int = Field(default_factory=lambda: 7)

    m = M(a="3", c=None, d="4")
    assert m.a == 3
    assert m.b == 1
    assert m.c is None
    assert m.d == 4
    assert m.e == 7

    d = m.dict()
    assert d == {"a": 3, "b": 1, "c": None, "d": 4, "e": 7}
    js = m.json()
    assert json.loads(js) == d

    with pytest.raises(TypeError):
        M(c="x", d=None)


def test_table_create_insert_select_where_refresh_update():
    class Hero(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        name: str
        age: int | None = None
        active: bool = True

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        h1 = Hero(name="Spider-Boy", age=None, active=True)
        h2 = Hero(name="Daredevil", age=33, active=False)
        session.add(h1)
        session.add(h2)
        session.commit()

        assert h1.id is not None and h2.id is not None
        assert h1.id < h2.id

        # where
        res = session.exec(select(Hero).where(Hero.name == "Daredevil")).one()
        assert isinstance(res, Hero)
        assert res.name == "Daredevil"
        assert res.age == 33
        assert res.active is False

        # IS NULL
        res2 = session.exec(select(Hero).where(Hero.age == None)).one()  # noqa: E711
        assert res2.name == "Spider-Boy"

        # refresh (and update)
        h2.name = "DD"
        session.add(h2)
        session.commit()
        session.refresh(h2)
        assert h2.name == "DD"

        # query compatibility
        names = [h.name for h in session.query(Hero).filter(Hero.active == True).all()]  # noqa: E712
        assert names == ["Spider-Boy"]


def test_relationship_ignored_by_columns_and_dict():
    class Team(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        name: str

    class Player(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        name: str
        team_id: int | None = None
        team: Team | None = Relationship(back_populates="players")

    # relationship shouldn't become a DB column
    assert "team" in Player.__relationship_fields__
    assert "team" not in [c.name for c in Player.__table__.columns]

    p = Player(name="A", team_id=None)
    assert p.dict() == {"id": None, "name": "A", "team_id": None}