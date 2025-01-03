"""Upgrade manager for handling data upgrades."""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..storage.interface import StorageInterface, StorageData
from ..schema.evolution import SchemaEvolution
from .strategy import UpgradeStrategy
from .result import UpgradeResult, UpgradeStatus


class UpgradeManager:
    """Manages data upgrades across schema versions."""
    
    def __init__(
        self,
        storage: StorageInterface,
        schema_evolution: SchemaEvolution,
        max_workers: int = 4
    ):
        """Initialize upgrade manager.
        
        Args:
            storage: Storage interface for reading/writing data
            schema_evolution: Schema evolution manager
            max_workers: Maximum number of parallel upgrade workers
        """
        self.storage = storage
        self.schema_evolution = schema_evolution
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self._transform_registry: Dict[str, Callable] = {}
        
    def register_transform(self, name: str, func: Callable) -> None:
        """Register a transform function.
        
        Args:
            name: Name of the transform function
            func: The transform function to register
        """
        self._transform_registry[name] = func
        
    def _apply_strategy(
        self,
        data: Dict[str, Any],
        strategy: UpgradeStrategy
    ) -> Dict[str, Any]:
        """Apply an upgrade strategy to data.
        
        Args:
            data: Data to upgrade
            strategy: Upgrade strategy to apply
            
        Returns:
            Dict[str, Any]: Upgraded data
        """
        result = data.copy()
        
        # Add new fields
        for field_def in strategy.add_fields:
            if field_def.name not in result:
                result[field_def.name] = field_def.default_value
                
            # Apply transform if specified
            if field_def.transform_function:
                transform = self._transform_registry.get(field_def.transform_function)
                if transform:
                    result[field_def.name] = transform(result[field_def.name])
        
        # Remove fields
        for field in strategy.remove_fields:
            result.pop(field, None)
            
        # Rename fields
        for old_name, new_name in strategy.rename_fields.items():
            if old_name in result:
                result[new_name] = result.pop(old_name)
                
        # Apply transforms
        for field, transform_name in strategy.transform_functions.items():
            if field in result:
                transform = self._transform_registry.get(transform_name)
                if transform:
                    result[field] = transform(result[field])
                    
        return result
        
    def upgrade_node(
        self,
        node_type: str,
        node_id: str,
        target_version: Optional[int] = None
    ) -> UpgradeResult:
        """Upgrade a single node.
        
        Args:
            node_type: Type of node to upgrade
            node_id: ID of node to upgrade
            target_version: Target version (defaults to latest)
            
        Returns:
            UpgradeResult: Result of the upgrade operation
        """
        try:
            # Read current data
            storage_data = self.storage.read(node_type, node_id)
            if not storage_data:
                return UpgradeResult(
                    node_type=node_type,
                    node_id=node_id,
                    from_version=0,
                    to_version=0,
                    status=UpgradeStatus.FAILED,
                    timestamp=datetime.now(timezone.utc),
                    error="Node not found"
                )
                
            current_version = storage_data.version
            if target_version is None:
                target_version = self.schema_evolution.get_latest_version().version
                
            if current_version >= target_version:
                return UpgradeResult(
                    node_type=node_type,
                    node_id=node_id,
                    from_version=current_version,
                    to_version=target_version,
                    status=UpgradeStatus.NOT_NEEDED,
                    timestamp=datetime.now(timezone.utc)
                )
                
            # Get upgrade path
            upgraded_data = storage_data.data.copy()
            changes = {}
            
            # Apply upgrades sequentially
            for version in range(current_version, target_version):
                strategy = self.schema_evolution.get_version(version + 1)
                if not strategy:
                    continue
                    
                # Track changes before upgrade
                old_data = upgraded_data.copy()
                
                # Apply upgrade strategy
                upgraded_data = self._apply_strategy(upgraded_data, strategy)
                
                # Track changes
                changes[f"v{version + 1}"] = {
                    k: v for k, v in upgraded_data.items()
                    if k not in old_data or old_data[k] != v
                }
                
            # Save upgraded data
            new_storage_data = StorageData(
                data=upgraded_data,
                version=target_version,
                created_at=storage_data.created_at,
                updated_at=datetime.now(timezone.utc),
                metadata=storage_data.metadata
            )
            
            if self.storage.update(node_type, node_id, new_storage_data):
                return UpgradeResult(
                    node_type=node_type,
                    node_id=node_id,
                    from_version=current_version,
                    to_version=target_version,
                    status=UpgradeStatus.SUCCESS,
                    timestamp=datetime.now(timezone.utc),
                    changes=changes
                )
            else:
                return UpgradeResult(
                    node_type=node_type,
                    node_id=node_id,
                    from_version=current_version,
                    to_version=target_version,
                    status=UpgradeStatus.FAILED,
                    timestamp=datetime.now(timezone.utc),
                    error="Failed to save upgraded data"
                )
                
        except Exception as e:
            self.logger.exception(f"Error upgrading node {node_type}/{node_id}")
            return UpgradeResult(
                node_type=node_type,
                node_id=node_id,
                from_version=current_version if 'current_version' in locals() else 0,
                to_version=target_version if 'target_version' in locals() else 0,
                status=UpgradeStatus.FAILED,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
            
    def upgrade_all(
        self,
        node_type: str,
        target_version: Optional[int] = None,
        batch_size: int = 100
    ) -> List[UpgradeResult]:
        """Upgrade all nodes of a type.
        
        Args:
            node_type: Type of nodes to upgrade
            target_version: Target version (defaults to latest)
            batch_size: Number of nodes to upgrade in parallel
            
        Returns:
            List[UpgradeResult]: Results of all upgrade operations
        """
        results = []
        node_ids = self.storage.list_nodes(node_type)
        
        # Process nodes in batches
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i in range(0, len(node_ids), batch_size):
                batch = node_ids[i:i + batch_size]
                futures = [
                    executor.submit(self.upgrade_node, node_type, node_id, target_version)
                    for node_id in batch
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        if result.status == UpgradeStatus.FAILED:
                            self.logger.error(
                                f"Failed to upgrade {node_type}/{result.node_id}: {result.error}"
                            )
                    except Exception as e:
                        self.logger.exception(f"Error processing upgrade batch for {node_type}")
                        
        return results
