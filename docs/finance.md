# Finance Package API Documentation

## Overview
The finance package provides functionality for managing sales orders and related financial data.

## Classes

### SalesOrderHeader (implements Node)
Sales order header node implementation.

#### Methods
```python
def create(self, customer_name: str, customer_email: str, shipping_address: str,
           order_date: str, payment_method: str) -> str
```
Create a new sales order header.
- `customer_name`: Name of the customer
- `customer_email`: Email address of the customer
- `shipping_address`: Shipping address for the order
- `order_date`: Date of the order (ISO format)
- `payment_method`: Payment method used
- Returns: ID of created sales order header

```python
def query(self, customer_email: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]
```
Query sales order headers.
- `customer_email`: Optional filter by customer email
- `status`: Optional filter by order status
- Returns: List of matching headers

```python
def update_status(self, header_id: str, new_status: str) -> bool
```
Update the status of a sales order.
- `header_id`: ID of the sales order header
- `new_status`: New status to set
- Returns: True if update successful

### SalesOrderItem (implements Node)
Sales order item node implementation.

#### Methods
```python
def create(self, sales_order_id: str, product_code: str, product_name: str,
           price: Decimal, quantity: int, unit: str, discount: Decimal = Decimal("0.00")) -> str
```
Create a new sales order item.
- `sales_order_id`: ID of parent sales order header
- `product_code`: Product code reference
- `product_name`: Name of the product
- `price`: Unit price of the product
- `quantity`: Quantity ordered
- `unit`: Unit of measurement
- `discount`: Discount percentage (0-1)
- Returns: ID of created sales order item

```python
def query(self, sales_order_id: Optional[str] = None) -> List[Dict[str, Any]]
```
Query sales order items.
- `sales_order_id`: Optional filter by parent sales order
- Returns: List of matching items

### SalesOrder
Facade for managing sales orders, combining header and item operations.

#### Constructor
```python
def __init__(self, generator: Generator)
```
- `generator`: Generator instance for node operations

#### Methods
```python
def create_header(self, customer_name: str, customer_email: str, shipping_address: str,
                 order_date: str, payment_method: str) -> str
```
Create a new sales order header.
- Delegates to SalesOrderHeader.create()

```python
def create_item(self, sales_order_id: str, product_code: str, product_name: str,
               price: Decimal, quantity: int, unit: str, discount: Decimal = Decimal("0.00")) -> str
```
Create a new sales order item.
- Delegates to SalesOrderItem.create()

```python
def get_header(self, header_id: str) -> Optional[Dict[str, Any]]
```
Get sales order header by ID.
- Delegates to SalesOrderHeader.read()

```python
def get_items(self, header_id: str) -> List[Dict[str, Any]]
```
Get all items for a sales order.
- Delegates to SalesOrderItem.query()

```python
def calculate_total(self, header_id: str) -> Decimal
```
Calculate and update total amount for a sales order.
- Calculates total from items
- Updates header with new total
- Returns calculated total

```python
def update_status(self, header_id: str, new_status: str) -> bool
```
Update the status of a sales order.
- Delegates to SalesOrderHeader.update_status()
