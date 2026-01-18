import os
import sys
import time
from pathlib import Path
from typing import Optional

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
)


class Hero(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


def test_bulk_insert_and_query_performance(tmp_path: Path):
    db_path = tmp_path / "perf.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

    N = 3000

    t0 = time.perf_counter()
    with Session(engine) as session:
        for i in range(N):
            hero = Hero(
                name=f"Hero{i}",
                secret_name=f"Secret{i}",
                age=i % 80,
            )
            session.add(hero)
        session.commit()
    t_insert = time.perf_counter() - t0

    t1 = time.perf_counter()
    with Session(engine) as session:
        statement = select(Hero).where(Hero.age >= 18)
        results = list(session.exec(statement))
    t_query = time.perf_counter() - t1

    # 打印方便调试和离线分析
    print(f"[PERF] insert {N} heroes: {t_insert:.4f}s, query: {t_query:.4f}s")
    assert len(results) > 0
