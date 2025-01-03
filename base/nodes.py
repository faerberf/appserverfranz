"""Base node interface and implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from .generator import Generator
from .counter import Counter


class Node(ABC):
    """Abstract base class for all node types."""
    
    def __init__(self, generator: Generator):
        """Initialize with a generator instance."""
        self.generator = generator
        self.storage = generator.storage
        self.version_manager = generator.version_manager
        self.counter = Counter(generator.storage)
        self.node_type = self._get_node_type()

    @abstractmethod
    def _get_node_type(self) -> str:
        """Get the type name for this node.
        
        Returns:
            str: Node type name used in storage and metadata
        """
        pass

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data with default fields.
        
        Args:
            data: Raw data to prepare
            
        Returns:
            Dict[str, Any]: Data with default fields
        """
        now = datetime.now(timezone.utc)
        
        # Get next ID
        node_id = self.counter.get_next_id(self.node_type)
        
        # Add default fields
        data.update({
            "id": node_id,
            "date_from": now.isoformat(),
            "date_to": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        })
        
        return data

    @abstractmethod
    def create(self, **kwargs) -> str:
        """Create a new node instance.
        
        Args:
            **kwargs: Node-specific creation parameters
            
        Returns:
            str: ID of created node
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        pass

    def read(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Read a node by ID.
        
        Args:
            node_id: ID of the node to read
            
        Returns:
            Optional[Dict[str, Any]]: Node data if found, None otherwise
        """
        return self.generator.read_node(self.node_type, node_id)

    def update(self, node_id: str, data: Dict[str, Any]) -> bool:
        """Update a node by creating a new version.
        
        This creates a new version of the node with updated data,
        setting date_to on the previous version and date_from on the new version.
        
        Args:
            node_id: ID of the node to update
            data: New node data
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If node not found or data invalid
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            raise ValueError(f"Node {node_id} not found")
            
        now = datetime.now(timezone.utc)
        
        # Close current version
        current["date_to"] = now.isoformat()
        if not self.generator.update_node(self.node_type, node_id, current):
            raise ValueError(f"Failed to update node {node_id}")
            
        # Create new version
        data.update({
            "id": node_id,  # Keep same ID
            "date_from": now.isoformat(),
            "date_to": None
        })
        
        return self.generator.update_node(self.node_type, node_id, data)

    def delete(self, node_id: str) -> bool:
        """Mark a node as deleted by setting date_to.
        
        This doesn't actually delete the node, just marks it as inactive
        by setting date_to on the current version.
        
        Args:
            node_id: ID of the node to delete
            
        Returns:
            bool: True if successful
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            return False
            
        # Set date_to to mark as deleted
        current["date_to"] = datetime.now(timezone.utc).isoformat()
        return self.generator.update_node(self.node_type, node_id, current)

    def query(self, **kwargs) -> List[Dict[str, Any]]:
        """Query nodes with optional filters.
        
        Args:
            **kwargs: Query parameters
            
        Returns:
            List[Dict[str, Any]]: List of matching nodes
        """
        # Add active version filter
        kwargs["date_to"] = None
        return self.generator.query_nodes(self.node_type, **kwargs)
