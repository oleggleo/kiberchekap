from abc import ABC, abstractmethod
from models import Lead


class BaseNotifier(ABC):

    @abstractmethod
    def can_notify(self, lead: Lead) -> bool:
        pass

    @abstractmethod
    def send(self, lead: Lead, event: str) -> None:
        pass

    def notify(self, lead: Lead, event: str) -> None:
        if self.can_notify(lead):
            self.send(lead, event)