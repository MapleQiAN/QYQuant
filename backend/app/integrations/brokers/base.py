from abc import ABC, abstractmethod


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
