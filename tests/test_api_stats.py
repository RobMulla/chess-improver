from unittest.mock import MagicMock, patch

import pytest

from src.web.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_activity_stats_endpoint(client):
    """Test the /api/stats/activity endpoint returns correct data structure."""

    # Mock data objects
    row1 = MagicMock()
    row1.date_str = "2024-01-01"
    row1.total = 5
    row1.analyzed = 2

    row2 = MagicMock()
    row2.date_str = "2024-01-02"
    row2.total = 3
    row2.analyzed = 3

    # Mock the database session chain
    with patch("src.web.app.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Setup the query chain: session.query().group_by().order_by().all()
        # Note: No .filter() in the actual implementation
        mock_query = mock_session.query.return_value
        mock_group_by = mock_query.group_by.return_value
        mock_order_by = mock_group_by.order_by.return_value
        mock_order_by.all.return_value = [row1, row2]

        response = client.get("/api/stats/activity")

        # Assertions
        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert "activity" in data
        assert len(data["activity"]) == 2

        assert data["activity"][0]["date"] == "2024-01-01"
        assert data["activity"][0]["count"] == 5
        assert data["activity"][0]["analyzed"] == 2

        assert data["activity"][1]["date"] == "2024-01-02"
        assert data["activity"][1]["count"] == 3
        assert data["activity"][1]["analyzed"] == 3
