"""Product functionality."""
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from base.nodes import Node
from base.storage.interface import StorageData
from base.generator import Generator
from base.metadata.api import MetadataAPI


class Product(Node):
    """Product functionality."""
    
    def __init__(self, generator: Generator):
        """Initialize with generator."""
        super().__init__(generator)
        
    def _get_node_type(self) -> str:
        """Get node type name."""
        return "masterdata.product"
        
    def create(
        self,
        code: str,
        name: str,
        description: str,
        price: Decimal,
        unit: str
    ) -> int:
        """Create a new product.
        
        Args:
            code: Product code
            name: Product name
            description: Product description
            price: Product price
            unit: Product unit
            
        Returns:
            int: Product ID
            
        Raises:
            ValueError: If product creation fails
        """
        try:
            # Get next ID
            product_id = self.counter.get_next_id(self.node_type)
            
            # Get latest metadata version
            metadata = self.generator.metadata_api.get_metadata("masterdata/product")
            if not metadata or "versions" not in metadata:
                raise ValueError("No metadata found for product")
                
            # Get latest version number
            latest_version = max(int(v) for v in metadata["versions"].keys())
            
            # Create product data
            data = {
                "id": product_id,
                "code": code,
                "name": name,
                "description": description,
                "price": str(price),
                "unit": unit,
                "_schema_version": latest_version
            }
            
            # Create product
            if not self.storage.create(self.node_type, str(product_id), data):
                raise ValueError(f"Failed to create product {code}")
                
            return product_id
            
        except Exception as e:
            raise ValueError(f"Failed to create product {code}: {str(e)}")
            
    def get(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Optional[Dict[str, Any]]: Product data or None if not found
        """
        return self.storage.read(self.node_type, str(product_id))
        
    def update(
        self,
        product_id: int,
        code: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[Decimal] = None,
        unit: Optional[str] = None
    ) -> bool:
        """Update a product.
        
        Args:
            product_id: Product ID
            code: New product code
            name: New product name
            description: New product description
            price: New product price
            unit: New product unit
            
        Returns:
            bool: True if updated, False if not found
            
        Raises:
            ValueError: If update fails
        """
        try:
            # Get current product
            product = self.get(product_id)
            if not product:
                return False
                
            # Update fields if provided
            data = dict(product)
            if code is not None:
                data["code"] = code
            if name is not None:
                data["name"] = name
            if description is not None:
                data["description"] = description
            if price is not None:
                data["price"] = str(price)
            if unit is not None:
                data["unit"] = unit
                
            # Update product
            return self.storage.update("product", str(product_id), data)
            
        except Exception as e:
            raise ValueError(f"Failed to update product {product_id}: {str(e)}")
            
    def delete(self, product_id: int) -> bool:
        """Delete a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        return self.storage.delete("product", str(product_id))
        
    def list_products(self) -> List[Dict[str, Any]]:
        """List all products.
        
        Returns:
            List[Dict[str, Any]]: List of products
        """
        products = []
        for product_id in self.storage.list_nodes("product"):
            product = self.get(int(product_id))
            if product:
                products.append(product)
        return products
