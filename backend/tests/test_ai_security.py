"""
Tests for the AI Security endpoint (Phase 3).

Tests:
- AI tool aggregation
- Agent framework detection
- Exposed keys timeline
- AI risk trend calculation
- Status determination
- Explanation generation
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


class TestAISecurityHelpers:
    """Test AI security helper functions."""

    def test_is_agent_framework_langchain(self):
        """LangChain should be detected as agent framework."""
        from backend.routes.ai_security import is_agent_framework
        
        assert is_agent_framework("langchain") is True
        assert is_agent_framework("langchain-serve") is True
        assert is_agent_framework("LANGCHAIN") is True
    
    def test_is_agent_framework_crewai(self):
        """CrewAI should be detected as agent framework."""
        from backend.routes.ai_security import is_agent_framework
        
        assert is_agent_framework("crewai") is True
        assert is_agent_framework("crewAI-tools") is True
    
    def test_is_agent_framework_autogen(self):
        """AutoGen should be detected as agent framework."""
        from backend.routes.ai_security import is_agent_framework
        
        assert is_agent_framework("autogen") is True
        assert is_agent_framework("microsoft-autogen") is True
    
    def test_is_not_agent_framework(self):
        """Regular AI libraries should not be flagged as agent frameworks."""
        from backend.routes.ai_security import is_agent_framework
        
        assert is_agent_framework("openai-python") is False
        assert is_agent_framework("transformers") is False
        assert is_agent_framework("pytorch") is False
        assert is_agent_framework("tensorflow") is False


class TestAIStatus:
    """Test AI status determination."""

    def test_clean_status_low_score(self):
        """Low scores should return clean status."""
        from backend.routes.ai_security import get_ai_status
        
        assert get_ai_status(0) == "clean"
        assert get_ai_status(10) == "clean"
        assert get_ai_status(20) == "clean"
    
    def test_warning_status_medium_score(self):
        """Medium scores should return warning status."""
        from backend.routes.ai_security import get_ai_status
        
        assert get_ai_status(21) == "warning"
        assert get_ai_status(35) == "warning"
        assert get_ai_status(50) == "warning"
    
    def test_critical_status_high_score(self):
        """High scores should return critical status."""
        from backend.routes.ai_security import get_ai_status
        
        assert get_ai_status(51) == "critical"
        assert get_ai_status(75) == "critical"
        assert get_ai_status(100) == "critical"


class TestExplanationGeneration:
    """Test AI explanation generation."""

    def test_clean_no_tools_explanation(self):
        """Clean state with no tools should have appropriate message."""
        from backend.routes.ai_security import generate_ai_explanation
        
        explanation = generate_ai_explanation(
            ai_score=0,
            tools_count=0,
            agent_count=0,
            keys_count=0,
            status="clean"
        )
        
        assert "No AI tools" in explanation or "minimal" in explanation
    
    def test_exposed_keys_in_explanation(self):
        """Exposed keys should be mentioned in explanation."""
        from backend.routes.ai_security import generate_ai_explanation
        
        explanation = generate_ai_explanation(
            ai_score=60,
            tools_count=2,
            agent_count=1,
            keys_count=3,
            status="critical"
        )
        
        assert "3" in explanation
        assert "key" in explanation.lower()
    
    def test_critical_action_required(self):
        """Critical status should mention immediate action."""
        from backend.routes.ai_security import generate_ai_explanation
        
        explanation = generate_ai_explanation(
            ai_score=80,
            tools_count=5,
            agent_count=2,
            keys_count=2,
            status="critical"
        )
        
        assert "immediate" in explanation.lower() or "action" in explanation.lower()


class TestNextActionDetermination:
    """Test next action recommendation logic."""

    def test_keys_exposed_action(self):
        """Exposed keys should trigger rotation recommendation."""
        from backend.routes.ai_security import determine_ai_next_action
        
        action = determine_ai_next_action(
            status="critical",
            keys_count=2,
            agent_count=1,
            tools_count=5
        )
        
        assert "rotate" in action.lower() or "key" in action.lower()
    
    def test_agent_frameworks_action(self):
        """Agent frameworks should trigger access control review."""
        from backend.routes.ai_security import determine_ai_next_action
        
        action = determine_ai_next_action(
            status="warning",
            keys_count=0,
            agent_count=2,
            tools_count=5
        )
        
        assert "agent" in action.lower() or "audit" in action.lower()
    
    def test_no_exposure_action(self):
        """No exposure should recommend continued monitoring."""
        from backend.routes.ai_security import determine_ai_next_action
        
        action = determine_ai_next_action(
            status="clean",
            keys_count=0,
            agent_count=0,
            tools_count=0
        )
        
        assert "monitor" in action.lower()


class TestAIToolDetected:
    """Test AIToolDetected schema."""

    def test_tool_detected_schema(self):
        """AIToolDetected schema should have required fields."""
        from backend.routes.ai_security import AIToolDetected
        
        tool = AIToolDetected(
            name="openai-python",
            count=5,
            is_agent_framework=False
        )
        
        assert tool.name == "openai-python"
        assert tool.count == 5
        assert tool.is_agent_framework is False


class TestExposedKeyEvent:
    """Test ExposedKeyEvent schema."""

    def test_key_event_schema(self):
        """ExposedKeyEvent schema should have required fields."""
        from backend.routes.ai_security import ExposedKeyEvent
        
        event = ExposedKeyEvent(
            date="2025-01-01",
            count=3,
            key_types=["openai", "anthropic"]
        )
        
        assert event.date == "2025-01-01"
        assert event.count == 3
        assert "openai" in event.key_types


class TestAIRiskPoint:
    """Test AIRiskPoint schema."""

    def test_risk_point_schema(self):
        """AIRiskPoint schema should have required fields."""
        from backend.routes.ai_security import AIRiskPoint
        
        point = AIRiskPoint(
            week_start="2025-01-06",
            ai_score=45,
            delta=5
        )
        
        assert point.week_start == "2025-01-06"
        assert point.ai_score == 45
        assert point.delta == 5
