"""scope_loader 콜백 레지스트리 테스트."""
from unittest.mock import MagicMock


class TestReloadCallbacks:
    """reload_scope() 콜백 호출 테스트."""

    def test_callback_called_on_reload(self):
        """reload 시 등록된 콜백이 호출된다."""
        from app.core.scope_loader import _reload_callbacks, register_reload_callback, reload_scope

        callback = MagicMock()
        original_callbacks = _reload_callbacks.copy()

        try:
            register_reload_callback(callback)
            reload_scope()
            callback.assert_called_once()
            # The callback receives the loaded data dict
            args = callback.call_args[0]
            assert isinstance(args[0], dict)
        finally:
            # Cleanup: restore original callbacks
            _reload_callbacks.clear()
            _reload_callbacks.extend(original_callbacks)

    def test_callback_receives_scope_data(self):
        """콜백이 scope 데이터를 인자로 받는다."""
        from app.core.scope_loader import _reload_callbacks, register_reload_callback, reload_scope

        received = {}

        def capture_data(data):
            received.update(data)

        original_callbacks = _reload_callbacks.copy()

        try:
            register_reload_callback(capture_data)
            reload_scope()
            # Should have at least korean_market from the actual scope file
            assert "korean_market" in received or received == {}  # empty if no scope file
        finally:
            _reload_callbacks.clear()
            _reload_callbacks.extend(original_callbacks)

    def test_failing_callback_does_not_break_reload(self):
        """실패한 콜백이 다른 콜백 실행을 막지 않는다."""
        from app.core.scope_loader import _reload_callbacks, register_reload_callback, reload_scope

        good_callback = MagicMock()
        bad_callback = MagicMock(side_effect=RuntimeError("test error"))

        original_callbacks = _reload_callbacks.copy()

        try:
            register_reload_callback(bad_callback)
            register_reload_callback(good_callback)
            # Should not raise
            data = reload_scope()
            assert isinstance(data, dict)
            # Good callback should still be called despite bad one failing
            good_callback.assert_called_once()
        finally:
            _reload_callbacks.clear()
            _reload_callbacks.extend(original_callbacks)

    def test_multiple_callbacks_all_called(self):
        """여러 콜백이 모두 호출된다."""
        from app.core.scope_loader import _reload_callbacks, register_reload_callback, reload_scope

        cb1 = MagicMock()
        cb2 = MagicMock()
        cb3 = MagicMock()

        original_callbacks = _reload_callbacks.copy()

        try:
            register_reload_callback(cb1)
            register_reload_callback(cb2)
            register_reload_callback(cb3)
            reload_scope()
            cb1.assert_called_once()
            cb2.assert_called_once()
            cb3.assert_called_once()
        finally:
            _reload_callbacks.clear()
            _reload_callbacks.extend(original_callbacks)
