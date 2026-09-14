from app.core.config import get_settings


def test_settings_demo_defaults():
    s = get_settings()
    assert s.embedding_dimensions == 1536
