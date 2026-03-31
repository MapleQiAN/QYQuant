import inspect
import json
import os
import threading

from ..backtest.sandbox_template import RESULT_PREFIX, build_sandbox_script
from ..strategy_runtime.errors import StrategyRuntimeError
from ..strategy_runtime.sandbox import run_strategy_in_subprocess

try:
    from e2b_code_interpreter import Sandbox as E2BSandbox
except ImportError:  # pragma: no cover
    E2BSandbox = None


DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_POOL_SIZE = 1
_DEFAULT_SANDBOX_CLS = object()
LOCAL_SANDBOX_MODE = 'local'


class SandboxService:
    def __init__(self, sandbox_cls=_DEFAULT_SANDBOX_CLS):
        self.sandbox_cls = E2BSandbox if sandbox_cls is _DEFAULT_SANDBOX_CLS else sandbox_cls
        self.api_key = os.getenv('E2B_API_KEY')
        self.sandbox_mode = (os.getenv('BACKTEST_SANDBOX_MODE') or '').strip().lower()
        self.pool_size = max(int(os.getenv('E2B_WARM_POOL_SIZE', DEFAULT_POOL_SIZE)), 0)
        self._pool = []
        self._lock = threading.Lock()

    def execute_strategy(self, code, market_data, params, metadata=None):
        execution_metadata = dict(metadata or {})
        timeout_seconds = int(execution_metadata.get('timeout_seconds') or DEFAULT_TIMEOUT_SECONDS)

        if self._should_use_local():
            outcome = self._execute_locally(code, market_data, params, execution_metadata, timeout_seconds)
            return outcome

        self._ensure_remote_available()
        self._warm_pool_if_needed(timeout_seconds)
        sandbox = self._acquire(timeout_seconds)
        keep_warm = self.pool_size > 0
        try:
            script = build_sandbox_script(code, market_data, params, execution_metadata)
            execution = sandbox.run_code(
                script,
                timeout=timeout_seconds,
                request_timeout=timeout_seconds + 30,
                envs={"QYQUANT_SANDBOX": "1"},
            )
            payload = self._parse_execution(execution)
            if not payload.get('ok'):
                error = payload.get('error') or 'sandbox_execution_failed'
                if 'timeout' in error.lower():
                    raise StrategyRuntimeError('strategy_timeout', {"reason": error})
                raise StrategyRuntimeError('strategy_runtime_error', {"reason": error})
            return payload.get('result') or {"trades": [], "logs": []}
        except Exception as exc:
            keep_warm = False
            if isinstance(exc, StrategyRuntimeError):
                raise
            if 'timeout' in str(exc).lower():
                raise StrategyRuntimeError('strategy_timeout', {"reason": str(exc)}) from exc
            raise StrategyRuntimeError('sandbox_execution_failed', {"reason": str(exc)}) from exc
        finally:
            self._release(sandbox, keep_warm)

    def _execute_locally(self, code, market_data, params, metadata, timeout_seconds):
        outcome = run_strategy_in_subprocess(
            symbol=(market_data or {}).get('symbol'),
            source=code,
            callable_name=metadata.get('callable_name'),
            bars=(market_data or {}).get('bars') or [],
            params=params,
            timeout_seconds=timeout_seconds,
        )
        return {
            "trades": outcome.get('trades') or [],
            "logs": outcome.get('logs') or [],
        }

    @staticmethod
    def _is_test_env():
        return os.getenv('FLASK_ENV', '').lower() in {'test', 'testing'}

    def _should_use_local(self):
        return self._is_test_env() or self.sandbox_mode == LOCAL_SANDBOX_MODE

    def _ensure_remote_available(self):
        if self.sandbox_cls is None:
            raise StrategyRuntimeError('sandbox_unavailable', {"reason": "e2b_code_interpreter_not_installed"})
        if not self.api_key:
            raise StrategyRuntimeError('sandbox_unavailable', {"reason": "missing_e2b_api_key"})

    def _should_use_remote(self):
        return not self._should_use_local()

    def _warm_pool_if_needed(self, timeout_seconds):
        if not self._should_use_remote():
            return
        self._ensure_remote_available()
        with self._lock:
            while len(self._pool) < self.pool_size:
                self._pool.append(self._create_remote_sandbox(timeout_seconds))

    def _acquire(self, timeout_seconds):
        with self._lock:
            if self._pool:
                return self._pool.pop()
        return self._create_remote_sandbox(timeout_seconds)

    def _release(self, sandbox, keep_warm):
        if sandbox is None:
            return
        with self._lock:
            if keep_warm and len(self._pool) < self.pool_size:
                self._pool.append(sandbox)
                return
        self._close_sandbox(sandbox)

    def _create_remote_sandbox(self, timeout_seconds):
        if not self.sandbox_cls:
            raise RuntimeError('e2b_code_interpreter is not installed')

        create = getattr(self.sandbox_cls, 'create', None)
        factory = create if callable(create) else self.sandbox_cls
        kwargs = {}
        for name, value in {
            'api_key': self.api_key,
            'timeout': timeout_seconds,
            'envs': {"QYQUANT_SANDBOX": "1"},
        }.items():
            if self._accepts_keyword(factory, name):
                kwargs[name] = value
        return factory(**kwargs)

    @staticmethod
    def _accepts_keyword(factory, name):
        try:
            signature = inspect.signature(factory)
        except (TypeError, ValueError):
            return False
        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                return True
        return name in signature.parameters

    @staticmethod
    def _parse_execution(execution):
        text = getattr(execution, 'text', None)
        if text is None:
            text = str(execution)
        for line in reversed(str(text).splitlines()):
            if line.startswith(RESULT_PREFIX):
                return json.loads(line[len(RESULT_PREFIX):])
        raise StrategyRuntimeError('sandbox_execution_failed', {"reason": "missing_result_payload"})

    @staticmethod
    def _close_sandbox(sandbox):
        for method_name in ('kill', 'close'):
            method = getattr(sandbox, method_name, None)
            if callable(method):
                method()
                return


_sandbox_service = SandboxService()


def get_sandbox_service():
    return _sandbox_service


def execute_strategy(code, market_data, params, metadata=None):
    return get_sandbox_service().execute_strategy(code, market_data, params, metadata=metadata)
