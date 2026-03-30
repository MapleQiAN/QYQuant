from abc import ABC, abstractmethod


class MarketDataAdapter(ABC):
    @abstractmethod
    def get_bars(self, symbol, interval, start_time=None, end_time=None, limit=None):
        raise NotImplementedError

    def get_latest_quote(self, symbol):
        raise NotImplementedError
