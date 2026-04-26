from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class BrokerOrderNotSupported(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BrokerOrderRequest:
    client_order_id: str
    symbol: str
    side: str
    quantity: str
    order_type: str = "market"
    limit_price: str | None = None
    time_in_force: str = "day"
    metadata: dict[str, str] = field(default_factory=dict)

    def to_payload(self) -> dict:
        return {
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "time_in_force": self.time_in_force,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class BrokerOrderResponse:
    client_order_id: str
    broker_order_id: str | None
    status: str
    raw_payload: dict = field(default_factory=dict)

    def to_payload(self) -> dict:
        return {
            "client_order_id": self.client_order_id,
            "broker_order_id": self.broker_order_id,
            "status": self.status,
            "raw_payload": dict(self.raw_payload),
        }


@dataclass(frozen=True, slots=True)
class BrokerOrderStatus:
    client_order_id: str | None
    broker_order_id: str
    status: str
    filled_quantity: str | None = None
    filled_avg_price: str | None = None
    raw_payload: dict = field(default_factory=dict)

    def to_payload(self) -> dict:
        return {
            "client_order_id": self.client_order_id,
            "broker_order_id": self.broker_order_id,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "filled_avg_price": self.filled_avg_price,
            "raw_payload": dict(self.raw_payload),
        }


@dataclass(frozen=True, slots=True)
class BrokerFill:
    broker_order_id: str
    symbol: str
    side: str
    price: str
    quantity: str
    filled_at: int | None = None
    raw_payload: dict = field(default_factory=dict)

    def to_payload(self) -> dict:
        return {
            "broker_order_id": self.broker_order_id,
            "symbol": self.symbol,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "filled_at": self.filled_at,
            "raw_payload": dict(self.raw_payload),
        }


class BrokerAccountAdapter(ABC):
    @abstractmethod
    def validate_credentials(self, config):
        raise NotImplementedError

    @abstractmethod
    def get_account_summary(self, integration):
        raise NotImplementedError

    @abstractmethod
    def get_positions(self, integration):
        raise NotImplementedError

    def place_order(self, integration, order_request: BrokerOrderRequest) -> BrokerOrderResponse:
        raise BrokerOrderNotSupported(f"{self.__class__.__name__} does not support live orders")

    def cancel_order(self, integration, broker_order_id: str) -> dict:
        raise BrokerOrderNotSupported(f"{self.__class__.__name__} does not support live order cancellation")

    def get_order(self, integration, broker_order_id: str) -> BrokerOrderStatus:
        raise BrokerOrderNotSupported(f"{self.__class__.__name__} does not support live order status")

    def list_orders(self, integration, since=None) -> list[BrokerOrderStatus]:
        raise BrokerOrderNotSupported(f"{self.__class__.__name__} does not support live order listing")

    def get_fills(self, integration, since=None) -> list[BrokerFill]:
        raise BrokerOrderNotSupported(f"{self.__class__.__name__} does not support live fills")
