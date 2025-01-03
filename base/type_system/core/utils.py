from connectors.database import DatabaseConnector
from connectors.filesystem import FileSystemConnector
from connectors.base import SourceConnector

def resolve_node_definition(node_path):
    """
    Resolves a node definition path to an actual data source (e.g., database table, file path).

    Args:
        node_path (str): The path-like string representing the node definition (e.g., "/masterdata/product", "/file_system/order").

    Returns:
        tuple: A tuple containing the connector instance and the source identifier (e.g., table name, file path).
               Returns None if the node path is not recognized.
    """
    if node_path.startswith("/masterdata/product"):
        connector = DatabaseConnector()
        source_identifier = "products"  # The actual table name in the database
        return connector, source_identifier
    elif node_path.startswith("/masterdata/customer"):
        connector = DatabaseConnector()
        source_identifier = "customers"
        return connector, source_identifier
    elif node_path.startswith("/file_system"):
        connector = FileSystemConnector()
        # Remove the "/file_system" prefix to get the relative file path
        source_identifier = node_path[len("/file_system"):]
        return connector, source_identifier
    else:
        return None, None  # Node path not recognized

def load_properties_from_external_source(source):
    """Loads a type definition from an external source such as a database or file system."""
    connector, source_identifier = resolve_node_definition(source)

    if connector and source_identifier:
        if isinstance(connector, SourceConnector):
            return connector.get_schema(source_identifier)
        else:
            raise ValueError(f"Invalid connector type for source: {source}")
    else:
        raise ValueError(f"Could not resolve node definition for source: {source}")