import pytest

from config import settings


@pytest.fixture(autouse=True)
def use_test_provider(monkeypatch):
    """Use only the testing provider from .env (TEST_CHAT_PROVIDER) instead of the priority list.

    autouse=True applies this fixture to every test without naming it. Tests can still
    set their own priority, which replaces this one. monkeypatch puts the original back
    after each test. If the testing provider fails, the tests fail: fix it or choose
    another one in .env, then run the tests again.
    """
    monkeypatch.setattr(settings, "chat_provider_priority", [settings.test_chat_provider])
