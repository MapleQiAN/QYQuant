import pytest


def test_execute_strategy_requires_e2b_outside_test_env(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.delenv('E2B_API_KEY', raising=False)
    monkeypatch.setattr('app.services.sandbox.E2BSandbox', None)

    from app.services.sandbox import SandboxService
    from app.strategy_runtime.errors import StrategyRuntimeError

    service = SandboxService()

    with pytest.raises(StrategyRuntimeError) as exc_info:
        service.execute_strategy(
            code='class Strategy:\n    def on_bar(self, ctx, bar):\n        return None\n',
            market_data={"symbol": "BTCUSDT", "bars": []},
            params={},
            metadata={"callable_name": "Strategy"},
        )

    assert exc_info.value.message == 'sandbox_unavailable'


def test_execute_strategy_replenishes_remote_warm_pool(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('E2B_API_KEY', 'sandbox-key')
    monkeypatch.setenv('E2B_WARM_POOL_SIZE', '2')

    from app.services.sandbox import SandboxService

    created = []

    class FakeExecution:
        text = '__QYQUANT_RESULT__={"ok": true, "result": {"trades": [], "logs": ["remote-ok"]}}'

    class FakeSandbox:
        def __init__(self, api_key=None, timeout=None, envs=None):
            self.api_key = api_key
            self.timeout = timeout
            self.envs = envs
            self.run_calls = []
            self.closed = False
            created.append(self)

        def run_code(self, script, timeout=None, request_timeout=None, envs=None):
            self.run_calls.append(
                {
                    "script": script,
                    "timeout": timeout,
                    "request_timeout": request_timeout,
                    "envs": envs,
                }
            )
            return FakeExecution()

        def kill(self):
            self.closed = True

    service = SandboxService(sandbox_cls=FakeSandbox)

    result = service.execute_strategy(
        code='class Strategy:\n    def on_bar(self, ctx, bar):\n        return None\n',
        market_data={"symbol": "BTCUSDT", "bars": []},
        params={},
        metadata={"callable_name": "Strategy", "timeout_seconds": 300},
    )

    assert result["logs"] == ["remote-ok"]
    assert len(created) == 2
    assert len(service._pool) == 2
    assert all(item.api_key == 'sandbox-key' for item in created)
    assert all(item.envs == {"QYQUANT_SANDBOX": "1"} for item in created)
    executed = [item for item in created if item.run_calls]
    assert len(executed) == 1
    assert executed[0].run_calls[0]["timeout"] == 300
    assert executed[0].run_calls[0]["request_timeout"] == 330
