import pytest

from app.strategy_runtime.errors import StrategyRuntimeError


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


def test_execute_strategy_timeout_raises_strategy_timeout(monkeypatch):
    """AC#4: 超时后任务状态更新为 timeout"""
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('E2B_API_KEY', 'sandbox-key')
    monkeypatch.setenv('E2B_WARM_POOL_SIZE', '0')

    from app.services.sandbox import SandboxService

    class FakeSandbox:
        def __init__(self, **kwargs):
            pass

        def run_code(self, script, **kwargs):
            raise TimeoutError("Execution timeout after 300s")

        def kill(self):
            pass

    service = SandboxService(sandbox_cls=FakeSandbox)

    with pytest.raises(StrategyRuntimeError) as exc_info:
        service.execute_strategy(
            code='class Strategy:\n    pass\n',
            market_data={"symbol": "BTCUSDT", "bars": []},
            params={},
        )

    assert exc_info.value.message == 'strategy_timeout'


def test_execute_strategy_destroys_sandbox_after_execution(monkeypatch):
    """AC#1: 执行完毕后沙箱销毁，明文不落盘"""
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('E2B_API_KEY', 'sandbox-key')
    monkeypatch.setenv('E2B_WARM_POOL_SIZE', '0')

    from app.services.sandbox import SandboxService

    class FakeExecution:
        text = '__QYQUANT_RESULT__={"ok": true, "result": {"trades": [], "logs": []}}'

    class FakeSandbox:
        def __init__(self, **kwargs):
            self.killed = False

        def run_code(self, script, **kwargs):
            return FakeExecution()

        def kill(self):
            self.killed = True

    service = SandboxService(sandbox_cls=FakeSandbox)
    service.execute_strategy(
        code='class Strategy:\n    pass\n',
        market_data={"symbol": "BTCUSDT", "bars": []},
        params={},
    )

    # pool_size=0 → sandbox should be destroyed, not kept
    assert len(service._pool) == 0


def test_execute_strategy_destroys_sandbox_on_error(monkeypatch):
    """沙箱执行失败时也必须销毁沙箱"""
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('E2B_API_KEY', 'sandbox-key')
    monkeypatch.setenv('E2B_WARM_POOL_SIZE', '1')

    from app.services.sandbox import SandboxService

    destroyed = []

    class FakeSandbox:
        def __init__(self, **kwargs):
            pass

        def run_code(self, script, **kwargs):
            raise RuntimeError("unexpected error")

        def kill(self):
            destroyed.append(True)

    service = SandboxService(sandbox_cls=FakeSandbox)

    with pytest.raises(StrategyRuntimeError) as exc_info:
        service.execute_strategy(
            code='class Strategy:\n    pass\n',
            market_data={"symbol": "BTCUSDT", "bars": []},
            params={},
        )

    assert exc_info.value.message == 'sandbox_execution_failed'
    # On error, keep_warm=False → sandbox destroyed, not returned to pool
    assert len(service._pool) == 0
    assert len(destroyed) == 1


def test_execute_strategy_requires_api_key_outside_test_env(monkeypatch):
    """AC#2/AC#3: 非测试环境必须通过 E2B 远程沙箱执行（网络隔离+文件系统隔离由平台保证）"""
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.delenv('E2B_API_KEY', raising=False)

    from app.services.sandbox import SandboxService

    class FakeSandboxCls:
        pass

    service = SandboxService(sandbox_cls=FakeSandboxCls)

    with pytest.raises(StrategyRuntimeError) as exc_info:
        service.execute_strategy(
            code='class Strategy:\n    pass\n',
            market_data={"symbol": "BTCUSDT", "bars": []},
            params={},
        )

    assert exc_info.value.message == 'sandbox_unavailable'
    assert exc_info.value.details['reason'] == 'missing_e2b_api_key'
