# Base Package API Documentation

## Overview
The base package provides core functionality for node management, storage, and metadata handling.

## Classes

### Node (Abstract Base Class)
Base interface for all node types in the system.

#### Constructor
```python
def __init__(self, generator: Generator)
```
- `generator`: Generator instance for node operations

#### Abstract Methods
```python
@abstractmethod
def _get_node_type(self) -> str
```
Get the type name for this node.
- Returns: Node type name used in storage and metadata
- Must be implemented by concrete classes

```python
@abstractmethod
def create(self, **kwargs) -> str
```
Create a new node instance.
- Must be implemented by concrete classes
- Args: Node-specific creation parameters
- Returns: ID of created node
- Raises: ValueError if parameters are invalid

```python
@abstractmethod
def query(self, **kwargs) -> List[Dict[str, Any]]
```
Query nodes based on criteria.
- Must be implemented by concrete classes
- Args: Node-specific query parameters
- Returns: List of matching nodes

#### Implemented Methods
```python
def read(self, node_id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]
```
Read a node by ID.
- `node_id`: ID of the node to read
- `timestamp`: Optional timestamp for historical versions
- Returns: Node data if found, None otherwise

```python
def update(self, node_id: str, data: Dict[str, Any]) -> bool
```
Update an existing node.
- `node_id`: ID of the node to update
- `data`: New node data
- Returns: True if update successful
- Raises: ValueError if data is invalid

```python
def delete(self, node_id: str) -> bool
```
Delete a node.
- `node_id`: ID of the node to delete
- Returns: True if deletion successful

### Generator
Main interface for creating and managing nodes.

#### Constructor
```python
def __init__(self, base_path: str, metadata_dir: str = "metadata")
```
- `base_path`: Base directory path for storing node data
- `metadata_dir`: Directory containing metadata definitions (default: "metadata")

#### Methods
```python
def create_node(self, node_type: str, data: Dict[str, Any]) -> str
```
Create a new node of the given type.
- `node_type`: Type of node to create
- `data`: Node data to store
- Returns: ID of the created node
- Raises: ValueError if data is invalid or metadata not found

```python
def read_node(self, node_type: str, id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]
```
Read a node by ID.
- `node_type`: Type of node to read
- `id`: ID of the node
- `timestamp`: Optional timestamp for reading historical versions
- Returns: Node data if found, None otherwise

```python
def update_node(self, node_type: str, id: str, data: Dict[str, Any]) -> bool
```
Update an existing node.
- `node_type`: Type of node to update
- `id`: ID of the node
- `data`: New node data
- Returns: True if update successful, False otherwise
- Raises: ValueError if data is invalid

```python
def delete_node(self, node_type: str, id: str) -> bool
```
Delete a node.
- `node_type`: Type of node to delete
- `id`: ID of the node
- Returns: True if deletion successful, False otherwise

### Storage (Abstract Base Class)
Abstract base class for implementing storage backends.

#### Methods
```python
@abstractmethod
def create(self, node_type: str, data: Dict[str, Any]) -> str
```
Create a new node.
- Must be implemented by concrete classes
- Returns: ID of created node

```python
@abstractmethod
def read(self, node_type: str, id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]
```
Read a node.
- Must be implemented by concrete classes
- Returns: Node data if found, None otherwise

```python
@abstractmethod
def update(self, node_type: str, id: str, data: Dict[str, Any]) -> bool
```
Update a node.
- Must be implemented by concrete classes
- Returns: True if successful, False otherwise

```python
@abstractmethod
def delete(self, node_type: str, id: str) -> bool
```
Delete a node.
- Must be implemented by concrete classes
- Returns: True if successful, False otherwise
