# Finance Package API Documentation

## Overview
The finance package provides functionality for managing sales orders and related financial data.

## Classes

### SalesOrderHeader (`Node`)
Operations for sales order headers.

#### Methods
```python
def create(self, **data) -> str
```
Create a new sales order header.

```python
def read(self, node_id: str) -> Optional[Dict[str, Any]]
```
Retrieve a sales order header by ID.

```python
def update(self, node_id: str, data: Dict[str, Any]) -> bool
```
Update fields on a sales order header.

```python
def update_status(self, node_id: str, new_status: str) -> bool
```
Update the `status` field of a sales order header.

```python
def delete(self, node_id: str) -> bool
```
Mark a sales order header as deleted by setting `date_to`.

### SalesOrderItem (`Node`)
Operations for individual sales order items.

#### Methods
```python
def create(self, **data) -> str
```
Create a new sales order item.

```python
def read(self, node_id: str) -> Optional[Dict[str, Any]]
```
Retrieve a sales order item by ID.

```python
def query(self, **kwargs) -> List[Dict[str, Any]]
```
Query sales order items, for example by `order_id`.

```python
def update(self, node_id: str, data: Dict[str, Any]) -> bool
```
Update fields on a sales order item.

```python
def delete(self, node_id: str) -> bool
```
Mark a sales order item as deleted by setting `date_to`.

### SalesOrder
Facade combining header and item operations.

#### Constructor
```python
def __init__(self, generator: Generator)
```

#### Methods
```python
def create_order(self, header_data: Dict[str, Any], items_data: List[Dict[str, Any]]) -> Dict[str, Any]
```
Create a new sales order along with its items.

```python
def get_order(self, header_id: str) -> Optional[Dict[str, Any]]
```
Retrieve an order and its items.

```python
def update_order(self, header_id: str, header_data: Optional[Dict[str, Any]] = None,
                 items_data: Optional[List[Dict[str, Any]]] = None) -> bool
```
Update an existing order.

```python
def update_status(self, header_id: str, new_status: str) -> bool
```
Update the status of an existing order.

```python
def delete_order(self, header_id: str) -> bool
```
Delete an order including its items.

### SalesOrderAPI
API layer that adds version handling to `SalesOrder`.

#### Methods
```python
def create_order(self, api_version: str, order_data: Dict[str, Any],
                 items_data: List[Dict[str, Any]]) -> Dict[str, Any]
```
Create a new order via the API.

```python
def get_order(self, api_version: str, header_id: str) -> Optional[Dict[str, Any]]
```
Fetch an order via the API.

```python
def update_order(self, api_version: str, header_id: str,
                 order_data: Optional[Dict[str, Any]] = None,
                 items_data: Optional[List[Dict[str, Any]]] = None) -> bool
```
Update an order via the API.

```python
def delete_order(self, api_version: str, header_id: str) -> bool
```
Delete an order via the API.

```python
def list_orders(self, api_version: str) -> List[Dict[str, Any]]
```
List all orders with basic information.

