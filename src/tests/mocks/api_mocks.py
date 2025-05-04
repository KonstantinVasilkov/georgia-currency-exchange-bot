"""
Mock data for API testing.
"""

from datetime import datetime, timezone


def get_mock_exchange_response() -> dict:
    """Provide sample API response data for tests."""
    return {
        "best": {"USD": {"buy": 2.65, "sell": 2.70, "ccy": "USD", "nbg": 2.68}},
        "organizations": [
            {
                "id": "test-org-1",
                "name": "Test Organization",
                "offices": [
                    {
                        "id": "test-office-1",
                        "name": "Test Office",
                        "address": "123 Test St",
                        "lat": 41.7151,
                        "lng": 44.8271,
                        "rates": {
                            "USD": {
                                "buy": 2.65,
                                "sell": 2.70,
                                "ccy": "USD",
                                "time_from": datetime.now(timezone.utc).isoformat(),
                            }
                        },
                    }
                ],
            }
        ],
    }


def get_mock_organization_data() -> dict:
    """Provide sample organization data for tests."""
    return {
        "name": "Test Organization",
        "is_active": True,
        "external_ref_id": "test-org-1",
    }


def get_mock_office_data(organization_id: str) -> dict:
    """Provide sample office data for tests."""
    return {
        "name": "Test Office",
        "address": "123 Test St",
        "lat": 41.7151,
        "lng": 44.8271,
        "is_active": True,
        "organization_id": organization_id,
        "external_ref_id": "test-office-1",
    }


def get_mock_rate_data(office_id: str) -> dict:
    """Provide sample rate data for tests."""
    return {
        "office_id": office_id,
        "currency": "USD",
        "buy_rate": 2.65,
        "sell_rate": 2.70,
        "timestamp": datetime.now(timezone.utc),
    }
