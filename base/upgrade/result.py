"""Upgrade result tracking."""
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


class UpgradeStatus(Enum):
    """Status of an upgrade operation."""
    
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_NEEDED = "not_needed"


@dataclass
class UpgradeResult:
    """Result of an upgrade operation."""
    
    node_type: str
    node_id: str
    from_version: int
    to_version: int
    status: UpgradeStatus
    timestamp: datetime
    error: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_type": self.node_type,
            "node_id": self.node_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "changes": self.changes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpgradeResult':
        """Create from dictionary."""
        return cls(
            node_type=data["node_type"],
            node_id=data["node_id"],
            from_version=data["from_version"],
            to_version=data["to_version"],
            status=UpgradeStatus(data["status"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            error=data.get("error"),
            changes=data.get("changes")
        )
