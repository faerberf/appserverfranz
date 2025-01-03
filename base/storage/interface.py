"""Storage interface for reading and writing data."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union


class StorageData:
    """Represents data in storage with version information."""
    
    def __init__(
        self,
        data: Dict[str, Any],
        version: int,
        created_at: datetime,
        updated_at: datetime
    ):
        """Initialize storage data.
        
        Args:
            data: Actual data content
            version: Schema version
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.data = data
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageData':
        """Create from dictionary representation."""
        return cls(
            data=data["data"],
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


class StorageInterface(ABC):
    """Interface for reading and writing data."""
    
    @abstractmethod
    def create(self, node_type: str, node_id: str, data: Union[Dict[str, Any], StorageData]) -> bool:
        """Create a new node.
        
        Args:
            node_type: Type of node
            node_id: ID of node
            data: Data to write
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def read(self, node_type: str, node_id: str) -> Optional[StorageData]:
        """Read node data.
        
        Args:
            node_type: Type of node
            node_id: ID of node
            
        Returns:
            Optional[StorageData]: Node data if found
        """
        pass
        
    @abstractmethod
    def write(
        self,
        node_type: str,
        node_id: str,
        data: Union[Dict[str, Any], StorageData]
    ) -> bool:
        """Write node data.
        
        Args:
            node_type: Type of node
            node_id: ID of node
            data: Data to write
            
        Returns:
            bool: True if successful
        """
        pass
        
    @abstractmethod
    def update(
        self,
        node_type: str,
        node_id: str,
        data: Union[Dict[str, Any], StorageData]
    ) -> bool:
        """Update node data.
        
        Args:
            node_type: Type of node
            node_id: ID of node
            data: Data to update
            
        Returns:
            bool: True if successful
        """
        pass
        
    @abstractmethod
    def list_nodes(self, node_type: str) -> List[str]:
        """List all nodes of a type.
        
        Args:
            node_type: Type of nodes to list
            
        Returns:
            List[str]: List of node IDs
        """
        pass
        
    @abstractmethod
    def get_version(self, node_type: str, node_id: str) -> Optional[int]:
        """Get schema version of a node.
        
        Args:
            node_type: Type of node
            node_id: Node identifier
            
        Returns:
            Optional[int]: Schema version if found
        """
        pass
