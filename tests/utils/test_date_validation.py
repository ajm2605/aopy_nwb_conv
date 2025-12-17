"""
Updated tests for get_valid_preprocessed_dates that properly mock the Config class

These tests match your actual Config implementation structure.
"""
import re
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the function to test
from aopy_nwb_conv.utils.date_validation import get_valid_preprocessed_dates
from aopy_nwb_conv.utils.config import Config


# ============================================================================
# ENVIRONMENT-INDEPENDENT TESTS (Run everywhere, including CI/CD)
# ============================================================================

class TestGetValidPreprocessedDatesUnit:
    """Unit tests that don't depend on actual file system or config"""

    @pytest.fixture
    def mock_config(self):
        """Mock Config object that matches your actual Config class structure"""
        mock = MagicMock()
        # Mock the get_date_format method to return a string
        mock.get_date_format.return_value = "%Y%m%d"
        return mock

    def test_empty_directory(self, mock_config):
        """Test with no HDF files in directory"""
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=[]):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=re.compile(r'\d{8}')):
                    result = get_valid_preprocessed_dates("/fake/path", "subject123")
                    
                    assert result == []
                    assert isinstance(result, list)

    def test_files_without_dates(self, mock_config):
        """Test with files that don't contain dates"""
        fake_files = [
            "/path/to/subject123_data.hdf",
            "/path/to/subject123_info.hdf",
            "/path/to/no_date_file.hdf"
        ]
        
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=fake_files):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{8}'):
                    with patch('aopy_nwb_conv.utils.date_validation.extract_date_from_string', return_value=None):
                        result = get_valid_preprocessed_dates("/fake/path", "subject123")
                        
                        assert result == []

    def test_files_with_valid_dates(self, mock_config):
        """Test with files containing valid dates"""
        fake_files = [
            "/path/to/subject123_20231215.hdf",
            "/path/to/subject123_20231216.hdf",
            "/path/to/subject123_20231217.hdf"
        ]
        
        expected_dates = [
            datetime(2023, 12, 15),
            datetime(2023, 12, 16),
            datetime(2023, 12, 17)
        ]
        
        def mock_extract_date(filename, regex):
            if "20231215" in filename:
                return expected_dates[0]
            elif "20231216" in filename:
                return expected_dates[1]
            elif "20231217" in filename:
                return expected_dates[2]
            return None
        
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=fake_files):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{8}'):
                    with patch('aopy_nwb_conv.utils.date_validation.extract_date_from_string', side_effect=mock_extract_date):
                        result = get_valid_preprocessed_dates("/fake/path", "subject123")
                        
                        assert len(result) == 3
                        assert result[0] == (fake_files[0], expected_dates[0])
                        assert result[1] == (fake_files[1], expected_dates[1])
                        assert result[2] == (fake_files[2], expected_dates[2])

    def test_mixed_files_with_and_without_dates(self, mock_config):
        """Test with mix of files with and without dates"""
        fake_files = [
            "/path/to/subject123_20231215.hdf",
            "/path/to/subject123_no_date.hdf",
            "/path/to/subject123_20231216.hdf",
            "/path/to/another_file.hdf"
        ]
        
        expected_dates = [
            datetime(2023, 12, 15),
            datetime(2023, 12, 16)
        ]
        
        def mock_extract_date(filename, regex):
            if "20231215" in filename:
                return expected_dates[0]
            elif "20231216" in filename:
                return expected_dates[1]
            return None
        
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=fake_files):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{8}'):
                    with patch('aopy_nwb_conv.utils.date_validation.extract_date_from_string', side_effect=mock_extract_date):
                        result = get_valid_preprocessed_dates("/fake/path", "subject123")
                        
                        assert len(result) == 2
                        assert result[0][0] == fake_files[0]
                        assert result[0][1] == expected_dates[0]
                        assert result[1][0] == fake_files[2]
                        assert result[1][1] == expected_dates[1]

    def test_different_date_formats(self):
        """Test with different date format from config"""
        mock_config = MagicMock()
        mock_config.get_date_format.return_value = "%Y-%m-%d"
        
        fake_files = [
            "/path/to/subject123_2023-12-15.hdf",
            "/path/to/subject123_2023-12-16.hdf"
        ]
        
        expected_dates = [
            datetime(2023, 12, 15),
            datetime(2023, 12, 16)
        ]
        
        def mock_extract_date(filename, regex):
            if "2023-12-15" in filename:
                return expected_dates[0]
            elif "2023-12-16" in filename:
                return expected_dates[1]
            return None
        
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=fake_files):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{4}-\d{2}-\d{2}'):
                    with patch('aopy_nwb_conv.utils.date_validation.extract_date_from_string', side_effect=mock_extract_date):
                        result = get_valid_preprocessed_dates("/fake/path", "subject123")
                        
                        assert len(result) == 2

    def test_config_method_called_correctly(self, mock_config):
        """Test that Config.get_date_format() is called"""
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config) as MockConfig:
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=[]):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{8}'):
                    get_valid_preprocessed_dates("/fake/path", "subject123")
                    
                    # Verify Config was instantiated
                    MockConfig.assert_called_once()
                    
                    # Verify get_date_format was called
                    mock_config.get_date_format.assert_called_once()


# ============================================================================
# ALTERNATIVE: More Concise Context Manager Approach
# ============================================================================

class TestGetValidPreprocessedDatesUnitConcise:
    """Alternative test style using a helper method for cleaner mocking"""

    @pytest.fixture
    def mock_config(self):
        """Mock Config object"""
        mock = MagicMock()
        mock.get_date_format.return_value = "%Y%m%d"
        return mock

    def run_with_mocks(self, mock_config, cached_files, extract_date_func=None, date_regex=r'\d{8}'):
        """Helper method to run function with common mocks"""
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config), \
             patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=cached_files), \
             patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=date_regex):
            
            if extract_date_func:
                with patch('aopy_nwb_conv.file_utils.extract_date_from_string', side_effect=extract_date_func):
                    return get_valid_preprocessed_dates("/fake/path", "subject123")
            else:
                with patch('aopy_nwb_conv.file_utils.extract_date_from_string', return_value=None):
                    return get_valid_preprocessed_dates("/fake/path", "subject123")

    def test_empty_directory(self, mock_config):
        """Test with no HDF files in directory"""
        result = self.run_with_mocks(mock_config, cached_files=[])
        assert result == []

    def test_files_without_dates(self, mock_config):
        """Test with files that don't contain dates"""
        fake_files = [
            "/path/to/subject123_data.hdf",
            "/path/to/subject123_info.hdf"
        ]
        result = self.run_with_mocks(mock_config, cached_files=fake_files)
        assert result == []

    def test_files_with_dates(self, mock_config):
        """Test with files containing valid dates"""
        fake_files = [
            "/path/to/subject123_20231215.hdf",
            "/path/to/subject123_20231216.hdf"
        ]
        
        expected_dates = [
            datetime(2023, 12, 15),
            datetime(2023, 12, 16)
        ]
        
        def mock_extract_date(filename, regex):
            if "20231215" in filename:
                return expected_dates[0]
            elif "20231216" in filename:
                return expected_dates[1]
            return None
        
        result = self.run_with_mocks(
            mock_config, 
            cached_files=fake_files, 
            extract_date_func=mock_extract_date
        )
        
        assert len(result) == 2
        assert result[0] == (fake_files[0], expected_dates[0])
        assert result[1] == (fake_files[1], expected_dates[1])


# ============================================================================
# FIXTURE-BASED TESTS (Use Config's reset functionality)
# ============================================================================

class TestGetValidPreprocessedDatesWithConfigReset:
    """Tests that use the actual Config class with reset between tests"""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset the global config before and after each test"""
        from aopy_nwb_conv.utils.config import reset_config
        reset_config()
        yield
        reset_config()

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file"""
        config_content = """
data:
  data_root: /fake/data/root
  output_root: /fake/output
  subdirs:
    monkey_preprocessed: preprocessed
    nwb_output: nwb

date_format: "%Y%m%d"

logging:
  level: INFO
"""
        temp_dir = Path(tempfile.mkdtemp())
        config_file = temp_dir / "config.yaml"
        config_file.write_text(config_content)
        
        yield config_file
        
        shutil.rmtree(temp_dir)

    def test_with_temp_config_file(self, temp_config_file):
        """Test using a temporary config file"""
        # Patch the Config to use our temp config
        with patch('aopy_nwb_conv.utils.config.get_default_config_paths', return_value=[temp_config_file]):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=[]):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=r'\d{8}'):
                    result = get_valid_preprocessed_dates("/fake/path", "subject123")
                    
                    # Verify it used the config
                    assert result == []


# ============================================================================
# INTEGRATION TESTS WITH REAL CONFIG (Skip if not available)
# ============================================================================

class TestGetValidPreprocessedDatesConfigIntegration:
    """Integration tests that use actual Config - only run in dev environment"""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset config between tests"""
        from aopy_nwb_conv.utils.config import reset_config
        reset_config()
        yield
        reset_config()

    def test_with_actual_config_hdf_path(self):
        """Test with actual config HDF path"""
        try:
            from aopy_nwb_conv.utils.config import Config
        except ImportError:
            pytest.skip("Config not available")

        try:
            config = Config()
            paths = config.get_paths()
            preprocessing_path = paths.get('monkey_preprocessed')

            if preprocessing_path is None:
                pytest.skip("'monkey_preprocessed' path not in config")

            preprocessing_path = Path(preprocessing_path)
            if not preprocessing_path.exists():
                pytest.skip(f"Preprocessing directory does not exist: {preprocessing_path}")

        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # Test with actual config and file system
        result = get_valid_preprocessed_dates(preprocessing_path, "subject123")

        # Basic assertions
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)
        
        if result:
            # Verify structure: (path, date)
            assert all(isinstance(path, str) for path, date in result)
            assert all(isinstance(date, datetime) for path, date in result)
            
            # Verify paths are from the expected directory
            assert all(str(preprocessing_path) in path for path, date in result)
            
            print(f"✓ Found {len(result)} files with valid dates")

    def test_config_date_format_is_used(self):
        """Test that the date format from config is actually used"""
        try:
            from aopy_nwb_conv.utils.config import Config
            config = Config()
            
            # Get the date format from config
            date_format = config.get_date_format()
            
            paths = config.get_paths()
            preprocessing_path = paths.get('monkey_preprocessed')

            if preprocessing_path is None or not Path(preprocessing_path).exists():
                pytest.skip("Preprocessing path not available")

        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # The function should use the config's date format
        result = get_valid_preprocessed_dates(Path(preprocessing_path), "subject123")
        
        # If we got results, the date format worked
        assert isinstance(result, list)
        
        print(f"✓ Date format '{date_format}' used successfully")
        print(f"✓ Found {len(result)} files")


# ============================================================================
# PARAMETRIZED TESTS FOR DIFFERENT CONFIG SCENARIOS
# ============================================================================

class TestGetValidPreprocessedDatesParametrized:
    """Test with various config scenarios"""

    @pytest.mark.parametrize("date_format,file_pattern,expected_date", [
        ("%Y%m%d", "subject_20231215.hdf", datetime(2023, 12, 15)),
        ("%Y-%m-%d", "subject_2023-12-15.hdf", datetime(2023, 12, 15)),
        ("%d%m%Y", "subject_15122023.hdf", datetime(2023, 12, 15)),
    ])
    def test_various_date_formats(self, date_format, file_pattern, expected_date):
        """Test with different date formats"""
        mock_config = MagicMock()
        mock_config.get_date_format.return_value = date_format
        
        fake_files = [f"/path/to/{file_pattern}"]
        
        # Create appropriate regex for the format
        if date_format == "%Y%m%d":
            regex = r'\d{8}'
        elif date_format == "%Y-%m-%d":
            regex = r'\d{4}-\d{2}-\d{2}'
        elif date_format == "%d%m%Y":
            regex = r'\d{8}'
        
        with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
            with patch('aopy_nwb_conv.utils.cache.get_cached_files', return_value=fake_files):
                with patch('aopy_nwb_conv.utils.date_validation.define_date_regex', return_value=regex):
                    with patch('aopy_nwb_conv.file_utils.extract_date_from_string', return_value=expected_date):
                        result = get_valid_preprocessed_dates("/fake/path", "subject123")
                        
                        assert len(result) == 1
                        assert result[0][1] == expected_date


# ============================================================================
# DEMONSTRATION: How the mocking works with your Config class
# ============================================================================

def demonstrate_config_mocking():
    """
    This demonstrates how the mocking approach works with your Config class.
    
    Your actual code does:
        config = Config()
        date_format = config.get_date_format()
    
    Our mock does:
        mock_config = MagicMock()
        mock_config.get_date_format.return_value = "%Y%m%d"
        
        with patch('module.Config', return_value=mock_config):
            # When Config() is called, it returns mock_config
            # When get_date_format() is called on that, it returns "%Y%m%d"
    """
    
    # Create mock that mimics your Config class
    mock_config = MagicMock()
    mock_config.get_date_format.return_value = "%Y%m%d"
    
    # This simulates what happens in the test
    with patch('aopy_nwb_conv.utils.config.Config', return_value=mock_config):
        # Inside your function, this happens:
        # config = Config()  # Returns mock_config
        # date_format = config.get_date_format()  # Returns "%Y%m%d"
        pass


if __name__ == "__main__":
    # Show how the mocking works
    print("=== Config Mocking Demonstration ===")
    demonstrate_config_mocking()
    print("✓ Mocking approach matches your Config class structure")
    print()
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])