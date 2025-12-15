import tempfile
from pathlib import Path

from aopy_nwb_conv.utils.cache import get_temp_cache_path, load_cache_pickle, save_cache_pickle


class TestCache:
    """Test suite for cache utilities"""

    def test_get_temp_cache_path_default(self):
        """Test getting cache path with default name"""
        cache_file = get_temp_cache_path()

        assert cache_file is not None
        assert isinstance(cache_file, Path)
        assert cache_file.name == "file_date_cache.pkl"
        assert "aopy_nwb_conv_cache" in str(cache_file)
        assert cache_file.parent.exists()  # Directory should be created

    def test_get_temp_cache_path_custom_name(self):
        """Test getting cache path with custom name"""
        custom_name = "my_custom_cache.pkl"
        cache_file = get_temp_cache_path(custom_name)

        assert cache_file.name == custom_name
        assert cache_file.parent.exists()

    def test_get_temp_cache_path_in_tmp(self):
        """Test that cache path is in system temp directory"""
        cache_file = get_temp_cache_path()
        temp_dir = Path(tempfile.gettempdir())

        assert temp_dir in cache_file.parents

    def test_save_and_load_cache_pickle_simple(self):
        """Test saving and loading a simple cache"""
        cache_path = get_temp_cache_path("test_simple.pkl")

        # Create test cache data
        test_cache = {
            'file1.txt': {'mtime': 123456.789, 'date': '2024-01-15'},
            'file2.txt': {'mtime': 987654.321, 'date': '2024-02-20'}
        }

        # Save cache
        save_cache_pickle(test_cache, cache_path)
        assert cache_path.exists()

        # Load cache
        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == test_cache

        # Cleanup
        cache_path.unlink()

    def test_save_and_load_cache_pickle_complex(self):
        """Test saving and loading complex data structures"""
        cache_path = get_temp_cache_path("test_complex.pkl")

        # More complex cache data with nested structures
        test_cache = {
            '/path/to/file1.txt': {
                'mtime': 1234567890.123,
                'date': '2024-01-15',
                'metadata': {'size': 1024, 'permissions': 'rw-r--r--'}
            },
            '/path/to/file2.log': {
                'mtime': 9876543210.987,
                'date': None,  # No date found
                'metadata': {'size': 2048, 'permissions': 'rw-rw-r--'}
            }
        }

        save_cache_pickle(test_cache, cache_path)
        loaded_cache = load_cache_pickle(cache_path)

        assert loaded_cache == test_cache
        assert loaded_cache['/path/to/file2.log']['date'] is None

        # Cleanup
        cache_path.unlink()

    def test_save_and_load_cache_pickle_path_objects(self):
        """Test that Path objects can be stored in cache"""
        cache_path = get_temp_cache_path("test_paths.pkl")

        test_cache = {
            'key1': Path('/some/path/file.txt'),
            'key2': {'path': Path('/another/path'), 'value': 42}
        }

        save_cache_pickle(test_cache, cache_path)
        loaded_cache = load_cache_pickle(cache_path)

        assert isinstance(loaded_cache['key1'], Path)
        assert loaded_cache['key1'] == Path('/some/path/file.txt')
        assert isinstance(loaded_cache['key2']['path'], Path)

        # Cleanup
        cache_path.unlink()

    def test_load_cache_pickle_nonexistent(self):
        """Test loading from non-existent cache file"""
        cache_path = get_temp_cache_path("nonexistent.pkl")

        # Ensure file doesn't exist
        if cache_path.exists():
            cache_path.unlink()

        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == {}

    def test_load_cache_pickle_corrupted(self):
        """Test loading from corrupted cache file"""
        cache_path = get_temp_cache_path("test_corrupted.pkl")

        # Write corrupted data
        with open(cache_path, 'wb') as f:
            f.write(b'This is not valid pickle data!')

        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == {}

        # Cleanup
        cache_path.unlink()

    def test_load_cache_pickle_empty_file(self):
        """Test loading from empty cache file"""
        cache_path = get_temp_cache_path("test_empty.pkl")

        # Create empty file
        cache_path.touch()

        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == {}

        # Cleanup
        cache_path.unlink()

    def test_save_cache_pickle_empty_dict(self):
        """Test saving empty cache"""
        cache_path = get_temp_cache_path("test_empty_dict.pkl")

        test_cache = {}
        save_cache_pickle(test_cache, cache_path)

        assert cache_path.exists()
        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == {}

        # Cleanup
        cache_path.unlink()

    def test_save_cache_pickle_overwrites(self):
        """Test that saving cache overwrites existing file"""
        cache_path = get_temp_cache_path("test_overwrite.pkl")

        # Save first cache
        cache1 = {'key1': 'value1'}
        save_cache_pickle(cache1, cache_path)

        # Save second cache (should overwrite)
        cache2 = {'key2': 'value2'}
        save_cache_pickle(cache2, cache_path)

        loaded_cache = load_cache_pickle(cache_path)
        assert loaded_cache == cache2
        assert 'key1' not in loaded_cache

        # Cleanup
        cache_path.unlink()

    def test_cache_with_large_data(self):
        """Test caching with larger dataset"""
        cache_path = get_temp_cache_path("test_large.pkl")

        # Create a larger cache with many entries
        test_cache = {
            f'/path/to/file_{i}.txt': {
                'mtime': float(i * 1000),
                'date': f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}'
            }
            for i in range(1000)
        }

        save_cache_pickle(test_cache, cache_path)
        loaded_cache = load_cache_pickle(cache_path)

        assert len(loaded_cache) == 1000
        assert loaded_cache == test_cache

        # Cleanup
        cache_path.unlink()

    def test_cache_directory_persistence(self):
        """Test that cache directory persists across multiple operations"""
        cache_dir = Path(tempfile.gettempdir()) / 'aopy_nwb_conv_cache'

        # Get multiple cache paths
        cache1 = get_temp_cache_path("cache1.pkl")
        cache2 = get_temp_cache_path("cache2.pkl")

        # Both should use the same directory
        assert cache1.parent == cache2.parent
        assert cache1.parent == cache_dir
        assert cache_dir.exists()

    def test_cache_isolation(self):
        """Test that different cache files are isolated"""
        cache1_path = get_temp_cache_path("isolated1.pkl")
        cache2_path = get_temp_cache_path("isolated2.pkl")

        data1 = {'cache': 'one'}
        data2 = {'cache': 'two'}

        save_cache_pickle(data1, cache1_path)
        save_cache_pickle(data2, cache2_path)

        loaded1 = load_cache_pickle(cache1_path)
        loaded2 = load_cache_pickle(cache2_path)

        assert loaded1 == data1
        assert loaded2 == data2
        assert loaded1 != loaded2

        # Cleanup
        cache1_path.unlink()
        cache2_path.unlink()


# If you want to run tests with pytest
#if __name__ == "__main__":
#    pytest.main([__file__, "-v"])
