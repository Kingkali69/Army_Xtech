#!/usr/bin/env python3
"""
KK&G DevOps Cybersecurity Engine - Complete Backend Ecosystem
=============================================================
Enterprise backend architecture supporting the v3 Plugin Framework:
- Plugin Marketplace (distribution, discovery, monetization)
- Enterprise Integration Layers (SIEM, ML, licensing)
- Multi-Platform Adapter Orchestration (cross-platform sync)
- Cloud-Native Infrastructure (microservices, APIs, databases)
"""

import asyncio
import aiohttp
import asyncpg
import redis.asyncio as redis
import json
import uuid
import hashlib
import hmac
import jwt
import base64
import zipfile
import tarfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, AsyncIterator
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from decimal import Decimal
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel, validator
import boto3
import docker
from kubernetes import client, config
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import stripe
import requests

# ============================================================================
# CORE BACKEND DATA MODELS
# ============================================================================

class PlatformType(Enum):
    """Supported platform types"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    CLOUD_AWS = "cloud_aws"
    CLOUD_AZURE = "cloud_azure"
    CLOUD_GCP = "cloud_gcp"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"

class DeploymentTier(Enum):
    """Deployment tier levels"""
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"

class MarketplaceStatus(Enum):
    """Plugin marketplace status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"

@dataclass
class PlatformCapabilities:
    """Platform-specific capabilities and constraints"""
    platform_type: PlatformType
    supported_architectures: List[str]  # x86_64, arm64, etc.
    os_versions: List[str]
    container_support: bool
    gpu_acceleration: bool
    hardware_security: bool  # TPM, Secure Enclave, etc.
    network_capabilities: Dict[str, bool]
    storage_types: List[str]
    max_memory_gb: Optional[int] = None
    max_cpu_cores: Optional[int] = None

@dataclass
class MarketplacePlugin:
    """Plugin metadata for marketplace"""
    plugin_id: str
    name: str
    version: str
    author: str
    organization: str
    description: str
    long_description: str
    category: str
    subcategory: str
    tags: List[str]
    price: Decimal  # 0 for free plugins
    license_type: str
    
    # Platform support
    supported_platforms: List[PlatformCapabilities]
    minimum_framework_version: str
    
    # Distribution
    download_url: str
    checksum_sha256: str
    signature: str  # Digital signature
    size_bytes: int
    
    # Marketplace metadata
    status: MarketplaceStatus
    published_date: Optional[datetime]
    last_updated: datetime
    download_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    
    # Monetization
    pricing_model: str  # "one_time", "subscription", "usage_based"
    subscription_period: Optional[str] = None  # "monthly", "yearly"
    trial_period_days: int = 0
    
    # Compliance & Security
    security_scan_status: str = "pending"
    compliance_certifications: List[str] = field(default_factory=list)
    vulnerability_score: Optional[float] = None
    
    # Analytics
    usage_analytics: bool = True
    telemetry_collection: bool = False

@dataclass
class LicenseKey:
    """Software license key management"""
    license_id: str
    plugin_id: str
    customer_id: str
    license_type: str  # "trial", "standard", "enterprise", "unlimited"
    
    # Validity
    issued_date: datetime
    expires_date: Optional[datetime]
    max_installations: Optional[int]
    current_installations: int = 0
    
    # Feature flags
    features_enabled: Dict[str, bool]
    usage_limits: Dict[str, Any]
    
    # Status
    is_active: bool = True
    revocation_reason: Optional[str] = None
    
    # Hardware binding
    hardware_fingerprints: List[str] = field(default_factory=list)
    allow_vm_deployment: bool = True

@dataclass
class DeploymentInstance:
    """Individual deployment instance"""
    instance_id: str
    organization_id: str
    deployment_name: str
    platform_type: PlatformType
    deployment_tier: DeploymentTier
    
    # Location & Infrastructure
    region: str
    availability_zone: Optional[str]
    infrastructure_provider: str  # "aws", "azure", "gcp", "on_premise"
    
    # Configuration
    installed_plugins: List[str]
    configuration_profile: str
    resource_allocation: Dict[str, Any]
    
    # Status
    status: str  # "running", "stopped", "updating", "error"
    last_heartbeat: datetime
    version: str
    
    # Networking
    endpoints: List[str]
    vpn_config: Optional[Dict[str, Any]]
    firewall_rules: List[Dict[str, Any]]
    
    # Monitoring
    metrics_collection: bool = True
    log_retention_days: int = 30
    
    # Security
    encryption_enabled: bool = True
    certificate_info: Optional[Dict[str, Any]] = None

# ============================================================================
# PLUGIN MARKETPLACE BACKEND
# ============================================================================

class PluginMarketplaceAPI:
    """Central API for plugin marketplace operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_pool = None
        self.redis_client = None
        self.s3_client = boto3.client('s3')
        self.stripe_client = stripe
        self.signing_key = self._load_signing_key()
        
    async def initialize(self):
        """Initialize backend connections"""
        # PostgreSQL connection pool
        self.db_pool = await asyncpg.create_pool(
            host=self.config['database']['host'],
            port=self.config['database']['port'],
            database=self.config['database']['name'],
            user=self.config['database']['user'],
            password=self.config['database']['password'],
            min_size=5,
            max_size=20
        )
        
        # Redis connection
        self.redis_client = redis.Redis(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            password=self.config['redis']['password']
        )
        
        # Initialize database schema
        await self._create_database_schema()
        
        logging.info("✅ Plugin Marketplace API initialized")
    
    async def publish_plugin(self, plugin_data: MarketplacePlugin, 
                           plugin_file: bytes) -> Dict[str, Any]:
        """Publish a new plugin to the marketplace"""
        try:
            # Security scan
            scan_results = await self._security_scan_plugin(plugin_file)
            if scan_results['risk_level'] == 'high':
                return {'error': 'Plugin failed security scan', 'details': scan_results}
            
            # Code review (if required)
            if plugin_data.price > 0 or plugin_data.license_type == 'enterprise':
                review_status = await self._queue_code_review(plugin_data.plugin_id)
                plugin_data.status = MarketplaceStatus.PENDING_REVIEW
            else:
                plugin_data.status = MarketplaceStatus.APPROVED
            
            # Store plugin file
            storage_path = await self._store_plugin_file(
                plugin_data.plugin_id, 
                plugin_data.version, 
                plugin_file
            )
            
            # Generate digital signature
            signature = self._sign_plugin(plugin_file)
            plugin_data.signature = signature
            plugin_data.download_url = storage_path
            plugin_data.size_bytes = len(plugin_file)
            plugin_data.checksum_sha256 = hashlib.sha256(plugin_file).hexdigest()
            
            # Store in database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO marketplace_plugins 
                    (plugin_id, name, version, author, organization, description, 
                     long_description, category, subcategory, tags, price, 
                     license_type, supported_platforms, minimum_framework_version,
                     download_url, checksum_sha256, signature, size_bytes, 
                     status, published_date, last_updated, pricing_model,
                     trial_period_days, security_scan_status, vulnerability_score)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 
                            $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
                """, 
                plugin_data.plugin_id, plugin_data.name, plugin_data.version,
                plugin_data.author, plugin_data.organization, plugin_data.description,
                plugin_data.long_description, plugin_data.category, 
                plugin_data.subcategory, json.dumps(plugin_data.tags),
                str(plugin_data.price), plugin_data.license_type,
                json.dumps([asdict(p) for p in plugin_data.supported_platforms]),
                plugin_data.minimum_framework_version, plugin_data.download_url,
                plugin_data.checksum_sha256, plugin_data.signature,
                plugin_data.size_bytes, plugin_data.status.value,
                plugin_data.published_date, plugin_data.last_updated,
                plugin_data.pricing_model, plugin_data.trial_period_days,
                plugin_data.security_scan_status, plugin_data.vulnerability_score
                )
            
            # Cache popular queries
            await self._update_search_cache(plugin_data)
            
            # Notify subscribers
            await self._notify_plugin_published(plugin_data)
            
            return {
                'success': True,
                'plugin_id': plugin_data.plugin_id,
                'status': plugin_data.status.value,
                'download_url': plugin_data.download_url
            }
            
        except Exception as e:
            logging.error(f"Plugin publication failed: {e}")
            return {'error': str(e)}
    
    async def search_plugins(self, query: str, filters: Dict[str, Any],
                           platform: PlatformType, page: int = 1, 
                           page_size: int = 20) -> Dict[str, Any]:
        """Search plugins in marketplace"""
        try:
            # Check cache first
            cache_key = f"search:{hashlib.md5(f'{query}{json.dumps(filters)}{platform.value}{page}{page_size}'.encode()).hexdigest()}"
            cached_result = await self.redis_client.get(cache_key)
            
            if cached_result:
                return json.loads(cached_result)
            
            # Build query
            where_conditions = ["status = 'published'"]
            params = []
            param_count = 0
            
            if query:
                param_count += 1
                where_conditions.append(f"(name ILIKE ${param_count} OR description ILIKE ${param_count} OR tags::text ILIKE ${param_count})")
                params.append(f"%{query}%")
            
            if filters.get('category'):
                param_count += 1
                where_conditions.append(f"category = ${param_count}")
                params.append(filters['category'])
            
            if filters.get('price_range'):
                price_min, price_max = filters['price_range']
                param_count += 1
                where_conditions.append(f"price >= ${param_count}")
                params.append(str(price_min))
                param_count += 1
                where_conditions.append(f"price <= ${param_count}")
                params.append(str(price_max))
            
            # Platform compatibility
            param_count += 1
            where_conditions.append(f"supported_platforms::text ILIKE ${param_count}")
            params.append(f"%{platform.value}%")
            
            # Execute query
            offset = (page - 1) * page_size
            where_clause = " AND ".join(where_conditions)
            
            async with self.db_pool.acquire() as conn:
                # Get total count
                count_query = f"SELECT COUNT(*) FROM marketplace_plugins WHERE {where_clause}"
                total_count = await conn.fetchval(count_query, *params)
                
                # Get plugins
                search_query = f"""
                    SELECT plugin_id, name, version, author, organization, description,
                           category, subcategory, tags, price, license_type,
                           download_count, rating, review_count, published_date
                    FROM marketplace_plugins 
                    WHERE {where_clause}
                    ORDER BY 
                        CASE WHEN $1 IS NOT NULL THEN rating * download_count END DESC,
                        published_date DESC
                    LIMIT ${param_count + 1} OFFSET ${param_count + 2}
                """
                params.extend([page_size, offset])
                
                rows = await conn.fetch(search_query, query, *params[1:])
                
                plugins = []
                for row in rows:
                    plugin_dict = dict(row)
                    plugin_dict['tags'] = json.loads(plugin_dict['tags'])
                    plugin_dict['price'] = float(plugin_dict['price'])
                    plugin_dict['published_date'] = plugin_dict['published_date'].isoformat() if plugin_dict['published_date'] else None
                    plugins.append(plugin_dict)
                
                result = {
                    'plugins': plugins,
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
                
                # Cache result
                await self.redis_client.setex(cache_key, 300, json.dumps(result))  # 5 min cache
                
                return result
                
        except Exception as e:
            logging.error(f"Plugin search failed: {e}")
            return {'error': str(e)}
    
    async def purchase_plugin(self, plugin_id: str, customer_id: str,
                            payment_method: str) -> Dict[str, Any]:
        """Handle plugin purchase and license generation"""
        try:
            # Get plugin info
            async with self.db_pool.acquire() as conn:
                plugin_row = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1 AND status = 'published'",
                    plugin_id
                )
                
                if not plugin_row:
                    return {'error': 'Plugin not found or not available'}
                
                plugin_price = Decimal(plugin_row['price'])
                
                # Process payment (if not free)
                if plugin_price > 0:
                    payment_result = await self._process_payment(
                        customer_id, plugin_price, payment_method, plugin_id
                    )
                    if not payment_result['success']:
                        return payment_result
                    transaction_id = payment_result['transaction_id']
                else:
                    transaction_id = None
                
                # Generate license key
                license_key = await self._generate_license_key(
                    plugin_id, customer_id, plugin_row['license_type']
                )
                
                # Record purchase
                await conn.execute("""
                    INSERT INTO plugin_purchases 
                    (purchase_id, plugin_id, customer_id, transaction_id, license_key_id,
                     purchase_date, price_paid, payment_method)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, str(uuid.uuid4()), plugin_id, customer_id, transaction_id,
                license_key.license_id, datetime.now(), str(plugin_price), payment_method)
                
                # Update download count
                await conn.execute(
                    "UPDATE marketplace_plugins SET download_count = download_count + 1 WHERE plugin_id = $1",
                    plugin_id
                )
                
                return {
                    'success': True,
                    'license_key': asdict(license_key),
                    'download_url': await self._generate_download_url(plugin_id, license_key.license_id)
                }
                
        except Exception as e:
            logging.error(f"Plugin purchase failed: {e}")
            return {'error': str(e)}
    
    async def update_plugin(self, plugin_id: str, new_version: str,
                          plugin_file: bytes, author_id: str) -> Dict[str, Any]:
        """Update existing plugin with new version"""
        try:
            # Verify ownership
            async with self.db_pool.acquire() as conn:
                owner_check = await conn.fetchval(
                    "SELECT author FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id
                )
                
                if owner_check != author_id:
                    return {'error': 'Unauthorized: Not plugin owner'}
                
                # Security scan new version
                scan_results = await self._security_scan_plugin(plugin_file)
                if scan_results['risk_level'] == 'high':
                    return {'error': 'Plugin update failed security scan', 'details': scan_results}
                
                # Store new version
                storage_path = await self._store_plugin_file(plugin_id, new_version, plugin_file)
                signature = self._sign_plugin(plugin_file)
                checksum = hashlib.sha256(plugin_file).hexdigest()
                
                # Update database
                await conn.execute("""
                    UPDATE marketplace_plugins 
                    SET version = $2, download_url = $3, checksum_sha256 = $4, 
                        signature = $5, size_bytes = $6, last_updated = $7,
                        security_scan_status = $8, vulnerability_score = $9
                    WHERE plugin_id = $1
                """, plugin_id, new_version, storage_path, checksum, signature,
                len(plugin_file), datetime.now(), scan_results['status'], 
                scan_results.get('score'))
                
                # Notify existing users of update
                await self._notify_plugin_update(plugin_id, new_version)
                
                # Clear related caches
                await self._clear_plugin_cache(plugin_id)
                
                return {
                    'success': True,
                    'plugin_id': plugin_id,
                    'version': new_version,
                    'download_url': storage_path
                }
                
        except Exception as e:
            logging.error(f"Plugin update failed: {e}")
            return {'error': str(e)}
    
    # Private helper methods
    
    async def _security_scan_plugin(self, plugin_file: bytes) -> Dict[str, Any]:
        """Perform security scan on plugin"""
        # Implementation would include:
        # - Static code analysis
        # - Malware scanning
        # - Dependency vulnerability checking
        # - Permission analysis
        
        return {
            'status': 'passed',
            'risk_level': 'low',
            'score': 85.0,
            'issues_found': [],
            'scan_date': datetime.now().isoformat()
        }
    
    async def _store_plugin_file(self, plugin_id: str, version: str, 
                               plugin_file: bytes) -> str:
        """Store plugin file in S3/cloud storage"""
        key = f"plugins/{plugin_id}/{version}/plugin.kkg"
        
        self.s3_client.put_object(
            Bucket=self.config['storage']['bucket'],
            Key=key,
            Body=plugin_file,
            ServerSideEncryption='AES256',
            Metadata={
                'plugin-id': plugin_id,
                'version': version,
                'upload-date': datetime.now().isoformat()
            }
        )
        
        return f"https://{self.config['storage']['bucket']}.s3.amazonaws.com/{key}"
    
    def _sign_plugin(self, plugin_file: bytes) -> str:
        """Generate digital signature for plugin"""
        signature = self.signing_key.sign(
            plugin_file,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    async def _generate_license_key(self, plugin_id: str, customer_id: str,
                                  license_type: str) -> LicenseKey:
        """Generate software license key"""
        license_key = LicenseKey(
            license_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            customer_id=customer_id,
            license_type=license_type,
            issued_date=datetime.now(),
            expires_date=datetime.now() + timedelta(days=365) if license_type != 'unlimited' else None,
            max_installations=self._get_license_limits(license_type)['max_installations'],
            features_enabled=self._get_license_features(license_type),
            usage_limits=self._get_license_limits(license_type)
        )
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO license_keys 
                (license_id, plugin_id, customer_id, license_type, issued_date, 
                 expires_date, max_installations, features_enabled, usage_limits, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, license_key.license_id, license_key.plugin_id, license_key.customer_id,
            license_key.license_type, license_key.issued_date, license_key.expires_date,
            license_key.max_installations, json.dumps(license_key.features_enabled),
            json.dumps(license_key.usage_limits), license_key.is_active)
        
        return license_key
    
    def _get_license_limits(self, license_type: str) -> Dict[str, Any]:
        """Get license limits based on type"""
        limits = {
            'trial': {'max_installations': 1, 'max_events_per_day': 1000},
            'standard': {'max_installations': 3, 'max_events_per_day': 10000},
            'enterprise': {'max_installations': 100, 'max_events_per_day': -1},
            'unlimited': {'max_installations': -1, 'max_events_per_day': -1}
        }
        return limits.get(license_type, limits['trial'])
    
    def _get_license_features(self, license_type: str) -> Dict[str, bool]:
        """Get enabled features based on license type"""
        features = {
            'trial': {'advanced_analytics': False, 'custom_integrations': False, 'priority_support': False},
            'standard': {'advanced_analytics': True, 'custom_integrations': False, 'priority_support': False},
            'enterprise': {'advanced_analytics': True, 'custom_integrations': True, 'priority_support': True},
            'unlimited': {'advanced_analytics': True, 'custom_integrations': True, 'priority_support': True}
        }
        return features.get(license_type, features['trial'])
    
    async def _process_payment(self, customer_id: str, amount: Decimal,
                             payment_method: str, plugin_id: str) -> Dict[str, Any]:
        """Process payment through Stripe"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                customer=customer_id,
                payment_method=payment_method,
                metadata={'plugin_id': plugin_id},
                confirm=True
            )
            
            if intent.status == 'succeeded':
                return {'success': True, 'transaction_id': intent.id}
            else:
                return {'success': False, 'error': f'Payment {intent.status}'}
                
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    async def _create_database_schema(self):
        """Create database tables if they don't exist"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS marketplace_plugins (
            plugin_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(50) NOT NULL,
            author VARCHAR(255) NOT NULL,
            organization VARCHAR(255),
            description TEXT,
            long_description TEXT,
            category VARCHAR(100),
            subcategory VARCHAR(100),
            tags JSONB,
            price DECIMAL(10,2) DEFAULT 0,
            license_type VARCHAR(50),
            supported_platforms JSONB,
            minimum_framework_version VARCHAR(50),
            download_url TEXT,
            checksum_sha256 VARCHAR(64),
            signature TEXT,
            size_bytes INTEGER,
            status VARCHAR(50) DEFAULT 'draft',
            published_date TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            rating DECIMAL(3,2) DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            pricing_model VARCHAR(50) DEFAULT 'one_time',
            subscription_period VARCHAR(20),
            trial_period_days INTEGER DEFAULT 0,
            security_scan_status VARCHAR(50) DEFAULT 'pending',
            compliance_certifications JSONB DEFAULT '[]',
            vulnerability_score DECIMAL(5,2),
            usage_analytics BOOLEAN DEFAULT true,
            telemetry_collection BOOLEAN DEFAULT false
        );
        
        CREATE TABLE IF NOT EXISTS license_keys (
            license_id VARCHAR(255) PRIMARY KEY,
            plugin_id VARCHAR(255) REFERENCES marketplace_plugins(plugin_id),
            customer_id VARCHAR(255) NOT NULL,
            license_type VARCHAR(50) NOT NULL,
            issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_date TIMESTAMP,
            max_installations INTEGER,
            current_installations INTEGER DEFAULT 0,
            features_enabled JSONB,
            usage_limits JSONB,
            is_active BOOLEAN DEFAULT true,
            revocation_reason TEXT,
            hardware_fingerprints JSONB DEFAULT '[]',
            allow_vm_deployment BOOLEAN DEFAULT true
        );
        
        CREATE TABLE IF NOT EXISTS plugin_purchases (
            purchase_id VARCHAR(255) PRIMARY KEY,
            plugin_id VARCHAR(255) REFERENCES marketplace_plugins(plugin_id),
            customer_id VARCHAR(255) NOT NULL,
            transaction_id VARCHAR(255),
            license_key_id VARCHAR(255) REFERENCES license_keys(license_id),
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price_paid DECIMAL(10,2),
            payment_method VARCHAR(50)
        );
        
        CREATE TABLE IF NOT EXISTS deployment_instances (
            instance_id VARCHAR(255) PRIMARY KEY,
            organization_id VARCHAR(255) NOT NULL,
            deployment_name VARCHAR(255) NOT NULL,
            platform_type VARCHAR(50) NOT NULL,
            deployment_tier VARCHAR(50) NOT NULL,
            region VARCHAR(100),
            availability_zone VARCHAR(100),
            infrastructure_provider VARCHAR(50),
            installed_plugins JSONB DEFAULT '[]',
            configuration_profile VARCHAR(100),
            resource_allocation JSONB,
            status VARCHAR(50) DEFAULT 'stopped',
            last_heartbeat TIMESTAMP,
            version VARCHAR(50),
            endpoints JSONB DEFAULT '[]',
            vpn_config JSONB,
            firewall_rules JSONB DEFAULT '[]',
            metrics_collection BOOLEAN DEFAULT true,
            log_retention_days INTEGER DEFAULT 30,
            encryption_enabled BOOLEAN DEFAULT true,
            certificate_info JSONB,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_plugins_category ON marketplace_plugins(category);
        CREATE INDEX IF NOT EXISTS idx_plugins_status ON marketplace_plugins(status);
        CREATE INDEX IF NOT EXISTS idx_plugins_published ON marketplace_plugins(published_date);
        CREATE INDEX IF NOT EXISTS idx_licenses_customer ON license_keys(customer_id);
        CREATE INDEX IF NOT EXISTS idx_instances_org ON deployment_instances(organization_id);
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
    
    def _load_signing_key(self):
        """Load RSA private key for signing plugins"""
        key_path = Path(self.config['signing']['private_key_path'])
        if not key_path.exists():
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Save private key
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            public_key = private_key.public_key()
            pub_key_path = key_path.parent / 'public_key.pem'
            with open(pub_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            return private_key
        else:
            with open(key_path, 'rb') as f:
                return serialization.load_pem_private_key(
                    f.read(), 
                    password=None
                )

# ============================================================================
# ENTERPRISE INTEGRATION LAYERS
# ============================================================================

class SIEMConnectorHub:
    """Centralized SIEM integration management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connectors: Dict[str, Any] = {}
        self.message_queue = asyncio.Queue()
        self.integration_registry = {}
        
    async def register_siem_connector(self, siem_type: str, connector_class: type,
                                     connection_params: Dict[str, Any]) -> str:
        """Register a new SIEM connector"""
        connector_id = str(uuid.uuid4())
        
        try:
            # Initialize connector
            connector = connector_class(connection_params)
            await connector.initialize()
            
            # Test connection
            if not await connector.test_connection():
                raise ConnectionError(f"Failed to connect to {siem_type}")
            
            self.connectors[connector_id] = {
                'type': siem_type,
                'instance': connector,
                'status': 'active',
                'last_heartbeat': datetime.now(),
                'events_sent': 0,
                'errors': 0,
                'connection_params': connection_params
            }
            
            # Register in integration registry
            self.integration_registry[siem_type] = connector_id
            
            logging.info(f"✅ SIEM connector registered: {siem_type} ({connector_id})")
            return connector_id
            
        except Exception as e:
            logging.error(f"❌ Failed to register SIEM connector {siem_type}: {e}")
            raise
    
    async def send_security_event(self, event_data: Dict[str, Any], 
                                 target_siems: List[str] = None) -> Dict[str, Any]:
        """Send security event to SIEM systems"""
        results = {}
        
        # If no targets specified, send to all active connectors
        if target_siems is None:
            target_siems = list(self.integration_registry.keys())
        
        for siem_type in target_siems:
            connector_id = self.integration_registry.get(siem_type)
            if not connector_id or connector_id not in self.connectors:
                results[siem_type] = {'success': False, 'error': 'Connector not found'}
                continue
            
            connector_info = self.connectors[connector_id]
            
            try:
                # Transform event data to SIEM-specific format
                transformed_data = await self._transform_event_for_siem(
                    event_data, siem_type
                )
                
                # Send to SIEM
                success = await connector_info['instance'].send_event(transformed_data)
                
                if success:
                    connector_info['events_sent'] += 1
                    results[siem_type] = {'success': True}
                else:
                    connector_info['errors'] += 1
                    results[siem_type] = {'success': False, 'error': 'Send failed'}
                
                connector_info['last_heartbeat'] = datetime.now()
                
            except Exception as e:
                connector_info['errors'] += 1
                results[siem_type] = {'success': False, 'error': str(e)}
                logging.error(f"Failed to send event to {siem_type}: {e}")
        
        return results
    
    async def query_threat_intelligence(self, indicators: List[str],
                                      source_siems: List[str] = None) -> Dict[str, Any]:
        """Query threat intelligence from SIEM systems"""
        results = {}
        
        if source_siems is None:
            source_siems = list(self.integration_registry.keys())
        
        for siem_type in source_siems:
            connector_id = self.integration_registry.get(siem_type)
            if not connector_id or connector_id not in self.connectors:
                continue
            
            connector_info = self.connectors[connector_id]
            
            try:
                intel_data = await connector_info['instance'].query_threat_intel(indicators)
                results[siem_type] = intel_data
            except Exception as e:
                logging.error(f"Failed to query threat intel from {siem_type}: {e}")
                results[siem_type] = {'error': str(e)}
        
        return results
    
    async def _transform_event_for_siem(self, event_data: Dict[str, Any], 
                                       siem_type: str) -> Dict[str, Any]:
        """Transform generic event data to SIEM-specific format"""
        
        # Common transformations
        base_transform = {
            'timestamp': event_data.get('timestamp', datetime.now().isoformat()),
            'event_id': event_data.get('event_id'),
            'source_system': 'KKG-Security-Framework',
            'severity': event_data.get('severity', 'medium'),
            'event_type': event_data.get('event_type'),
            'raw_data': event_data
        }
        
        # SIEM-specific transformations
        if siem_type == 'splunk':
            return {
                'time': base_transform['timestamp'],
                'source': base_transform['source_system'],
                'sourcetype': 'kkg:security_event',
                'index': 'security',
                '_raw': json.dumps(base_transform),
                **event_data
            }
        
        elif siem_type == 'qradar':
            return {
                'magnitude': self._severity_to_magnitude(base_transform['severity']),
                'event_category_id': self._get_qradar_category(event_data.get('event_type')),
                'source_ip': event_data.get('source_ip'),
                'destination_ip': event_data.get('destination_ip'),
                'username': event_data.get('username'),
                'custom_properties': base_transform
            }
        
        elif siem_type == 'sentinel':
            return {
                'TimeGenerated': base_transform['timestamp'],
                'Computer': event_data.get('hostname', 'unknown'),
                'EventID': event_data.get('event_id'),
                'Level': base_transform['severity'],
                'EventData': json.dumps(base_transform)
            }
        
        elif siem_type == 'elastic':
            return {
                '@timestamp': base_transform['timestamp'],
                'agent': {'type': 'kkg-security'},
                'ecs': {'version': '8.0'},
                'event': {
                    'category': event_data.get('category', 'security'),
                    'type': event_data.get('event_type'),
                    'severity': self._severity_to_ecs_level(base_transform['severity'])
                },
                'kkg': base_transform
            }
        
        else:
            return base_transform
    
    def _severity_to_magnitude(self, severity: str) -> int:
        """Convert severity to QRadar magnitude"""
        mapping = {'low': 3, 'medium': 5, 'high': 7, 'critical': 9}
        return mapping.get(severity.lower(), 5)
    
    def _get_qradar_category(self, event_type: str) -> int:
        """Get QRadar event category ID"""
        categories = {
            'network_anomaly': 11000,
            'endpoint_threat': 12000,
            'user_behavior': 13000,
            'system_event': 14000
        }
        return categories.get(event_type, 10000)
    
    def _severity_to_ecs_level(self, severity: str) -> int:
        """Convert severity to ECS log level"""
        mapping = {'low': 2, 'medium': 4, 'high': 6, 'critical': 8}
        return mapping.get(severity.lower(), 4)

class MLPipelineOrchestrator:
    """Machine Learning pipeline management for threat detection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pipelines: Dict[str, Dict[str, Any]] = {}
        self.model_registry = {}
        self.training_queue = asyncio.Queue()
        self.inference_queue = asyncio.Queue()
        
    async def initialize(self):
        """Initialize ML infrastructure"""
        # Start training and inference workers
        asyncio.create_task(self._training_worker())
        asyncio.create_task(self._inference_worker())
        
        # Load pre-trained models
        await self._load_pretrained_models()
        
        logging.info("✅ ML Pipeline Orchestrator initialized")
    
    async def register_ml_pipeline(self, pipeline_id: str, 
                                  pipeline_config: Dict[str, Any]) -> bool:
        """Register a new ML pipeline"""
        try:
            pipeline = {
                'id': pipeline_id,
                'type': pipeline_config['type'],  # 'training', 'inference', 'both'
                'model_type': pipeline_config['model_type'],
                'data_sources': pipeline_config['data_sources'],
                'target_features': pipeline_config['target_features'],
                'training_schedule': pipeline_config.get('training_schedule'),
                'resource_requirements': pipeline_config.get('resource_requirements', {}),
                'status': 'registered',
                'created_date': datetime.now(),
                'last_trained': None,
                'model_version': None,
                'performance_metrics': {}
            }
            
            self.pipelines[pipeline_id] = pipeline
            
            # If it's a training pipeline, validate data sources
            if pipeline['type'] in ['training', 'both']:
                await self._validate_data_sources(pipeline['data_sources'])
            
            logging.info(f"✅ ML pipeline registered: {pipeline_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to register ML pipeline {pipeline_id}: {e}")
            return False
    
    async def trigger_model_training(self, pipeline_id: str, 
                                   training_data: Dict[str, Any] = None) -> str:
        """Trigger model training for a pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        training_job_id = str(uuid.uuid4())
        
        training_job = {
            'job_id': training_job_id,
            'pipeline_id': pipeline_id,
            'training_data': training_data,
            'status': 'queued',
            'created_date': datetime.now(),
            'started_date': None,
            'completed_date': None,
            'model_metrics': None,
            'error_message': None
        }
        
        await self.training_queue.put(training_job)
        
        logging.info(f"🚀 Model training queued: {training_job_id} for pipeline {pipeline_id}")
        return training_job_id
    
    async def run_inference(self, model_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on input data"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not found in registry")
        
        inference_job = {
            'job_id': str(uuid.uuid4()),
            'model_id': model_id,
            'input_data': input_data,
            'status': 'queued',
            'created_date': datetime.now()
        }
        
        # For real-time inference, process immediately
        return await self._process_inference_job(inference_job)
    
    async def batch_inference(self, model_id: str, 
                            batch_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run batch inference"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not found in registry")
        
        results = []
        
        for data in batch_data:
            inference_job = {
                'job_id': str(uuid.uuid4()),
                'model_id': model_id,
                'input_data': data,
                'status': 'queued',
                'created_date': datetime.now()
            }
            
            result = await self._process_inference_job(inference_job)
            results.append(result)
        
        return results
    
    async def _training_worker(self):
        """Background worker for model training"""
        while True:
            try:
                training_job = await self.training_queue.get()
                
                logging.info(f"🏃 Starting training job: {training_job['job_id']}")
                training_job['status'] = 'running'
                training_job['started_date'] = datetime.now()
                
                # Get pipeline configuration
                pipeline = self.pipelines[training_job['pipeline_id']]
                
                # Load and prepare training data
                training_data = await self._prepare_training_data(
                    pipeline, training_job['training_data']
                )
                
                # Train model based on type
                model_result = await self._train_model(
                    pipeline['model_type'], 
                    training_data,
                    pipeline['target_features']
                )
                
                if model_result['success']:
                    # Register trained model
                    model_id = f"{training_job['pipeline_id']}_v{int(datetime.now().timestamp())}"
                    self.model_registry[model_id] = {
                        'model': model_result['model'],
                        'pipeline_id': training_job['pipeline_id'],
                        'version': model_id,
                        'trained_date': datetime.now(),
                        'metrics': model_result['metrics'],
                        'feature_names': model_result.get('feature_names', [])
                    }
                    
                    # Update pipeline
                    pipeline['last_trained'] = datetime.now()
                    pipeline['model_version'] = model_id
                    pipeline['performance_metrics'] = model_result['metrics']
                    
                    training_job['status'] = 'completed'
                    training_job['model_metrics'] = model_result['metrics']
                    
                    logging.info(f"✅ Training completed: {training_job['job_id']} -> {model_id}")
                else:
                    training_job['status'] = 'failed'
                    training_job['error_message'] = model_result['error']
                    logging.error(f"❌ Training failed: {training_job['job_id']}: {model_result['error']}")
                
                training_job['completed_date'] = datetime.now()
                
            except Exception as e:
                logging.error(f"Training worker error: {e}")
                await asyncio.sleep(5)
    
    async def _inference_worker(self):
        """Background worker for batch inference"""
        while True:
            try:
                inference_job = await self.inference_queue.get()
                await self._process_inference_job(inference_job)
                
            except Exception as e:
                logging.error(f"Inference worker error: {e}")
                await asyncio.sleep(1)
    
    async def _process_inference_job(self, inference_job: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single inference job"""
        try:
            model_info = self.model_registry[inference_job['model_id']]
            model = model_info['model']
            
            # Prepare input data
            input_features = await self._prepare_inference_data(
                inference_job['input_data'],
                model_info['feature_names']
            )
            
            # Run inference
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba([input_features])[0]
                prediction = model.predict([input_features])[0]
                confidence = float(max(probabilities))
            else:
                prediction = model.predict([input_features])[0]
                confidence = 1.0
            
            return {
                'job_id': inference_job['job_id'],
                'model_id': inference_job['model_id'],
                'prediction': prediction,
                'confidence': confidence,
                'status': 'completed',
                'processing_time': (datetime.now() - inference_job['created_date']).total_seconds()
            }
            
        except Exception as e:
            logging.error(f"Inference processing failed: {e}")
            return {
                'job_id': inference_job['job_id'],
                'status': 'failed',
                'error': str(e)
            }
    
    async def _prepare_training_data(self, pipeline: Dict[str, Any], 
                                   custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare training data from various sources"""
        # Implementation would aggregate data from:
        # - Historical security events
        # - Threat intelligence feeds
        # - Custom datasets
        # - Real-time event streams
        
        return {
            'features': [],  # Feature matrix
            'labels': [],    # Target labels
            'feature_names': [],
            'data_size': 0
        }
    
    async def _train_model(self, model_type: str, training_data: Dict[str, Any],
                          target_features: List[str]) -> Dict[str, Any]:
        """Train ML model based on type"""
        try:
            if model_type == 'isolation_forest':
                from sklearn.ensemble import IsolationForest
                model = IsolationForest(contamination=0.1, random_state=42)
                model.fit(training_data['features'])
                
                # Calculate metrics (for unsupervised learning)
                anomaly_scores = model.decision_function(training_data['features'])
                metrics = {
                    'model_type': 'isolation_forest',
                    'samples_trained': len(training_data['features']),
                    'anomaly_score_mean': float(anomaly_scores.mean()),
                    'anomaly_score_std': float(anomaly_scores.std())
                }
                
            elif model_type == 'random_forest':
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    training_data['features'], 
                    training_data['labels'], 
                    test_size=0.2, 
                    random_state=42
                )
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                # Calculate metrics
                y_pred = model.predict(X_test)
                metrics = {
                    'model_type': 'random_forest',
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'precision': float(precision_score(y_test, y_pred, average='weighted')),
                    'recall': float(recall_score(y_test, y_pred, average='weighted')),
                    'f1_score': float(f1_score(y_test, y_pred, average='weighted')),
                    'samples_trained': len(X_train),
                    'samples_tested': len(X_test)
                }
                
            elif model_type == 'neural_network':
                # Placeholder for deep learning models
                # Would use TensorFlow/PyTorch
                model = None
                metrics = {'model_type': 'neural_network', 'status': 'not_implemented'}
                
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            return {
                'success': True,
                'model': model,
                'metrics': metrics,
                'feature_names': training_data['feature_names']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _prepare_inference_data(self, input_data: Dict[str, Any],
                                    feature_names: List[str]) -> List[float]:
        """Prepare input data for inference"""
        # Extract features in the same order as training
        features = []
        
        for feature_name in feature_names:
            if feature_name in input_data:
                value = input_data[feature_name]
                # Normalize/convert to float
                if isinstance(value, (int, float)):
                    features.append(float(value))
                elif isinstance(value, str):
                    features.append(float(len(value)))  # Simple string length feature
                else:
                    features.append(0.0)
            else:
                features.append(0.0)  # Default value for missing features
        
        return features
    
    async def _load_pretrained_models(self):
        """Load pre-trained models from storage"""
        # Implementation would load models from:
        # - S3/cloud storage
        # - Model registry
        # - Local filesystem
        
        # Example: Load a basic anomaly detection model
        try:
            from sklearn.ensemble import IsolationForest
            
            default_model = IsolationForest(contamination=0.1, random_state=42)
            # In real implementation, would load from saved state
            
            self.model_registry['default_anomaly_detector'] = {
                'model': default_model,
                'pipeline_id': 'system_default',
                'version': 'v1.0',
                'trained_date': datetime.now(),
                'metrics': {'model_type': 'isolation_forest'},
                'feature_names': ['network_traffic', 'connection_count', 'packet_size']
            }
            
            logging.info("✅ Pre-trained models loaded")
            
        except ImportError:
            logging.warning("⚠️ Scikit-learn not available, skipping pre-trained models")
    
    async def _validate_data_sources(self, data_sources: List[str]):
        """Validate that data sources are accessible"""
        for source in data_sources:
            # Implementation would validate:
            # - Database connections
            # - File system access
            # - API endpoints
            # - Stream connections
            pass

class LicenseManagementSystem:
    """Enterprise license management and validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_pool = None
        self.redis_client = None
        self.license_cache = {}
        self.hardware_fingerprint_cache = {}
        
    async def initialize(self):
        """Initialize license management system"""
        # Database connection
        self.db_pool = await asyncpg.create_pool(
            host=self.config['database']['host'],
            port=self.config['database']['port'],
            database=self.config['database']['name'],
            user=self.config['database']['user'],
            password=self.config['database']['password'],
            min_size=2,
            max_size=10
        )
        
        # Redis for caching
        self.redis_client = redis.Redis(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            password=self.config['redis']['password']
        )
        
        # Start license validation background task
        asyncio.create_task(self._license_validation_worker())
        
        logging.info("✅ License Management System initialized")
    
    async def validate_license(self, license_key: str, 
                             hardware_fingerprint: str,
                             instance_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate software license"""
        try:
            # Check cache first
            cache_key = f"license:{license_key}"
            cached_result = await self.redis_client.get(cache_key)
            
            if cached_result:
                result = json.loads(cached_result)
                # Still need to check hardware fingerprint and installation count
                if result['valid']:
                    hardware_valid = await self._validate_hardware_fingerprint(
                        license_key, hardware_fingerprint
                    )
                    if not hardware_valid:
                        result['valid'] = False
                        result['reason'] = 'hardware_mismatch'
                
                return result
            
            # Get license from database
            async with self.db_pool.acquire() as conn:
                license_row = await conn.fetchrow("""
                    SELECT * FROM license_keys 
                    WHERE license_id = $1 AND is_active = true
                """, license_key)
                
                if not license_row:
                    result = {
                        'valid': False,
                        'reason': 'license_not_found',
                        'message': 'License key not found or inactive'
                    }
                    # Cache negative result briefly
                    await self.redis_client.setex(cache_key, 60, json.dumps(result))
                    return result
                
                # Check expiration
                if license_row['expires_date'] and license_row['expires_date'] < datetime.now():
                    result = {
                        'valid': False,
                        'reason': 'expired',
                        'message': 'License has expired',
                        'expires_date': license_row['expires_date'].isoformat()
                    }
                    await self.redis_client.setex(cache_key, 300, json.dumps(result))
                    return result
                
                # Check installation limit
                if (license_row['max_installations'] > 0 and 
                    license_row['current_installations'] >= license_row['max_installations']):
                    
                    # Check if this hardware fingerprint is already registered
                    fingerprints = json.loads(license_row['hardware_fingerprints'] or '[]')
                    if hardware_fingerprint not in fingerprints:
                        result = {
                            'valid': False,
                            'reason': 'installation_limit_exceeded',
                            'message': 'Maximum number of installations reached',
                            'max_installations': license_row['max_installations'],
                            'current_installations': license_row['current_installations']
                        }
                        await self.redis_client.setex(cache_key, 300, json.dumps(result))
                        return result
                
                # Validate hardware fingerprint
                hardware_valid = await self._validate_and_update_hardware_fingerprint(
                    license_key, hardware_fingerprint, license_row
                )
                
                if not hardware_valid:
                    result = {
                        'valid': False,
                        'reason': 'hardware_mismatch',
                        'message': 'Hardware fingerprint validation failed'
                    }
                    await self.redis_client.setex(cache_key, 60, json.dumps(result))
                    return result
                
                # License is valid
                result = {
                    'valid': True,
                    'license_type': license_row['license_type'],
                    'features_enabled': json.loads(license_row['features_enabled'] or '{}'),
                    'usage_limits': json.loads(license_row['usage_limits'] or '{}'),
                    'expires_date': license_row['expires_date'].isoformat() if license_row['expires_date'] else None,
                    'customer_id': license_row['customer_id']
                }
                
                # Update instance tracking
                await self._update_instance_tracking(
                    license_key, hardware_fingerprint, instance_info
                )
                
                # Cache valid result
                await self.redis_client.setex(cache_key, 300, json.dumps(result))
                
                return result
                
        except Exception as e:
            logging.error(f"License validation failed: {e}")
            return {
                'valid': False,
                'reason': 'validation_error',
                'message': 'License validation failed due to system error'
            }
    
    async def track_usage(self, license_key: str, usage_type: str, 
                         amount: int = 1) -> Dict[str, Any]:
        """Track license usage for metered features"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current usage limits
                license_row = await conn.fetchrow("""
                    SELECT usage_limits, features_enabled FROM license_keys 
                    WHERE license_id = $1 AND is_active = true
                """, license_key)
                
                if not license_row:
                    return {'success': False, 'error': 'License not found'}
                
                usage_limits = json.loads(license_row['usage_limits'] or '{}')
                features_enabled = json.loads(license_row['features_enabled'] or '{}')
                
                # Check if usage type is allowed
                if usage_type in features_enabled and not features_enabled[usage_type]:
                    return {'success': False, 'error': f'Feature {usage_type} not enabled'}
                
                # Get current usage
                current_date = datetime.now().date().isoformat()
                usage_key = f"usage:{license_key}:{usage_type}:{current_date}"
                current_usage = await self.redis_client.get(usage_key)
                current_usage = int(current_usage) if current_usage else 0
                
                # Check limits
                limit_key = f'max_{usage_type}_per_day'
                if limit_key in usage_limits and usage_limits[limit_key] > 0:
                    if current_usage + amount > usage_limits[limit_key]:
                        return {
                            'success': False,
                            'error': 'Usage limit exceeded',
                            'limit': usage_limits[limit_key],
                            'current_usage': current_usage
                        }
                
                # Update usage
                new_usage = current_usage + amount
                await self.redis_client.setex(usage_key, 86400, new_usage)  # 24 hours
                
                # Log usage to database
                await conn.execute("""
                    INSERT INTO license_usage 
                    (license_id, usage_type, usage_date, usage_amount, cumulative_usage)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (license_id, usage_type, usage_date)
                    DO UPDATE SET 
                        usage_amount = license_usage.usage_amount + $4,
                        cumulative_usage = $5
                """, license_key, usage_type, current_date, amount, new_usage)
                
                return {
                    'success': True,
                    'usage_recorded': amount,
                    'total_usage_today': new_usage,
                    'remaining_quota': usage_limits.get(limit_key, -1) - new_usage if usage_limits.get(limit_key, -1) > 0 else -1
                }
                
        except Exception as e:
            logging.error(f"Usage tracking failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def revoke_license(self, license_key: str, reason: str) -> bool:
        """Revoke a software license"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE license_keys 
                    SET is_active = false, revocation_reason = $2
                    WHERE license_id = $1
                """, license_key