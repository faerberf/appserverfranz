"""Counter functionality."""
import os
import json
from typing import Dict, Any


class Counter:
    """Counter for generating sequential IDs."""
    
    def __init__(self, storage):
        """Initialize with storage interface."""
        self.storage = storage
        
    def _get_counter_path(self, node_type: str) -> str:
        """Get path to counter file."""
        print(f"\nDEBUG Counter._get_counter_path:")
        print(f"  Input node_type: {node_type}")
        print(f"  Storage base path: {self.storage.base_path}")
        
        # Split node type into parts and remove any empty parts
        parts = [p for p in node_type.split('/') if p]
        node_path = os.path.join(*parts)
        print(f"  Node path after join: {node_path}")
        
        # Counter should be in the data directory
        data_dir = os.path.join(self.storage.base_path, node_path)
        print(f"  Data dir: {data_dir}")
        
        # Use the last part of the path for the counter name
        counter_name = parts[-1]
        print(f"  Counter name: {counter_name}")
        
        # Create counter in the node's directory with the node's name
        counter_path = os.path.join(data_dir, f"{counter_name}.counter")
        print(f"  Counter path: {counter_path}")
        return counter_path
        
    def _ensure_counter(self, node_type: str) -> None:
        """Ensure counter exists for node type."""
        counter_path = self._get_counter_path(node_type)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(counter_path), exist_ok=True)
        
        # Create counter file if doesn't exist
        if not os.path.exists(counter_path):
            with open(counter_path, 'w') as f:
                json.dump({"current": 0}, f)
        
    def get_next_id(self, node_type: str) -> int:
        """Get next ID for a node type.
        
        Args:
            node_type: Type of node to get ID for
            
        Returns:
            int: Next available ID
            
        Raises:
            ValueError: If counter not found or update fails
        """
        # Ensure counter exists
        self._ensure_counter(node_type)
        
        counter_path = self._get_counter_path(node_type)
        
        try:
            # Read current value
            with open(counter_path, 'r') as f:
                data = json.load(f)
                
            current = data.get("current", 0)
            next_id = current + 1
            
            # Write new value
            with open(counter_path, 'w') as f:
                json.dump({"current": next_id}, f)
                
            return next_id
            
        except Exception as e:
            raise ValueError(f"Failed to update counter for {node_type}: {str(e)}")
