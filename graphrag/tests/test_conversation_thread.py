import time
import pytest
from eleutheria_graphrag.services.graphrag_service import ConversationThread, ThreadManager


def test_create_thread():
    mgr = ThreadManager(ttl_seconds=300)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    assert thread.thread_id
    assert thread.model == "gemini-3.1-pro"
    assert thread.turns == []


def test_get_thread():
    mgr = ThreadManager(ttl_seconds=300)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    retrieved = mgr.get_thread(thread.thread_id)
    assert retrieved is thread


def test_get_nonexistent_thread_returns_none():
    mgr = ThreadManager(ttl_seconds=300)
    assert mgr.get_thread("nonexistent") is None


def test_thread_ttl_expiry():
    mgr = ThreadManager(ttl_seconds=0)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    time.sleep(0.01)
    mgr.cleanup_expired()
    assert mgr.get_thread(thread.thread_id) is None


def test_touch_resets_ttl():
    mgr = ThreadManager(ttl_seconds=1)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    time.sleep(0.5)
    mgr.touch(thread.thread_id)
    time.sleep(0.7)
    mgr.cleanup_expired()
    assert mgr.get_thread(thread.thread_id) is not None
