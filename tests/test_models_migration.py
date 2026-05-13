from sqlalchemy import inspect, select

from memoria.infrastructure.db.models import RawEntry
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db


def test_initial_schema_creates_core_tables(tmp_path):
    db_path = tmp_path / "memoria.db"
    engine = create_engine_for_path(db_path)

    init_db(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {
        "raw_entries",
        "memory_events",
        "memory_issues",
        "issue_comments",
        "issue_links",
        "memory_chains",
        "chain_memberships",
        "proposals",
        "patch_records",
        "llm_jobs",
        "sleep_reports",
        "attachments",
        "import_audits",
    }.issubset(table_names)


def test_raw_entry_defaults_to_pending_processing(tmp_path):
    engine = create_engine_for_path(tmp_path / "memoria.db")
    init_db(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        raw = RawEntry(content="hello")
        session.add(raw)
        session.commit()

    with session_factory() as session:
        saved = session.scalars(select(RawEntry)).one()
        assert saved.processing_state == "pending_processing"
        assert saved.content == "hello"
