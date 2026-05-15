"""Smoke import tests (no external services required)."""


def test_indexer_app_import():
    from services.indexer.main import app

    assert app.title == "Indexer"


def test_retriever_app_import():
    from services.retriever.main import app

    assert app.title == "Retriever"


def test_qa_agent_app_import():
    from services.qa_agent.main import app

    assert app.title == "QA Agent"
