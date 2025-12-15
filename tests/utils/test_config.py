"""Tests for configuration management."""

import os
from pathlib import Path

import pytest
import yaml

from aopy_nwb_conv.utils.config import Config, get_config, reset_config, set_config


def test_check_env():
    # Check if it's currently set
    value = os.getenv('AOPY_NWB_CONFIG')
    print(f"AOPY_NWB_CONFIG = {value}")

    # Or check if it exists
    if 'AOPY_NWB_CONFIG' in os.environ:
        print("Environment variable is set")
    else:
        print("Environment variable is NOT set")

class TestCommonConfigCalls:
    def test_get_paths(self):
        config = Config()
        assert config is not None, "Personalized config file must be defined. See readme."
        paths = config.get_paths()
        for k in paths.keys():
            assert paths[k].exists(), f"Config path does not exist: {p}"

    def test_get_nhp_subjects(self):
        config = Config()
        subjects = config.get_nhp_subjects()
        assert isinstance(subjects, dict), "NHP subjects should be a dictionary."
        assert len(subjects) > 0, "NHP subjects dictionary should not be empty."



class TestConfigLoading:
    """Test configuration file loading."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary config file."""
        config_data = {
            'data': {
                'data_root': str(tmp_path / 'data'),
                'output_root': str(tmp_path / 'output'),
            },
            'logging': {
                'level': 'DEBUG',
                'log_dir': 'logs',
            },
            'conversion': {
                'compression': True,
                'chunk_size': 5000,
            }
        }

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return config_file

    @pytest.fixture
    def mock_data_structure(self, tmp_path):
        """Create mock data directory structure."""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()

        # Create sample subject/date/session structure
        session_dir = data_dir / 'MonkeyA' / '2024-03-15' / 'session_001'
        session_dir.mkdir(parents=True)

        return data_dir

    def test_config_loads_from_explicit_path(self, temp_config_file):
        """Test loading config from explicitly provided path."""
        config = Config(config_path=temp_config_file)

        assert config.config_path == temp_config_file
        assert config.get('logging.level') == 'DEBUG'
        assert config.get('conversion.chunk_size') == 5000

    def test_config_raises_on_invalid_path(self):
        """Test that invalid path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config(config_path="/nonexistent/config.yaml")

    def test_config_uses_defaults_when_no_file(self):
        """Test that defaults are used when no config file exists."""
        config = Config(config_path=None)

        assert config.get('data.data_root') is None
        assert config.get('data.output_root') == './output'
        assert config.get('logging.level') == 'INFO'
        assert config.get('conversion.compression') is True

    def test_config_from_environment_variable(self, temp_config_file, monkeypatch):
        """Test loading config from AOPY_NWB_CONFIG environment variable."""
        monkeypatch.setenv('AOPY_NWB_CONFIG', str(temp_config_file))

        config = Config()
        assert config.config_path == temp_config_file
        assert config.get('logging.level') == 'DEBUG'

    def test_config_env_var_invalid_path(self, monkeypatch):
        """Test that invalid env var path raises error."""
        monkeypatch.setenv('AOPY_NWB_CONFIG', '/nonexistent/config.yaml')

        with pytest.raises(FileNotFoundError):
            Config()

    def test_config_merges_with_defaults(self, tmp_path):
        """Test that partial config merges with defaults."""
        # Create config with only data section
        partial_config = tmp_path / 'partial_config.yaml'
        with open(partial_config, 'w') as f:
            yaml.dump({'data': {'data_root': '/tmp/data'}}, f)

        config = Config(config_path=partial_config)

        # Should have custom data_root
        assert config.get('data.data_root') == '/tmp/data'
        # Should have default logging settings
        assert config.get('logging.level') == 'INFO'
        assert config.get('conversion.compression') is True


class TestConfigGetMethod:
    """Test Config.get() method with dot notation."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_data = {
            'data': {
                'data_root': '/tmp/data',
                'nested': {
                    'deep': {
                        'value': 42
                    }
                }
            }
        }

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return Config(config_path=config_file)

    def test_get_top_level_key(self, config):
        """Test getting top-level configuration key."""
        assert isinstance(config.get('data'), dict)
        assert 'data_root' in config.get('data')

    def test_get_nested_key(self, config):
        """Test getting nested configuration key."""
        assert config.get('data.data_root') == '/tmp/data'

    def test_get_deeply_nested_key(self, config):
        """Test getting deeply nested configuration key."""
        assert config.get('data.nested.deep.value') == 42

    def test_get_nonexistent_key_returns_default(self, config):
        """Test that nonexistent key returns default value."""
        assert config.get('nonexistent.key', 'default') == 'default'
        assert config.get('data.nonexistent', None) is None

    def test_get_nonexistent_key_no_default(self, config):
        """Test that nonexistent key returns None when no default."""
        assert config.get('nonexistent.key') is None


class TestConfigProperties:
    """Test Config convenience properties."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_data = {
            'data': {
                'data_root': str(tmp_path / 'data'),
                'output_root': str(tmp_path / 'output'),
            }
        }

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return Config(config_path=config_file)

    def test_data_root_property(self, config, tmp_path):
        """Test data_root property returns Path."""
        assert config.data_root == tmp_path / 'data'
        assert isinstance(config.data_root, Path)

    def test_output_root_property(self, config, tmp_path):
        """Test output_root property returns Path."""
        assert config.output_root == tmp_path / 'output'
        assert isinstance(config.output_root, Path)

    def test_data_root_none_when_not_set(self):
        """Test data_root is None when not configured."""
        config = Config()
        assert config.data_root is None

    def test_output_root_has_default(self):
        """Test output_root has default value."""
        config = Config()
        assert config.output_root == Path('./output')


class TestGlobalConfig:
    """Test global config instance management."""

    @pytest.fixture(autouse=True)
    def reset_global_config(self):
        """Reset global config before and after each test."""
        reset_config()  # Clean before
        yield
        reset_config()

    def test_get_config_creates_singleton(self, tmp_path):
        """Test that get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_with_path(self, tmp_path):
        """Test get_config with explicit path."""
        config_file = tmp_path / 'config.yaml'
        config_data = {'data': {'data_root': '/tmp/data'}}

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = get_config(config_path=config_file)
        assert config.get('data.data_root') == '/tmp/data'

    def test_get_config_reload(self, tmp_path):
        """Test reloading global config."""
        # Create first config
        config1_file = tmp_path / 'config1.yaml'
        with open(config1_file, 'w') as f:
            yaml.dump({'data': {'data_root': '/tmp/data1'}}, f)

        config1 = get_config(config_path=config1_file)
        assert config1.get('data.data_root') == '/tmp/data1'

        # Create second config
        config2_file = tmp_path / 'config2.yaml'
        with open(config2_file, 'w') as f:
            yaml.dump({'data': {'data_root': '/tmp/data2'}}, f)

        # Without reload, should return same instance
        config_same = get_config(config_path=config2_file)
        assert config_same.get('data.data_root') == '/tmp/data1'

        # With reload, should use new config
        config2 = get_config(config_path=config2_file, reload=True)
        assert config2.get('data.data_root') == '/tmp/data2'

    def test_set_config(self, tmp_path):
        """Test set_config updates global instance."""
        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump({'data': {'data_root': '/tmp/new_data'}}, f)

        set_config(config_file)
        config = get_config()

        assert config.get('data.data_root') == '/tmp/new_data'


class TestConfigSearchPaths:
    """Test configuration file search order."""

    def test_search_order_explicit_path_first(self, tmp_path, monkeypatch):
        """Test that explicit path takes priority."""
        # Create config in explicit path
        explicit_config = tmp_path / 'explicit.yaml'
        with open(explicit_config, 'w') as f:
            yaml.dump({'data': {'data_root': 'explicit'}}, f)

        # Set environment variable
        env_config = tmp_path / 'env.yaml'
        with open(env_config, 'w') as f:
            yaml.dump({'data': {'data_root': 'env'}}, f)
        monkeypatch.setenv('AOPY_NWB_CONFIG', str(env_config))

        # Explicit path should win
        config = Config(config_path=explicit_config)
        assert config.get('data.data_root') == 'explicit'

    def test_search_order_env_var_second(self, tmp_path, monkeypatch):
        """Test that env var is used when no explicit path."""
        env_config = tmp_path / 'env.yaml'
        with open(env_config, 'w') as f:
            yaml.dump({'data': {'data_root': 'env'}}, f)

        monkeypatch.setenv('AOPY_NWB_CONFIG', str(env_config))

        config = Config()
        assert config.get('data.data_root') == 'env'

    def test_search_order_default_paths_last(self, tmp_path, monkeypatch):
        """Test that default paths are checked last."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config in current directory
        local_config = tmp_path / 'config.yaml'
        with open(local_config, 'w') as f:
            yaml.dump({'data': {'data_root': 'local'}}, f)

        config = Config()
        print(config.get('data.data_root'))
        assert config.get('data.data_root') == 'local'

"""Tests for validating user-generated configuration."""
class TestUserConfigValidation:
    """Test validation of user-generated config files."""

    @pytest.fixture
    def create_config_file(self, tmp_path):
        """Factory fixture to create config files."""
        def _create(config_data):
            config_file = tmp_path / 'user_config.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            return config_file
        return _create

    def test_valid_config_file_exists(self):
        config = Config()

        assert config is not None, "User needs to define a config file in default locations per readme."
        assert config.data_root is not None, "data_root must be defined in the config file."
        assert config.output_root is not None, "output_root must be defined in the config file."
        assert config.data_root.exists(), "data_root path in config file does not exist."
        assert config.output_root.exists(), "output_root path in config file does not exist."

    def test_config_with_nonexistent_data_root(self, tmp_path, create_config_file):
        """Test config with non-existent data_root."""
        config_data = {
            'data': {
                'data_root': '/this/path/definitely/does/not/exist',
            }
        }

        config_file = create_config_file(config_data)
        config = Config(config_path=config_file)

        # Config loads but path doesn't exist
        assert config.data_root == Path('/this/path/definitely/does/not/exist')
        assert not config.data_root.exists()

class TestConfigFileFormat:
    """Test validation of YAML format and structure."""

    def test_valid_yaml_format(self, tmp_path):
        """Test that config file is valid YAML."""
        config_file = tmp_path / 'config.yaml'
        config_data = {
            'data': {
                'data_root': '/tmp/data',
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Should load without error
        with open(config_file) as f:
            loaded = yaml.safe_load(f)

        assert loaded == config_data

    def test_invalid_yaml_format(self, tmp_path):
        """Test handling of malformed YAML."""
        config_file = tmp_path / 'bad_config.yaml'

        # Write invalid YAML
        with open(config_file, 'w') as f:
            f.write("data:\n  data_root: /tmp/data\n  invalid indentation")

        # Should raise YAML error
        with pytest.raises(yaml.YAMLError):
            with open(config_file) as f:
                yaml.safe_load(f)

    def test_config_with_missing_required_sections(self, tmp_path):
        """Test config with missing sections uses defaults."""
        config_file = tmp_path / 'minimal_config.yaml'

        # Only specify data_root
        with open(config_file, 'w') as f:
            yaml.dump({'data': {'data_root': '/tmp/data'}}, f)

        config = Config(config_path=config_file)

        # Should have user value
        assert config.get('data.data_root') == '/tmp/data'
        # Should have defaults for missing sections
        assert config.get('logging.level') == 'INFO'
        assert config.get('conversion.compression') is True


class TestConfigPathTypes:
    """Test that config handles different path formats."""

    @pytest.fixture
    def create_test_dirs(self, tmp_path):
        """Create test directory structure."""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        return data_dir

    def test_absolute_path(self, tmp_path, create_test_dirs):
        """Test config with absolute path."""
        config_file = tmp_path / 'config.yaml'

        config_data = {
            'data': {
                'data_root': str(create_test_dirs.absolute()),
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(config_path=config_file)
        assert config.data_root.is_absolute()
        assert config.data_root.exists()

    def test_relative_path(self, tmp_path, monkeypatch):
        """Test config with relative path."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create relative directory
        rel_dir = Path('data')
        rel_dir.mkdir()

        config_file = tmp_path / 'config.yaml'
        config_data = {
            'data': {
                'data_root': 'data',
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(config_path=config_file)
        assert config.data_root == Path('data')

    def test_home_directory_expansion(self, tmp_path):
        """Test that ~ is expanded to home directory."""
        config_file = tmp_path / 'config.yaml'
        config_data = {
            'data': {
                'data_root': '~/test_data',
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(config_path=config_file)

        # Path should still contain ~, but can be expanded
        expandable = Path(config.get('data.data_root')).expanduser()
        assert expandable.is_absolute()
        assert str(expandable).startswith(str(Path.home()))


class TestConfigIntegration:
    """Integration tests with actual data locator."""

    def test_data_locator_uses_config(self, tmp_path):
        """Test that DataLocator can use config."""
        from aopy_nwb_conv.core.data_locator import DataLocator
        from aopy_nwb_conv.utils.config import set_config

        # Create mock data structure
        data_dir = tmp_path / 'data'
        session_dir = data_dir / 'MonkeyA' / '2024-03-15' / 'session_001'
        session_dir.mkdir(parents=True)
        (session_dir / 'neural_data.h5').touch()

        # Create config
        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump({'data': {'data_root': str(data_dir)}}, f)

        # Set global config
        set_config(config_file)

        # DataLocator should use config
        locator = DataLocator()  # No argument!
        assert locator.data_root == data_dir

        # Should be able to locate session
        session = locator.locate_session('MonkeyA', '2024-03-15', 'session_001')
        assert session.subject_id == 'MonkeyA'

    def test_data_locator_override_config(self, tmp_path):
        """Test that explicit path overrides config."""
        from aopy_nwb_conv.core.data_locator import DataLocator
        from aopy_nwb_conv.utils.config import set_config

        # Create two data directories
        data_dir1 = tmp_path / 'data1'
        data_dir1.mkdir()

        data_dir2 = tmp_path / 'data2'
        data_dir2.mkdir()

        # Config points to data1
        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump({'data': {'data_root': str(data_dir1)}}, f)

        set_config(config_file)

        # But explicitly use data2
        locator = DataLocator(data_root=data_dir2)
        assert locator.data_root == data_dir2

    def test_data_locator_fails_without_config(self):
        """Test that DataLocator fails gracefully without config."""
        from aopy_nwb_conv.core.data_locator import DataLocator
        from aopy_nwb_conv.utils.config import get_config

        # Get config without setting it (uses defaults)
        get_config(reload=True)

        # Should raise ValueError with helpful message
        with pytest.raises(ValueError, match="data_root must be provided"):
            DataLocator()
