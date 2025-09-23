import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class IntakeQConfig:
    """Configuration settings for IntakeQ MCP Server."""
    
    # API Configuration
    base_url: str = "https://intakeq.com/api/v1"
    default_api_key: Optional[str] = None
    api_timeout: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_period: int = 60  # seconds
    
    # Server Configuration
    server_name: str = "intakeq-mcp-server"
    server_version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Security
    allowed_origins: list = None
    require_https: bool = False
    
    # OpenAPI Configuration
    openapi_file: str = "openapi.yaml"
    
    # Feature Flags
    enable_webhooks: bool = False
    enable_caching: bool = False
    cache_ttl: int = 300  # seconds
    
    # Pagination
    default_page_size: int = 100
    max_page_size: int = 100
    
    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            self.log_level = "INFO"
        
        # Validate port
        if not 1 <= self.port <= 65535:
            self.port = 8000

class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self):
        self._config: Optional[IntakeQConfig] = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def config(self) -> IntakeQConfig:
        """Get the current configuration, loading it if necessary."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def load_config(self) -> IntakeQConfig:
        """Load configuration from environment variables and defaults."""
        config_data = {}
        
        # Load from environment variables
        env_mappings = {
            'INTAKEQ_BASE_URL': 'base_url',
            'INTAKEQ_API_KEY': 'default_api_key',
            'INTAKEQ_API_TIMEOUT': 'api_timeout',
            'INTAKEQ_RATE_LIMIT_REQUESTS': 'rate_limit_requests',
            'INTAKEQ_RATE_LIMIT_PERIOD': 'rate_limit_period',
            'SERVER_NAME': 'server_name',
            'SERVER_VERSION': 'server_version',
            'PORT': 'port',
            'HOST': 'host',
            'LOG_LEVEL': 'log_level',
            'LOG_FORMAT': 'log_format',
            'LOG_FILE': 'log_file',
            'ALLOWED_ORIGINS': 'allowed_origins',
            'REQUIRE_HTTPS': 'require_https',
            'OPENAPI_FILE': 'openapi_file',
            'ENABLE_WEBHOOKS': 'enable_webhooks',
            'ENABLE_CACHING': 'enable_caching',
            'CACHE_TTL': 'cache_ttl',
            'DEFAULT_PAGE_SIZE': 'default_page_size',
            'MAX_PAGE_SIZE': 'max_page_size',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                config_data[config_key] = self._convert_env_value(value, config_key)
        
        # Handle special cases
        if 'ALLOWED_ORIGINS' in os.environ:
            config_data['allowed_origins'] = os.getenv('ALLOWED_ORIGINS').split(',')
        
        # Create and return configuration
        config = IntakeQConfig(**config_data)
        self._setup_logging(config)
        
        return config
    
    def _convert_env_value(self, value: str, key: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Integer fields
        int_fields = {
            'api_timeout', 'rate_limit_requests', 'rate_limit_period',
            'port', 'cache_ttl', 'default_page_size', 'max_page_size'
        }
        
        # Boolean fields
        bool_fields = {
            'require_https', 'enable_webhooks', 'enable_caching'
        }
        
        if key in int_fields:
            try:
                return int(value)
            except ValueError:
                self._logger.warning(f"Invalid integer value for {key}: {value}")
                return getattr(IntakeQConfig(), key)  # Use default
        
        elif key in bool_fields:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        else:
            return value
    
    def _setup_logging(self, config: IntakeQConfig):
        """Setup logging based on configuration."""
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper()),
            format=config.log_format,
            filename=config.log_file
        )
        
        # Add console handler if logging to file
        if config.log_file:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, config.log_level.upper()))
            console_handler.setFormatter(logging.Formatter(config.log_format))
            logging.getLogger().addHandler(console_handler)
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format."""
        if not api_key:
            return False
        
        # Basic validation - IntakeQ API keys are typically long alphanumeric strings
        if len(api_key) < 20:
            return False
        
        # Could add more sophisticated validation here
        return True
    
    def get_openapi_spec_path(self) -> Path:
        """Get the path to the OpenAPI specification file."""
        return Path(self.config.openapi_file)
    
    def is_development_mode(self) -> bool:
        """Check if running in development mode."""
        return os.getenv('ENVIRONMENT', 'production').lower() in ('development', 'dev', 'local')
    
    def get_cors_settings(self) -> Dict[str, Any]:
        """Get CORS settings for the server."""
        return {
            'allow_origins': self.config.allowed_origins,
            'allow_credentials': True,
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['*'],
        }
    
    def reload_config(self):
        """Reload configuration from environment."""
        self._config = None
        self._config = self.load_config()

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> IntakeQConfig:
    """Get the current configuration."""
    return config_manager.config

def validate_required_config():
    """Validate that required configuration is present."""
    config = get_config()
    errors = []
    
    # Check if OpenAPI file exists
    if not config_manager.get_openapi_spec_path().exists():
        errors.append(f"OpenAPI specification file not found: {config.openapi_file}")
    
    # Warn if no default API key (not required, but helpful for testing)
    if not config.default_api_key and not os.getenv('INTAKEQ_API_KEY'):
        logging.warning(
            "No default API key configured. Users will need to provide API keys for all requests."
        )
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

def get_api_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Get standard API headers for IntakeQ requests."""
    config = get_config()
    
    # Use provided key or fall back to default
    key_to_use = api_key or config.default_api_key
    
    if not key_to_use:
        raise ValueError("No API key provided and no default configured")
    
    return {
        'X-Auth-Key': key_to_use,
        'Content-Type': 'application/json',
        'User-Agent': f'{config.server_name}/{config.server_version}'
    }

def get_rate_limit_config() -> Dict[str, int]:
    """Get rate limiting configuration."""
    config = get_config()
    return {
        'requests': config.rate_limit_requests,
        'period': config.rate_limit_period
    }

# Environment-specific configurations
class DevelopmentConfig(IntakeQConfig):
    """Development-specific configuration overrides."""
    log_level: str = "DEBUG"
    require_https: bool = False
    enable_caching: bool = False

class ProductionConfig(IntakeQConfig):
    """Production-specific configuration overrides."""
    log_level: str = "WARNING"
    require_https: bool = True
    allowed_origins: list = None  # Should be set via environment
    
    def __post_init__(self):
        super().__post_init__()
        # Production-specific validations
        if self.allowed_origins == ["*"]:
            logging.warning("Using wildcard CORS origins in production is not recommended")

def get_environment_config() -> IntakeQConfig:
    """Get configuration based on environment."""
    env = os.getenv('ENVIRONMENT', 'production').lower()
    
    if env in ('development', 'dev', 'local'):
        return DevelopmentConfig()
    elif env == 'production':
        return ProductionConfig()
    else:
        return IntakeQConfig()  # Default configuration
