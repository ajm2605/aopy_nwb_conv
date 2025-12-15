"""Configuration management for aopy_nwb_conv."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# Default search paths for config file
def get_default_config_paths():
    """Return list of default config paths (evaluated at call time)."""
    return [
        Path.cwd() / "config.yaml",                    # Current directory
        Path.cwd() / "config" / "config.yaml",         # config/ subdirectory
        Path.home() / ".aopy_nwb_conv" / "config.yaml", # User home directory
        Path(__file__).parent.parent.parent / "config" / "config.yaml",  # Package directory
    ]


class Config:
    """Configuration manager for aopy_nwb_conv.
    
    Loads configuration from YAML file or environment variables.
    Priority order:
    1. Explicitly provided config_path
    2. AOPY_NWB_CONFIG environment variable
    3. Default search paths
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, searches default locations.
        """
        self.config_path = self._find_config(config_path)
        print(self.config_path)
        self._config = self._load_config()

    def _find_config(self, config_path: Optional[Path]) -> Optional[Path]:
        """Find configuration file."""
        # 1. Explicit path provided
        if config_path is not None:
            path = Path(config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file not found: {path}")

        # 2. Environment variable
        env_path = os.getenv("AOPY_NWB_CONFIG")
        if env_path is not None:
            path = Path(env_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file from env var not found: {path}")

        # 3. Search default paths
        for path in get_default_config_paths():
            if path.exists():
                return path

        # No config found - will use defaults
        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path is None:
            return self._get_defaults()

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        # Merge with defaults
        defaults = self._get_defaults()
        return self._merge_configs(defaults, config)

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'data': {
                'data_root': None,
                'output_root': './output',
            },
            'logging': {
                'level': 'INFO',
                'log_dir': 'logs',
            },
            'conversion': {
                'compression': True,
                'chunk_size': 10000,
            }
        }

    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two config dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result


    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'data.data_root')
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Example:
            >>> config = Config()
            >>> data_root = config.get('data.data_root')
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value


    def get_paths(self) -> Dict[str, Path]:
        """Get relevant paths from configuration."""
        data_root = Path(self.get('data.data_root'))
        data_output = Path(self.get('data.output_root'))
        subdirs = self.get('data.subdirs', {})

        paths = {'data_root': data_root, 'data_output': data_output}

        for key, subdir in subdirs.items():
            subdir_path = data_root / subdir
            paths[key] = subdir_path

        return paths
    
    def get_nhp_subjects(self) -> Dict[str, str]:
        """Get mapping of NHP subject codes to names."""
        nhp_subjects = self.get('nhp_subjects', {})
        assert nhp_subjects is not None, "NHP subjects not defined in config."

        return nhp_subjects

    def get_date_format(self) -> Dict[str, str]:
        """Get date string format"""
        date_format = self.get('date_format', None)
        assert date_format is not None, "NHP subjects not defined in config."

        return date_format

    @property
    def data_root(self) -> Optional[Path]:
        """Get data root path."""
        root = self.get('data.data_root')
        return Path(root) if root else None

    @property
    def output_root(self) -> Path:
        """Get output root path."""
        return Path(self.get('data.output_root', './output'))

    def __repr__(self) -> str:
        return f"Config(path={self.config_path})"


# Global config instance
_global_config: Optional[Config] = None


def get_config(config_path: Optional[Path] = None, reload: bool = False) -> Config:
    """Get global configuration instance.
    
    Args:
        config_path: Path to config file (only used on first call or if reload=True)
        reload: Force reload of configuration
        
    Returns:
        Config instance
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = Config(config_path)

    return _global_config


def set_config(config_path: Path):
    """Set global configuration from file.
    
    Args:
        config_path: Path to config file
    """
    global _global_config
    _global_config = Config(config_path)

def reset_config():  # Add this function
    """Reset global config (primarily for testing)."""
    global _global_config
    _global_config = None
