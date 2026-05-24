"""
Model Manager for AI Continuous Learning System
Comprehensive model versioning, deployment, and lifecycle management
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import pickle
import hashlib
import shutil
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class ModelStatus(Enum):
    """Model deployment status"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelType(Enum):
    """Model types for management"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    ENSEMBLE = "ensemble"
    NEURAL_NETWORK = "neural_network"
    TREE_BASED = "tree_based"


@dataclass
class ModelVersion:
    """Model version information"""
    model_id: str
    version: str
    model_name: str
    model_type: ModelType
    status: ModelStatus
    file_path: str
    file_hash: str
    file_size: int
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_timestamp: datetime
    deployment_timestamp: Optional[datetime] = None
    created_by: str = "system"
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ModelDeployment:
    """Model deployment information"""
    deployment_id: str
    model_id: str
    version: str
    environment: str
    status: ModelStatus
    deployment_timestamp: datetime
    rollback_version: Optional[str] = None
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    health_check_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelHistory:
    """Model history tracking"""
    model_id: str
    action: str
    version: str
    timestamp: datetime
    user: str
    details: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None


class ModelManager:
    """Comprehensive model version control and deployment management"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db", 
                 models_directory: str = "Models"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.models_directory = Path(models_directory)
        
        # Create models directory if it doesn't exist
        self.models_directory.mkdir(parents=True, exist_ok=True)
        
        # Version control settings
        self.max_versions_per_model = 10
        self.auto_cleanup_enabled = True
        self.backup_enabled = True
        
        # Initialize database tables
        self._init_model_tables()
        
        # Current deployments cache
        self._current_deployments = {}
        self._load_current_deployments()
        
        self.logger.info("Model Manager initialized")
    
    def save_model(self, model: Any, model_name: str, model_type: ModelType,
                   performance_metrics: Dict[str, float], metadata: Optional[Dict[str, Any]] = None,
                   description: str = "", tags: Optional[List[str]] = None) -> ModelVersion:
        """Save a new model version"""
        try:
            self.logger.info(f"Saving model: {model_name}")
            
            # Generate model ID and version
            model_id = self._generate_model_id(model_name)
            version = self._generate_version(model_id)
            
            # Create file path
            file_name = f"{model_id}_v{version}.pkl"
            file_path = self.models_directory / file_name
            
            # Save model to file
            with open(file_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Calculate file hash and size
            file_hash = self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            # Create model version
            model_version = ModelVersion(
                model_id=model_id,
                version=version,
                model_name=model_name,
                model_type=model_type,
                status=ModelStatus.DEVELOPMENT,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=file_size,
                metadata=metadata or {},
                performance_metrics=performance_metrics,
                training_timestamp=datetime.now(),
                description=description,
                tags=tags or []
            )
            
            # Store in database
            self._store_model_version(model_version)
            
            # Record history
            self._record_history(model_id, "model_saved", version, "system", {
                "model_name": model_name,
                "performance_metrics": performance_metrics,
                "file_size": file_size
            })
            
            # Auto-cleanup old versions if enabled
            if self.auto_cleanup_enabled:
                self._cleanup_old_versions(model_id)
            
            self.logger.info(f"Model saved successfully: {model_id} v{version}")
            return model_version
            
        except Exception as e:
            self.logger.error(f"Error saving model {model_name}: {e}")
            raise
    
    def load_model(self, model_id: str, version: Optional[str] = None) -> Tuple[Any, ModelVersion]:
        """Load a specific model version"""
        try:
            # Get model version info
            if version is None:
                model_version = self._get_latest_version(model_id)
            else:
                model_version = self._get_model_version(model_id, version)
            
            if not model_version:
                raise ValueError(f"Model not found: {model_id} v{version}")
            
            # Verify file exists and integrity
            file_path = Path(model_version.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Model file not found: {file_path}")
            
            # Verify file integrity
            current_hash = self._calculate_file_hash(file_path)
            if current_hash != model_version.file_hash:
                raise ValueError(f"Model file integrity check failed: {file_path}")
            
            # Load model
            with open(file_path, 'rb') as f:
                model = pickle.load(f)
            
            self.logger.info(f"Model loaded successfully: {model_id} v{model_version.version}")
            return model, model_version
            
        except Exception as e:
            self.logger.error(f"Error loading model {model_id} v{version}: {e}")
            raise
    
    def deploy_model(self, model_id: str, version: str, environment: str = "production",
                    deployment_config: Optional[Dict[str, Any]] = None) -> ModelDeployment:
        """Deploy a model version to specified environment"""
        try:
            self.logger.info(f"Deploying model: {model_id} v{version} to {environment}")
            
            # Verify model exists
            model_version = self._get_model_version(model_id, version)
            if not model_version:
                raise ValueError(f"Model version not found: {model_id} v{version}")
            
            # Check if model is ready for deployment
            if model_version.status == ModelStatus.DEVELOPMENT:
                raise ValueError(f"Model {model_id} v{version} is still in development")
            
            # Get current deployment for rollback
            current_deployment = self._get_current_deployment(model_id, environment)
            rollback_version = current_deployment.version if current_deployment else None
            
            # Create deployment with microseconds to avoid duplicates
            deployment_id = f"{model_id}_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            deployment = ModelDeployment(
                deployment_id=deployment_id,
                model_id=model_id,
                version=version,
                environment=environment,
                status=ModelStatus.PRODUCTION if environment == "production" else ModelStatus.STAGING,
                deployment_timestamp=datetime.now(),
                rollback_version=rollback_version,
                deployment_config=deployment_config or {}
            )
            
            # Perform health check
            health_check_results = self._perform_health_check(model_id, version)
            deployment.health_check_results = health_check_results
            
            if not health_check_results.get('healthy', False):
                raise ValueError(f"Health check failed for model {model_id} v{version}")
            
            # Store deployment
            self._store_deployment(deployment)
            
            # Update model status
            self._update_model_status(model_id, version, deployment.status)
            
            # Update current deployments cache
            self._current_deployments[f"{model_id}_{environment}"] = deployment
            
            # Record history
            self._record_history(model_id, "model_deployed", version, "system", {
                "environment": environment,
                "deployment_id": deployment_id,
                "rollback_version": rollback_version,
                "health_check": health_check_results
            })
            
            self.logger.info(f"Model deployed successfully: {deployment_id}")
            return deployment
            
        except Exception as e:
            self.logger.error(f"Error deploying model {model_id} v{version}: {e}")
            raise
    
    def rollback_model(self, model_id: str, environment: str = "production",
                      target_version: Optional[str] = None) -> ModelDeployment:
        """Rollback model to previous or specified version"""
        try:
            self.logger.info(f"Rolling back model: {model_id} in {environment}")
            
            # Get current deployment
            current_deployment = self._get_current_deployment(model_id, environment)
            if not current_deployment:
                raise ValueError(f"No current deployment found for {model_id} in {environment}")
            
            # Determine rollback version
            if target_version:
                rollback_version = target_version
            elif current_deployment.rollback_version:
                rollback_version = current_deployment.rollback_version
            else:
                # Find previous version
                rollback_version = self._get_previous_version(model_id, current_deployment.version)
                if not rollback_version:
                    raise ValueError(f"No rollback version available for {model_id}")
            
            # Verify rollback version exists
            rollback_model_version = self._get_model_version(model_id, rollback_version)
            if not rollback_model_version:
                raise ValueError(f"Rollback version not found: {model_id} v{rollback_version}")
            
            # Perform rollback deployment
            rollback_deployment = self.deploy_model(
                model_id, rollback_version, environment,
                current_deployment.deployment_config
            )
            
            # Record rollback history
            self._record_history(model_id, "model_rolled_back", rollback_version, "system", {
                "environment": environment,
                "from_version": current_deployment.version,
                "to_version": rollback_version,
                "reason": "manual_rollback"
            })
            
            self.logger.info(f"Model rolled back successfully: {model_id} from v{current_deployment.version} to v{rollback_version}")
            return rollback_deployment
            
        except Exception as e:
            self.logger.error(f"Error rolling back model {model_id}: {e}")
            raise
    
    def list_models(self, status_filter: Optional[ModelStatus] = None,
                   model_type_filter: Optional[ModelType] = None) -> List[ModelVersion]:
        """List all models with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM model_versions WHERE 1=1"
            params = []
            
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter.value)
            
            if model_type_filter:
                query += " AND model_type = ?"
                params.append(model_type_filter.value)
            
            query += " ORDER BY training_timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            models = []
            for row in rows:
                model_version = self._row_to_model_version(row)
                models.append(model_version)
            
            conn.close()
            return models
            
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []
    
    def get_model_history(self, model_id: str, limit: int = 50) -> List[ModelHistory]:
        """Get model history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM model_history 
                WHERE model_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (model_id, limit))
            
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history_item = ModelHistory(
                    model_id=row[1],
                    action=row[2],
                    version=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    user=row[5],
                    details=json.loads(row[6]),
                    previous_state=json.loads(row[7]) if row[7] else None
                )
                history.append(history_item)
            
            conn.close()
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting model history for {model_id}: {e}")
            return []
    
    def delete_model_version(self, model_id: str, version: str, force: bool = False) -> bool:
        """Delete a specific model version"""
        try:
            self.logger.info(f"Deleting model version: {model_id} v{version}")
            
            # Check if version is currently deployed
            if not force:
                deployments = self._get_active_deployments(model_id, version)
                if deployments:
                    raise ValueError(f"Cannot delete deployed model version: {model_id} v{version}")
            
            # Get model version info
            model_version = self._get_model_version(model_id, version)
            if not model_version:
                raise ValueError(f"Model version not found: {model_id} v{version}")
            
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup(model_version)
            
            # Delete model file
            file_path = Path(model_version.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM model_versions WHERE model_id = ? AND version = ?',
                         (model_id, version))
            
            conn.commit()
            conn.close()
            
            # Record history
            self._record_history(model_id, "model_deleted", version, "system", {
                "file_path": str(file_path),
                "backup_created": self.backup_enabled,
                "force_delete": force
            })
            
            self.logger.info(f"Model version deleted successfully: {model_id} v{version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting model version {model_id} v{version}: {e}")
            return False
    
    def get_model_metrics(self, model_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive model metrics"""
        try:
            if version is None:
                model_version = self._get_latest_version(model_id)
            else:
                model_version = self._get_model_version(model_id, version)
            
            if not model_version:
                return {}
            
            # Get deployment info
            deployments = self._get_model_deployments(model_id, version)
            
            # Get history
            history = self.get_model_history(model_id, limit=10)
            
            metrics = {
                "model_info": {
                    "model_id": model_version.model_id,
                    "version": model_version.version,
                    "name": model_version.model_name,
                    "type": model_version.model_type.value,
                    "status": model_version.status.value,
                    "file_size": model_version.file_size,
                    "training_timestamp": model_version.training_timestamp.isoformat()
                },
                "performance_metrics": model_version.performance_metrics,
                "deployment_info": {
                    "total_deployments": len(deployments),
                    "active_deployments": len([d for d in deployments if d.status in [ModelStatus.PRODUCTION, ModelStatus.STAGING]]),
                    "environments": list(set([d.environment for d in deployments]))
                },
                "history_summary": {
                    "total_actions": len(history),
                    "recent_actions": [{"action": h.action, "timestamp": h.timestamp.isoformat()} for h in history[:5]]
                },
                "metadata": model_version.metadata
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting model metrics for {model_id}: {e}")
            return {}
    
    def list_models(self) -> List[ModelVersion]:
        """List all available models"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT model_id, version, model_name, model_type, status, file_path,
                       file_hash, file_size, metadata, performance_metrics,
                       training_timestamp, deployment_timestamp, created_by, description
                FROM model_versions
                ORDER BY training_timestamp DESC
            """)
            
            rows = cursor.fetchall()
            models = []
            
            for row in rows:
                try:
                    metadata = json.loads(row[8]) if row[8] else {}
                    performance_metrics = json.loads(row[9]) if row[9] else {}
                    
                    model_version = ModelVersion(
                        model_id=row[0],
                        version=row[1],
                        model_name=row[2],
                        model_type=ModelType(row[3]),
                        status=ModelStatus(row[4]),
                        file_path=row[5],
                        file_hash=row[6],
                        file_size=row[7],
                        metadata=metadata,
                        performance_metrics=performance_metrics,
                        training_timestamp=datetime.fromisoformat(row[10]),
                        deployment_timestamp=datetime.fromisoformat(row[11]) if row[11] else None,
                        created_by=row[12] or "system",
                        description=row[13] or ""
                    )
                    models.append(model_version)
                    
                except Exception as model_error:
                    self.logger.warning(f"Error parsing model record: {model_error}")
                    continue
            
            conn.close()
            return models
            
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []
    
    def cleanup_old_versions(self, model_id: Optional[str] = None, keep_versions: int = None) -> Dict[str, int]:
        """Cleanup old model versions"""
        try:
            keep_count = keep_versions or self.max_versions_per_model
            cleanup_stats = {"deleted_versions": 0, "freed_space": 0}
            
            if model_id:
                model_ids = [model_id]
            else:
                # Get all model IDs
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT model_id FROM model_versions')
                model_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            for mid in model_ids:
                deleted_count, freed_space = self._cleanup_old_versions(mid, keep_count)
                cleanup_stats["deleted_versions"] += deleted_count
                cleanup_stats["freed_space"] += freed_space
            
            self.logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {"deleted_versions": 0, "freed_space": 0}
    
    def _generate_model_id(self, model_name: str) -> str:
        """Generate unique model ID"""
        # Check if model with this name already exists
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Look for existing models with same name
            cursor.execute('SELECT model_id FROM model_versions WHERE model_name = ? LIMIT 1', (model_name,))
            existing = cursor.fetchone()
            
            conn.close()
            
            if existing:
                return existing[0]  # Return existing model_id for same model name
            else:
                # Generate new unique ID
                timestamp = datetime.now().isoformat()
                hash_input = f"{model_name}_{timestamp}"
                model_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
                return f"{model_name.replace(' ', '_').lower()}_{model_hash}"
                
        except Exception:
            # Fallback to timestamp-based ID
            timestamp = datetime.now().isoformat()
            hash_input = f"{model_name}_{timestamp}"
            model_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            return f"{model_name.replace(' ', '_').lower()}_{model_hash}"
    
    def _generate_version(self, model_id: str) -> str:
        """Generate next version number for model"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all versions for this model and find the max numeric version
            cursor.execute('SELECT version FROM model_versions WHERE model_id = ?', (model_id,))
            versions = cursor.fetchall()
            
            max_version = 0
            for version_row in versions:
                version_str = version_row[0]
                try:
                    version_num = int(version_str)
                    max_version = max(max_version, version_num)
                except ValueError:
                    continue  # Skip non-numeric versions
            
            conn.close()
            return str(max_version + 1)
            
        except Exception:
            # Fallback to version 1
            return "1"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _perform_health_check(self, model_id: str, version: str) -> Dict[str, Any]:
        """Perform health check on model"""
        try:
            # Load model to verify it works
            model, model_version = self.load_model(model_id, version)
            
            health_check = {
                "healthy": True,
                "checks": {
                    "file_exists": True,
                    "file_integrity": True,
                    "model_loadable": True,
                    "has_predict_method": hasattr(model, 'predict'),
                    "file_size_reasonable": model_version.file_size < 1024 * 1024 * 100  # 100MB limit
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if all critical checks pass
            critical_checks = ["file_exists", "file_integrity", "model_loadable", "has_predict_method"]
            health_check["healthy"] = all(health_check["checks"][check] for check in critical_checks)
            
            return health_check
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "checks": {"file_exists": False, "file_integrity": False, "model_loadable": False},
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_latest_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get latest version of a model"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all versions for model
            cursor.execute('SELECT * FROM model_versions WHERE model_id = ?', (model_id,))
            all_rows = cursor.fetchall()
            
            if not all_rows:
                conn.close()
                return None
            
            # Sort by version number (numeric) and get latest
            latest_row = None
            latest_version = -1
            
            for row in all_rows:
                try:
                    version_num = int(row[2])  # version is at index 2
                    if version_num > latest_version:
                        latest_version = version_num
                        latest_row = row
                except ValueError:
                    continue  # Skip non-numeric versions
            
            conn.close()
            
            if latest_row:
                return self._row_to_model_version(latest_row)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest version for {model_id}: {e}")
            return None
    
    def _get_model_version(self, model_id: str, version: str) -> Optional[ModelVersion]:
        """Get specific model version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM model_versions WHERE model_id = ? AND version = ?',
                         (model_id, version))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_model_version(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting model version {model_id} v{version}: {e}")
            return None
    
    def _get_current_deployment(self, model_id: str, environment: str) -> Optional[ModelDeployment]:
        """Get current deployment for model in environment"""
        cache_key = f"{model_id}_{environment}"
        return self._current_deployments.get(cache_key)
    
    def _get_previous_version(self, model_id: str, current_version: str) -> Optional[str]:
        """Get previous version before current version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all versions and find the one before current
            cursor.execute('SELECT version FROM model_versions WHERE model_id = ?', (model_id,))
            versions = cursor.fetchall()
            
            # Convert to integers and sort
            numeric_versions = []
            for v in versions:
                try:
                    numeric_versions.append(int(v[0]))
                except ValueError:
                    continue
            
            numeric_versions.sort(reverse=True)
            current_version_num = int(current_version)
            
            # Find previous version
            previous_version = None
            for v in numeric_versions:
                if v < current_version_num:
                    previous_version = str(v)
                    break
            
            conn.close()
            
            return previous_version
            
        except Exception as e:
            self.logger.error(f"Error getting previous version for {model_id}: {e}")
            return None
    
    def _get_active_deployments(self, model_id: str, version: str) -> List[ModelDeployment]:
        """Get active deployments for model version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM model_deployments 
                WHERE model_id = ? AND version = ? AND status IN ('production', 'staging')
            ''', (model_id, version))
            
            rows = cursor.fetchall()
            conn.close()
            
            deployments = []
            for row in rows:
                deployment = self._row_to_deployment(row)
                deployments.append(deployment)
            
            return deployments
            
        except Exception as e:
            self.logger.error(f"Error getting active deployments: {e}")
            return []
    
    def _get_model_deployments(self, model_id: str, version: Optional[str] = None) -> List[ModelDeployment]:
        """Get all deployments for model"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if version:
                cursor.execute('SELECT * FROM model_deployments WHERE model_id = ? AND version = ?',
                             (model_id, version))
            else:
                cursor.execute('SELECT * FROM model_deployments WHERE model_id = ?', (model_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            deployments = []
            for row in rows:
                deployment = self._row_to_deployment(row)
                deployments.append(deployment)
            
            return deployments
            
        except Exception as e:
            self.logger.error(f"Error getting model deployments: {e}")
            return []
    
    def _cleanup_old_versions(self, model_id: str, keep_versions: int = None) -> Tuple[int, int]:
        """Cleanup old versions for specific model"""
        try:
            keep_count = keep_versions or self.max_versions_per_model
            
            # Get all versions for model, sorted by version number
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all versions for model
            cursor.execute('SELECT model_id, version, file_path, file_size FROM model_versions WHERE model_id = ?', (model_id,))
            all_rows = cursor.fetchall()
            
            # Sort by version number (numeric)
            rows = []
            for row in all_rows:
                try:
                    version_num = int(row[1])
                    rows.append((row, version_num))
                except ValueError:
                    continue  # Skip non-numeric versions
            
            # Sort by version number descending
            rows.sort(key=lambda x: x[1], reverse=True)
            rows = [row[0] for row in rows]  # Extract just the row data
            
            rows = cursor.fetchall()
            
            if len(rows) <= keep_count:
                conn.close()
                return 0, 0  # Nothing to cleanup
            
            # Identify versions to delete (keep the latest N versions)
            versions_to_delete = rows[keep_count:]
            deleted_count = 0
            freed_space = 0
            
            for row in versions_to_delete:
                version = row[1]
                file_path = row[2]
                file_size = row[3]
                
                # Check if version is deployed
                active_deployments = self._get_active_deployments(model_id, version)
                if active_deployments:
                    continue  # Skip deployed versions
                
                # Delete file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    freed_space += file_size
                
                # Delete from database
                cursor.execute('DELETE FROM model_versions WHERE model_id = ? AND version = ?',
                             (model_id, version))
                
                deleted_count += 1
                
                # Record history
                self._record_history(model_id, "version_cleaned_up", version, "system", {
                    "reason": "automatic_cleanup",
                    "file_size": file_size
                })
            
            conn.commit()
            conn.close()
            
            return deleted_count, freed_space
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions for {model_id}: {e}")
            return 0, 0
    
    def _create_backup(self, model_version: ModelVersion):
        """Create backup of model version"""
        try:
            backup_dir = self.models_directory / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            source_path = Path(model_version.file_path)
            backup_path = backup_dir / f"{model_version.model_id}_v{model_version.version}_backup.pkl"
            
            shutil.copy2(source_path, backup_path)
            
            self.logger.info(f"Backup created: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {model_version.model_id}: {e}")
    
    def _update_model_status(self, model_id: str, version: str, status: ModelStatus):
        """Update model status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE model_versions 
                SET status = ? 
                WHERE model_id = ? AND version = ?
            ''', (status.value, model_id, version))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating model status: {e}")
    
    def _load_current_deployments(self):
        """Load current deployments into cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest deployment for each model-environment combination
            cursor.execute('''
                SELECT d1.* FROM model_deployments d1
                INNER JOIN (
                    SELECT model_id, environment, MAX(deployment_timestamp) as max_timestamp
                    FROM model_deployments
                    WHERE status IN ('production', 'staging')
                    GROUP BY model_id, environment
                ) d2 ON d1.model_id = d2.model_id 
                    AND d1.environment = d2.environment 
                    AND d1.deployment_timestamp = d2.max_timestamp
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                deployment = self._row_to_deployment(row)
                cache_key = f"{deployment.model_id}_{deployment.environment}"
                self._current_deployments[cache_key] = deployment
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error loading current deployments: {e}")
    
    def _store_model_version(self, model_version: ModelVersion):
        """Store model version in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_versions (
                    model_id, version, model_name, model_type, status,
                    file_path, file_hash, file_size, metadata, performance_metrics,
                    training_timestamp, deployment_timestamp, created_by, description, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_version.model_id,
                model_version.version,
                model_version.model_name,
                model_version.model_type.value,
                model_version.status.value,
                model_version.file_path,
                model_version.file_hash,
                model_version.file_size,
                json.dumps(model_version.metadata),
                json.dumps(model_version.performance_metrics),
                model_version.training_timestamp.isoformat(),
                model_version.deployment_timestamp.isoformat() if model_version.deployment_timestamp else None,
                model_version.created_by,
                model_version.description,
                json.dumps(model_version.tags)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing model version: {e}")
            raise
    
    def _store_deployment(self, deployment: ModelDeployment):
        """Store deployment in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_deployments (
                    deployment_id, model_id, version, environment, status,
                    deployment_timestamp, rollback_version, deployment_config, health_check_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deployment.deployment_id,
                deployment.model_id,
                deployment.version,
                deployment.environment,
                deployment.status.value,
                deployment.deployment_timestamp.isoformat(),
                deployment.rollback_version,
                json.dumps(deployment.deployment_config),
                json.dumps(deployment.health_check_results)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing deployment: {e}")
            raise
    
    def _record_history(self, model_id: str, action: str, version: str, user: str, details: Dict[str, Any]):
        """Record model history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_history (
                    model_id, action, version, timestamp, user, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                model_id,
                action,
                version,
                datetime.now().isoformat(),
                user,
                json.dumps(details)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error recording history: {e}")
    
    def _row_to_model_version(self, row) -> ModelVersion:
        """Convert database row to ModelVersion object"""
        return ModelVersion(
            model_id=row[1],
            version=row[2],
            model_name=row[3],
            model_type=ModelType(row[4]),
            status=ModelStatus(row[5]),
            file_path=row[6],
            file_hash=row[7],
            file_size=row[8],
            metadata=json.loads(row[9]) if row[9] else {},
            performance_metrics=json.loads(row[10]) if row[10] else {},
            training_timestamp=datetime.fromisoformat(row[11]),
            deployment_timestamp=datetime.fromisoformat(row[12]) if row[12] else None,
            created_by=row[13] or "system",
            description=row[14] or "",
            tags=json.loads(row[15]) if row[15] else []
        )
    
    def _row_to_deployment(self, row) -> ModelDeployment:
        """Convert database row to ModelDeployment object"""
        return ModelDeployment(
            deployment_id=row[1],
            model_id=row[2],
            version=row[3],
            environment=row[4],
            status=ModelStatus(row[5]),
            deployment_timestamp=datetime.fromisoformat(row[6]),
            rollback_version=row[7],
            deployment_config=json.loads(row[8]) if row[8] else {},
            health_check_results=json.loads(row[9]) if row[9] else {}
        )
    
    def _init_model_tables(self):
        """Initialize database tables for model management"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Model versions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    metadata TEXT,
                    performance_metrics TEXT,
                    training_timestamp DATETIME NOT NULL,
                    deployment_timestamp DATETIME,
                    created_by TEXT DEFAULT 'system',
                    description TEXT,
                    tags TEXT,
                    UNIQUE(model_id, version)
                )
            ''')
            
            # Model deployments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deployment_id TEXT UNIQUE NOT NULL,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deployment_timestamp DATETIME NOT NULL,
                    rollback_version TEXT,
                    deployment_config TEXT,
                    health_check_results TEXT
                )
            ''')
            
            # Model history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user TEXT NOT NULL,
                    details TEXT,
                    previous_state TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_versions_id ON model_versions(model_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_deployments_id ON model_deployments(model_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_history_id ON model_history(model_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_deployments_env ON model_deployments(environment)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Model management database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing model tables: {e}")
            raise


# Utility functions for model management
def create_sample_model():
    """Create a sample model for testing"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    
    # Generate sample data
    X, y = make_classification(n_samples=100, n_features=10, random_state=42)
    
    # Create and train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    return model, {"accuracy": 0.95, "precision": 0.94, "recall": 0.96}


if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create model manager
    model_manager = ModelManager()
    
    # Create sample model
    model, metrics = create_sample_model()
    
    # Save model
    model_version = model_manager.save_model(
        model, "sample_classifier", ModelType.CLASSIFICATION,
        metrics, {"algorithm": "RandomForest", "n_estimators": 10},
        "Sample classification model for testing"
    )
    
    print(f"Model saved: {model_version.model_id} v{model_version.version}")
    
    # Load model
    loaded_model, loaded_version = model_manager.load_model(model_version.model_id)
    print(f"Model loaded: {loaded_version.model_name}")
    
    # Update status to testing
    model_manager._update_model_status(model_version.model_id, model_version.version, ModelStatus.TESTING)
    
    # Deploy model
    deployment = model_manager.deploy_model(
        model_version.model_id, model_version.version, "staging"
    )
    print(f"Model deployed: {deployment.deployment_id}")
    
    # Get model metrics
    metrics = model_manager.get_model_metrics(model_version.model_id)
    print(f"Model metrics: {metrics}")
    
    # List models
    models = model_manager.list_models()
    print(f"Total models: {len(models)}")
    
    print("Model Manager testing completed!")