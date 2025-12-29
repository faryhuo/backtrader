"""
Sizer Configuration - Types for position sizing strategies.

Supports the following sizer types:
- Fixed Size: Fixed number of shares per trade
- Percent Sizer: Percentage of account value
- All In Sizer: Use all available cash
- Risk Sizer: Risk-based position sizing
- Kelly Sizer: Kelly Criterion sizing
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SizerType(str, Enum):
    """Available sizer types for position management."""
    FIXED_SIZE = "fixed_size"
    PERCENT_SIZER = "percent_sizer"
    ALL_IN_SIZER = "all_in_sizer"
    RISK_SIZER = "risk_sizer"
    KELLY_SIZER = "kelly_sizer"


class SizerConfig(BaseModel):
    """
    Configuration for position sizing strategy.
    
    Attributes:
        type: The sizer type to use
        stake: Fixed number of shares (for FIXED_SIZE)
        percents: Percentage of account (for PERCENT_SIZER)
        risk_percent: Maximum risk per trade (for RISK_SIZER)
    """
    type: SizerType = Field(default=SizerType.FIXED_SIZE, description="Sizer type")
    stake: int = Field(default=100, ge=1, description="Fixed stake size")
    percents: float = Field(default=10.0, ge=0.1, le=100.0, description="Account percentage")
    risk_percent: float = Field(default=2.0, ge=0.1, le=100.0, description="Risk per trade %")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "stake": self.stake,
            "percents": self.percents,
            "risk_percent": self.risk_percent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SizerConfig":
        """Create from dictionary."""
        if data is None:
            return cls()
        
        sizer_type = data.get("type", SizerType.FIXED_SIZE.value)
        if isinstance(sizer_type, str):
            sizer_type = SizerType(sizer_type)
        
        return cls(
            type=sizer_type,
            stake=data.get("stake", 100),
            percents=data.get("percents", 10.0),
            risk_percent=data.get("risk_percent", 2.0),
        )


# Sizer type display names for frontend
SIZER_TYPE_LABELS = {
    SizerType.FIXED_SIZE: "Fixed Size",
    SizerType.PERCENT_SIZER: "Percent Sizer",
    SizerType.ALL_IN_SIZER: "All In Sizer",
    SizerType.RISK_SIZER: "Risk Sizer",
    SizerType.KELLY_SIZER: "Kelly Criterion",
}


__all__ = [
    "SizerType",
    "SizerConfig",
    "SIZER_TYPE_LABELS",
]
