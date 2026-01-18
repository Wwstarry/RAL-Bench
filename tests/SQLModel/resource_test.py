import os
import sys
import time
from pathlib import Path
from typing import Optional

import psutil

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
)

# 关键：在这里清空全局 MetaData，避免和其他测试文件里定义的表冲突
SQLModel.metadata.clear()


class Hero(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


def test_memory_usage_for_bulk_insert(tmp_path: Path):
    db_path = tmp_path / "resource.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

    process = psutil.Process()
    base = process.memory_info().rss

    N = 5000
    with Session(engine) as session:
        for i in range(N):
            hero = Hero(
                name=f"Hero{i}",
                secret_name=f"Secret{i}",
                age=i % 80,
            )
            session.add(hero)
        session.commit()

    time.sleep(0.5)
    used = process.memory_info().rss - base

    # 先用比较宽松的上限，后面可以根据 baseline 再调
    assert used < 300 * 1024 * 1024  # 300MB
