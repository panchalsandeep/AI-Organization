from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseConnector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify the API tokens or keys are valid."""
        pass

    @abstractmethod
    def sync_data(self) -> List[Dict[str, Any]]:
        """Fetch remote data and return as list of dict records."""
        pass
