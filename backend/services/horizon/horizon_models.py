"""Data models for ThreatVeil Horizon features."""
from typing import Dict, List, Optional


class HorizonRiskProfile:
    """Represents an AI risk profile for Horizon analysis."""
    
    def __init__(
        self,
        ai_tools: Optional[List[str]] = None,
        ai_vendors: Optional[List[Dict]] = None,
        ai_keys_exposed: Optional[List[Dict]] = None,
        ai_score: int = 0,
    ):
        self.ai_tools = ai_tools or []
        self.ai_vendors = ai_vendors or []
        self.ai_keys_exposed = ai_keys_exposed or []
        self.ai_score = ai_score
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "ai_tools": self.ai_tools,
            "ai_vendors": self.ai_vendors,
            "ai_keys_exposed": self.ai_keys_exposed,
            "ai_score": self.ai_score,
        }


# TODO: Add more Horizon-specific models as needed in future phases


