import pytest

from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine_for_path(tmp_path / "test.db")
    init_db(engine)
    return create_session_factory(engine)


@pytest.fixture(autouse=True)
def isolate_config_file(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMORIA_CONFIG", str(tmp_path / "config.toml"))
