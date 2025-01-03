# Master Data Package API Documentation

## Overview
The masterdata package provides functionality for managing master data like products and customers.

## Classes

### Product (implements Node)
Product node implementation.

#### Methods
```python
def create(self, code: str, name: str, description: str, price: Decimal, unit: str) -> str
```
Create a new product.
- `code`: Unique product code
- `name`: Product name
- `description`: Product description
- `price`: Product unit price
- `unit`: Unit of measurement
- Returns: ID of created product

```python
def query(self, code: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]
```
Query products.
- `code`: Optional filter by product code
- `status`: Optional filter by product status
- Returns: List of matching products

```python
def update_price(self, product_id: str, new_price: Decimal) -> bool
```
Update product price.
- `product_id`: ID of the product
- `new_price`: New price to set
- Returns: True if update successful

```python
def deactivate(self, product_id: str) -> bool
```
Deactivate a product.
- `product_id`: ID of the product
- Returns: True if deactivation successful

### Common Operations
All node implementations inherit these operations from the Node base class:

```python
def read(self, node_id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]
```
Read a product by ID.
- `node_id`: ID of the product
- `timestamp`: Optional timestamp for historical versions
- Returns: Product data if found, None otherwise

```python
def update(self, node_id: str, data: Dict[str, Any]) -> bool
```
Update a product.
- `node_id`: ID of the product
- `data`: New product data
- Returns: True if update successful

```python
def delete(self, node_id: str) -> bool
```
Delete a product.
- `node_id`: ID of the product
- Returns: True if deletion successful
