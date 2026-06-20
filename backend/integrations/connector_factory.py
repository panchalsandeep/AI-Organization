from typing import Dict, Any, List
from backend.integrations.base_connector import BaseConnector

class SlackConnector(BaseConnector):
    def test_connection(self) -> bool:
        token = self.config.get("bot_token", "")
        return token.startswith("xoxb-") or token == "mock-token"

    def sync_data(self) -> List[Dict[str, Any]]:
        # Fetch channels/history
        return [
            {"id": "msg-slack-1", "channel": "general", "text": "Sprint 3 planning starting", "user": "U123"},
            {"id": "msg-slack-2", "channel": "ops", "text": "Please log latest KPI metrics", "user": "U456"}
        ]

class NotionConnector(BaseConnector):
    def test_connection(self) -> bool:
        api_key = self.config.get("api_key", "")
        return api_key.startswith("secret_") or api_key == "mock-key"

    def sync_data(self) -> List[Dict[str, Any]]:
        # Fetch pages/database
        return [
            {"id": "page-notion-1", "title": "Product Specs", "url": "https://notion.so/specs"},
            {"id": "page-notion-2", "title": "SOC 2 Audit Controls", "url": "https://notion.so/controls"}
        ]

class GoogleDriveConnector(BaseConnector):
    def test_connection(self) -> bool:
        return bool(self.config.get("credentials_json") or self.config.get("api_key"))

    def sync_data(self) -> List[Dict[str, Any]]:
        # Fetch files
        return [
            {"id": "drive-file-1", "name": "Q2 Financial Report.xlsx", "mimeType": "application/vnd.ms-excel"},
            {"id": "drive-file-2", "name": "Meeting Recording.wav", "mimeType": "audio/wav"}
        ]

class GitHubConnector(BaseConnector):
    def test_connection(self) -> bool:
        return bool(self.config.get("personal_access_token") or self.config.get("username"))

    def sync_data(self) -> List[Dict[str, Any]]:
        # Fetch repository info
        return [
            {"id": "gh-issue-1", "repo": "ai-ops-backend", "title": "Implement WebSockets rate limiting", "state": "open"},
            {"id": "gh-pr-2", "repo": "ai-ops-dashboard", "title": "Add collab page design system", "state": "merged"}
        ]

class ConnectorFactory:
    @staticmethod
    def get_connector(integration_type: str, config: Dict[str, Any]) -> BaseConnector:
        types = {
            "slack": SlackConnector,
            "notion": NotionConnector,
            "google_drive": GoogleDriveConnector,
            "github": GitHubConnector
        }
        connector_class = types.get(integration_type.lower())
        if not connector_class:
            raise ValueError(f"Unsupported integration type: {integration_type}")
        return connector_class(config)
