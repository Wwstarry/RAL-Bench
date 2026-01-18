from typing import Optional
from pathlib import Path
import os
import sys

import pytest

# Resolve project root and choose which repository to test
# (reference vs generated) based on the SQLMODEL_TARGET env var.
ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("SQLMODEL_TARGET", "generated").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "SQLModel"
else:
    REPO_ROOT = ROOT / "generation" / "SQLModel"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlmodel import (  # type: ignore  # noqa: E402
    SQLModel,
    Field,
    Session,
    create_engine,
    select,
    Relationship,
)

# Ensure the global metadata is clean before registering test models
SQLModel.metadata.clear()


class Team(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    headquarters: Optional[str] = None

    heroes: list["Hero"] = Relationship(back_populates="team")  # type: ignore[valid-type]


class Hero(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    team: Optional["Team"] = Relationship(back_populates="heroes")  # type: ignore[valid-type]


class Item(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="default-name")
    description: Optional[str] = None
    quantity: int = Field(default=0)


@pytest.fixture
def engine(tmp_path: Path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def test_create_and_query_single_table(engine):
    with Session(engine) as session:
        hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
        hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Spider-Boy")
        hero = session.exec(statement).first()

    assert hero is not None
    assert hero.name == "Spider-Boy"
    assert hero.secret_name == "Pedro Parqueador"


def test_update_delete_and_get(engine):
    with Session(engine) as session:
        hero = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=45)
        session.add(hero)
        session.commit()
        session.refresh(hero)
        hero_id = hero.id

        hero.age = 48
        session.add(hero)
        session.commit()

    with Session(engine) as session:
        fetched = session.get(Hero, hero_id)
        assert fetched is not None
        assert fetched.age == 48

        session.delete(fetched)
        session.commit()

    with Session(engine) as session:
        deleted = session.get(Hero, hero_id)
        assert deleted is None


def test_filter_by_foreign_key(engine):
    with Session(engine) as session:
        team = Team(name="Preventers", headquarters="Sharp Tower")
        session.add(team)
        session.commit()
        session.refresh(team)

        hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson", team_id=team.id)
        hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador", team_id=None)
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

        team_id = team.id

    with Session(engine) as session:
        statement = select(Hero).where(Hero.team_id == team_id)
        heroes = session.exec(statement).all()

    assert len(heroes) == 1
    assert heroes[0].name == "Deadpond"


def test_relationship_navigation(engine):
    with Session(engine) as session:
        team = Team(name="Avengers", headquarters="Tower")
        session.add(team)
        session.commit()
        session.refresh(team)

        h1 = Hero(name="Iron Man", secret_name="Tony Stark", team_id=team.id)
        h2 = Hero(name="Captain America", secret_name="Steve Rogers", team_id=team.id)
        session.add(h1)
        session.add(h2)
        session.commit()

        team_id = team.id

    with Session(engine) as session:
        statement = select(Team).where(Team.id == team_id)
        team_obj = session.exec(statement).one()
        heroes = team_obj.heroes

        names = sorted(h.name for h in heroes)
        assert names == ["Captain America", "Iron Man"]

        hero_statement = select(Hero).where(Hero.name == "Iron Man")
        iron_man = session.exec(hero_statement).one()
        assert iron_man.team is not None
        assert iron_man.team.name == "Avengers"


def test_field_defaults_and_nullable(engine):
    with Session(engine) as session:
        item = Item()
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    with Session(engine) as session:
        fetched = session.get(Item, item_id)

    assert fetched is not None
    assert fetched.name == "default-name"
    assert fetched.description is None
    assert fetched.quantity == 0
