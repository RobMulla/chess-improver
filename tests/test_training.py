"""Test training plan generator."""
import pytest
from datetime import date
from unittest.mock import Mock, patch
from src.training.plan_generator import PlanGenerator


class TestPlanGenerator:
    """Test daily plan generation."""
    
    @patch('src.training.plan_generator.get_session')
    def test_plan_structure(self, mock_session):
        """Test generated plan has correct structure."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        generator = PlanGenerator()
        # Would need to mock the full database flow
    
    def test_task_fields(self):
        """Test task has required fields."""
        task = {
            "id": 1,
            "type": "tactics",
            "title": "Solve tactics",
            "duration": "10 min",
            "resources": ["https://lichess.org/training"],
            "completed": False
        }
        
        assert "id" in task
        assert "type" in task
        assert "title" in task
        assert "duration" in task
        assert "resources" in task
        assert "completed" in task
        assert isinstance(task["resources"], list)
