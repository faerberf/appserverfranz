"""Abstract base class for storage implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Storage(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    def create(self, node_type: str, data: Dict[str, Any]) -> str:
        """Create a new node.
        
        Args:
            node_type: Type of node to create
            data: Node data to store
            
        Returns:
            str: ID of the created node
        """
        pass

    @abstractmethod
    def read(self, node_type: str, id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Read a node.
        
        Args:
            node_type: Type of node to read
            id: ID of the node to read
            timestamp: Optional timestamp to read historical version
            
        Returns:
            Optional[Dict[str, Any]]: Node data if found, None otherwise
        """
        pass

    @abstractmethod
    def update(self, node_type: str, id: str, data: Dict[str, Any]) -> bool:
        """Update a node.
        
        Args:
            node_type: Type of node to update
            id: ID of the node to update
            data: New node data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, node_type: str, id: str) -> bool:
        """Delete a node.
        
        Args:
            node_type: Type of node to delete
            id: ID of the node to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
