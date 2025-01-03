"""Sales order functionality."""
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from base.nodes import Node
from base.storage.interface import StorageData
from base.generator import Generator
from base.metadata.api import MetadataAPI
from base.api.version import APIVersionManager
import os


class SalesOrderHeader(Node):
    """Sales order header functionality."""
    
    def __init__(self, generator: Generator):
        """Initialize with generator."""
        super().__init__(generator)
        
    def _get_node_type(self) -> str:
        """Get node type name."""
        return "finance/sales_order_header"
        
    def create(self, **data) -> str:
        """Create a new sales order header."""
        try:
            # Get next ID
            order_id = self.counter.get_next_id("finance/sales_order_header")
            
            # Add ID to data
            data["id"] = order_id
            
            # Add timestamps
            now = datetime.now(timezone.utc)
            data.update({
                "date_from": now.isoformat(),
                "date_to": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            })
            
            # Create header
            if not self.generator.create_node(self._get_node_type(), str(order_id), data):
                raise ValueError(f"Failed to create order header {order_id}")
                
            return str(order_id)
            
        except Exception as e:
            raise ValueError(f"Failed to create order header: {str(e)}")
        
    def read(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Read a sales order header.
        
        Args:
            node_id: Node ID
            
        Returns:
            Optional[Dict[str, Any]]: Node data or None if not found
        """
        try:
            data = self.generator.read_node(self._get_node_type(), node_id)
            return data
        except Exception as e:
            return None
        
    def update(self, node_id: str, data: Dict[str, Any]) -> bool:
        """Update a sales order header.
        
        Args:
            node_id: Node ID
            data: New node data
            
        Returns:
            bool: True if updated, False if not found
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            return False
            
        # Update data
        now = datetime.now(timezone.utc)
        current.update(data)
        current["date_modified"] = now.isoformat()
        
        # Update node
        return self.generator.update_node(self._get_node_type(), node_id, current)
        
    def delete(self, node_id: str) -> bool:
        """Delete a sales order header.
        
        Args:
            node_id: Node ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            return False
            
        # Set date_to to mark as deleted
        current["date_to"] = datetime.now(timezone.utc).isoformat()
        return self.generator.update_node(self._get_node_type(), node_id, current)


class SalesOrderItem(Node):
    """Sales order item functionality."""
    
    def __init__(self, generator: Generator):
        """Initialize with generator."""
        super().__init__(generator)
        
    def _get_node_type(self) -> str:
        """Get node type name."""
        return "finance/sales_order_item"
        
    def create(self, **data) -> str:
        """Create a new sales order item."""
        try:
            # Get next ID
            item_id = self.counter.get_next_id("finance/sales_order_item")
            
            # Add ID to data
            data["id"] = item_id
            
            # Add timestamps
            now = datetime.now(timezone.utc)
            data.update({
                "date_from": now.isoformat(),
                "date_to": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            })
            
            # Create item
            if not self.generator.create_node(self._get_node_type(), str(item_id), data):
                raise ValueError(f"Failed to create order item {item_id}")
                
            return str(item_id)
            
        except Exception as e:
            raise ValueError(f"Failed to create order item: {str(e)}")
        
    def read(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Read a sales order item.
        
        Args:
            node_id: Node ID
            
        Returns:
            Optional[Dict[str, Any]]: Node data or None if not found
        """
        return self.generator.read_node(self._get_node_type(), node_id)
        
    def query(self, **kwargs) -> List[Dict[str, Any]]:
        """Query sales order items.
        
        Args:
            **kwargs: Query parameters
            
        Returns:
            List[Dict[str, Any]]: List of node data
        """
        return self.generator.query_nodes(self._get_node_type(), **kwargs)
        
    def update(self, node_id: str, data: Dict[str, Any]) -> bool:
        """Update a sales order item.
        
        Args:
            node_id: Node ID
            data: New node data
            
        Returns:
            bool: True if updated, False if not found
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            return False
            
        # Update data
        now = datetime.now(timezone.utc)
        current.update(data)
        current["date_modified"] = now.isoformat()
        
        # Update node
        return self.generator.update_node(self._get_node_type(), node_id, current)
        
    def delete(self, node_id: str) -> bool:
        """Delete a sales order item.
        
        Args:
            node_id: Node ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Read current version
        current = self.read(node_id)
        if not current:
            return False
            
        # Set date_to to mark as deleted
        current["date_to"] = datetime.now(timezone.utc).isoformat()
        return self.generator.update_node(self._get_node_type(), node_id, current)


class SalesOrder:
    """Sales order functionality."""
    
    def __init__(self, generator: Generator):
        """Initialize with generator."""
        self.generator = generator
        self.header = SalesOrderHeader(generator)
        self.item = SalesOrderItem(generator)
        
    def create_order(
        self,
        header_data: Dict[str, Any],
        items_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new sales order."""
        try:
            # Create header
            header_id = self.header.create(**header_data)
            if not header_id:
                raise ValueError("Failed to create order header")
                
            # Create items
            item_ids = []
            for item_data in items_data:
                item_data["order_id"] = header_id
                item_id = self.item.create(**item_data)
                if not item_id:
                    raise ValueError("Failed to create order item")
                item_ids.append(item_id)
                
            # Return order data
            return {
                "header_id": header_id,
                "item_ids": item_ids
            }
            
        except Exception as e:
            raise ValueError(f"Failed to create order: {str(e)}")
            
    def get_order(self, header_id: str) -> Optional[Dict[str, Any]]:
        """Get a sales order by header ID.
        
        Args:
            header_id: Order header ID
            
        Returns:
            Optional[Dict[str, Any]]: Order data or None if not found
        """
        # Get header
        header = self.header.read(header_id)
        if not header:
            return None
            
        # Get items
        items = self.item.query(order_id=header_id)
                
        # Return order data
        return {
            "header": header,
            "items": items
        }
        
    def update_order(
        self,
        header_id: str,
        header_data: Optional[Dict[str, Any]] = None,
        items_data: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update a sales order.
        
        Args:
            header_id: Order header ID
            header_data: New header data
            items_data: New items data
            
        Returns:
            bool: True if updated, False if not found
        """
        try:
            # Update header
            if header_data:
                if not self.header.update(header_id, header_data):
                    return False
                    
            # Update items
            if items_data:
                # Get current items
                order = self.get_order(header_id)
                if not order:
                    return False
                    
                # Delete old items
                for item in order["items"]:
                    self.item.delete(item["id"])
                    
                # Create new items
                for item_data in items_data:
                    item_data["order_id"] = header_id
                    self.item.create(**item_data)
                    
            return True
            
        except Exception:
            return False
            
    def delete_order(self, header_id: str) -> bool:
        """Delete a sales order.
        
        Args:
            header_id: Order header ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get order
            order = self.get_order(header_id)
            if not order:
                return False
                
            # Delete items
            for item in order["items"]:
                if not self.item.delete(item["id"]):
                    return False
                    
            # Delete header
            return self.header.delete(header_id)
            
        except Exception:
            return False


class SalesOrderAPI:
    """Sales order API functionality."""
    
    def __init__(self, service: SalesOrder, version_manager: APIVersionManager):
        """Initialize with service and version manager."""
        self.service = service
        self.version_manager = version_manager
        
    def create_order(
        self,
        api_version: str,
        order_data: Dict[str, Any],
        items_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new sales order.
        
        Args:
            api_version: API version
            order_data: Order header data
            items_data: Order items data
            
        Returns:
            Dict[str, Any]: Created order data
            
        Raises:
            ValueError: If order creation fails
        """
        try:
            # Convert header data
            header_data = order_data.copy()
            schema_version = self.version_manager.get_schema_version("finance/sales_order_header")
            header_data["_schema_version"] = schema_version.version if schema_version else 1
            
            # Convert items data
            items = []
            for item_data in items_data:
                item = item_data.copy()
                schema_version = self.version_manager.get_schema_version("finance/sales_order_item")
                item["_schema_version"] = schema_version.version if schema_version else 1
                items.append(item)
                
            # Create order
            return self.service.create_order(header_data, items)
            
        except Exception as e:
            raise ValueError(f"Failed to create order: {str(e)}")
            
    def get_order(self, api_version: str, header_id: str) -> Optional[Dict[str, Any]]:
        """Get a sales order.
        
        Args:
            api_version: API version
            header_id: Order header ID
            
        Returns:
            Optional[Dict[str, Any]]: Order data or None if not found
        """
        try:
            # Get order
            order = self.service.get_order(header_id)
            if not order:
                return None
            
            # Convert header data
            header_data = order["header"]
            header_version = header_data.get("_schema_version", 1)
            header_data = self.version_manager.convert_response(
                api_version,
                "finance/sales_order_header",
                header_data,
                header_version
            )
            
            # Convert items data
            items = []
            for item_data in order["items"]:
                item_version = item_data.get("_schema_version", 1)
                item = self.version_manager.convert_response(
                    api_version,
                    "finance/sales_order_item",
                    item_data,
                    item_version
                )
                items.append(item)
                
            return {
                "header": header_data,
                "items": items
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get order: {str(e)}")
            
    def update_order(
        self,
        api_version: str,
        header_id: str,
        order_data: Optional[Dict[str, Any]] = None,
        items_data: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update a sales order.
        
        Args:
            api_version: API version
            header_id: Order header ID
            order_data: New order header data
            items_data: New order items data
            
        Returns:
            bool: True if updated, False if not found
        """
        try:
            # Convert header data
            header_data = None
            if order_data:
                header_data = order_data.copy()
                schema_version = self.version_manager.get_schema_version("finance/sales_order_header")
                header_data["_schema_version"] = schema_version.version if schema_version else 1
                
            # Convert items data
            items = None
            if items_data:
                items = []
                for item_data in items_data:
                    item = item_data.copy()
                    schema_version = self.version_manager.get_schema_version("finance/sales_order_item")
                    item["_schema_version"] = schema_version.version if schema_version else 1
                    items.append(item)
                    
            # Update order
            return self.service.update_order(header_id, header_data, items)
            
        except Exception as e:
            raise ValueError(f"Failed to update order: {str(e)}")
            
    def delete_order(self, api_version: str, header_id: str) -> bool:
        """Delete a sales order.
        
        Args:
            api_version: API version
            header_id: Order header ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            return self.service.delete_order(header_id)
        except Exception as e:
            raise ValueError(f"Failed to delete order: {str(e)}")

    def list_orders(self, api_version: str) -> List[Dict[str, Any]]:
        """List all orders with basic information.
        
        Args:
            api_version: API version
            
        Returns:
            List[Dict[str, Any]]: List of orders with their details
        """
        try:
            # Get the data path for order headers
            data_path = os.path.join(self.service.generator.data_path, "finance", "sales_order_header")
            
            if not os.path.exists(data_path):
                return []
                
            # List all order files
            order_files = []
            files_in_dir = os.listdir(data_path)
            
            for file_name in files_in_dir:
                if file_name.endswith(".json"):
                    # Get order details
                    order_id = file_name.replace(".json", "")
                    try:
                        order = self.get_order(api_version,order_id)
                        if order and order.get("header"):
                            order_files.append({
                                "id": order_id,
                                "header": order["header"],
                                "created_at": order["header"].get("created_at", "Unknown")
                            })
                    except Exception as e:
                        print(f"Error reading order {order_id}: {str(e)}")
            
            # Sort orders by creation date (newest first)
            order_files.sort(key=lambda x: x["created_at"], reverse=True)
            return order_files
                
        except Exception as e:
            return []
