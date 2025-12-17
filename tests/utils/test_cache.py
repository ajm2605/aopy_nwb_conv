import tempfile
from pathlib import Path
import pytest

from aopy_nwb_conv.utils.cache import get_temp_cache_path, load_cache_pickle, save_cache_pickle

@pytest.fixture
def test_directory():
    """Create a temporary directory with test files"""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    # Create directory structure with various files
    (temp_dir / "subdir1").mkdir()
    (temp_dir / "subdir2").mkdir()
    (temp_dir / "subdir1" / "nested").mkdir()

    # Create HDF files
    (temp_dir / "file1.hdf").touch()
    (temp_dir / "file2.hdf").touch()
    (temp_dir / "subdir1" / "file3.hdf").touch()
    (temp_dir / "subdir1" / "nested" / "file4.hdf").touch()

    # Create NWB files
    (temp_dir / "data1.nwb").touch()
    (temp_dir / "subdir2" / "data2.nwb").touch()

    # Create other files (should be ignored)
    (temp_dir / "readme.txt").touch()
    (temp_dir / "data.csv").touch()
    (temp_dir / "subdir1" / "notes.md").touch()

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def clear_cache_and_cleanup():
    """Clear cache before and after each test"""
    # Clear before test
    clear_cache()

    # Also clear any disk cache files
    from aopy_nwb_conv.utils.cache import get_temp_cache_path
    cache_dir = get_temp_cache_path("dummy.pkl").parent
    if cache_dir.exists():
        for cache_file in cache_dir.glob("file_cache_*.pkl"):
            try:
                cache_file.unlink()
            except:
                pass

    yield

    # Clear after test
    clear_cache()

    # Clean up disk cache files again
    if cache_dir.exists():
        for cache_file in cache_dir.glob("file_cache_*.pkl"):
            try:
                cache_file.unlink()
            except:
                pass


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

class TestClearCache:
    """Test the clear_cache function"""

    def test_clear_all_cache(self, test_directory):
        """Test clearing all caches"""
        # Create multiple caches
        cache_files_by_extension(test_directory, "hdf")
        cache_files_by_extension(test_directory, "nwb")

        assert len(_cached_files) == 2

        # Clear all
        clear_cache()

        assert len(_cached_files) == 0
        assert len(_cache_loaded) == 0

    def test_clear_specific_extension(self, test_directory):
        """Test clearing cache for specific extension"""
        # Create multiple caches
        cache_files_by_extension(test_directory, "hdf")
        cache_files_by_extension(test_directory, "nwb")

        assert len(_cached_files) == 2

        # Clear only HDF
        clear_cache("hdf")

        # HDF cache should be cleared
        hdf_key = f"{test_directory}_hdf"
        nwb_key = f"{test_directory}_nwb"

        assert hdf_key not in _cached_files
        assert nwb_key in _cached_files

    def test_clear_cache_idempotent(self):
        """Test that clearing empty cache doesn't error"""
        clear_cache()  # Should not raise error
        clear_cache("hdf")  # Should not raise error


class TestCachePerformance:
    """Test performance-related aspects of caching"""

    def test_large_number_of_files(self):
        """Test caching with many files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create 100 files
            for i in range(100):
                (temp_path / f"file_{i}.hdf").touch()

            files = cache_files_by_extension(temp_path, "hdf")

            assert len(files) == 100

    def test_deep_directory_structure(self):
        """Test caching with deep nested directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create deep nesting: depth 10
            current = temp_path
            for i in range(10):
                current = current / f"level_{i}"
                current.mkdir()
                (current / f"file_{i}.hdf").touch()

            files = cache_files_by_extension(temp_path, "hdf")

            assert len(files) == 10


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory"""
        fake_dir = Path("/nonexistent/directory/path")

        # Should not crash, but return empty or handle gracefully
        # Depending on implementation, this might raise FileNotFoundError
        # or return empty list
        try:
            files = find_file_ext(fake_dir, "hdf")
            assert files == []
        except FileNotFoundError:
            pass  # Also acceptable behavior

    def test_file_path_as_string(self, test_directory):
        """Test that string paths are handled"""
        files = cache_files_by_extension(str(test_directory), "hdf")

        assert len(files) == 4

    def test_cache_with_special_characters_in_path(self):
        """Test caching with special characters in directory name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            special_dir = Path(temp_dir) / "test-dir_with.special@chars"
            special_dir.mkdir()
            (special_dir / "file.hdf").touch()

            files = cache_files_by_extension(special_dir, "hdf")

            assert len(files) == 1

class TestConfigIntegration:
    """Test integration with Config when available"""

    def test_get_cached_files_from_config_hdf(self):
        """Test getting HDF files from config path (runs only if Config available)"""
        try:
            from aopy_nwb_conv.utils.config import Config
        except ImportError:
            pytest.skip("Config not available")

        try:
            config = Config()
            paths = config.get_paths()
            print(paths)
            preprocessing_path = paths.get('monkey_preprocessed')

            if preprocessing_path is None:
                pytest.skip("'monkey_preprocessing' path not in config")

            preprocessing_path = Path(preprocessing_path)
            if not preprocessing_path.exists():
                pytest.skip(f"Preprocessing directory does not exist: {preprocessing_path}")

        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # If we got here, Config is available and directory exists
        # Test loading files from config
        files = get_cached_files(preprocessing_path, extension="hdf", max=1000)

        # Basic assertions
        assert isinstance(files, list)
        assert all(isinstance(f, str) for f in files)
        assert all(f.endswith('.hdf') for f in files)

        # Verify files are from the expected directory
        assert all(str(preprocessing_path) in f for f in files)

        print(f"✓ Successfully loaded {len(files)} HDF files from config path")

    def test_get_cached_files_from_config_nwb(self):
        """Test getting NWB files from config path (runs only if Config available)"""
        try:
            from aopy_nwb_conv.utils.config import Config
        except ImportError:
            pytest.skip("Config not available")

        try:
            config = Config()
            paths = config.get_paths()
            nwb_path = paths.get('nwb_output')

            if nwb_path is None:
                pytest.skip("'nwb_output' path not in config")

            nwb_path = Path(nwb_path)
            if not nwb_path.exists():
                pytest.skip(f"NWB output directory does not exist: {nwb_path}")

        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # If we got here, Config is available and directory exists
        # Test loading files from config
        files = get_cached_files(nwb_path, extension="nwb", max = 1000)

        # Basic assertions
        assert isinstance(files, list)
        assert all(isinstance(f, str) for f in files)
        assert all(f.endswith('.nwb') for f in files)

        # Verify files are from the expected directory
        assert all(str(nwb_path) in f for f in files)

        print(f"✓ Successfully loaded {len(files)} NWB files from config path")

    def test_config_path_caching_performance(self):
        """Test that config-based caching works efficiently"""
        try:
            from aopy_nwb_conv.utils.config import Config
            config = Config()
            paths = config.get_paths()
            preprocessing_path = Path(paths.get('monkey_preprocessed'))

            if not preprocessing_path.exists():
                pytest.skip(f"Preprocessing directory does not exist: {preprocessing_path}")
        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        import time

        # First call - should scan directory
        start = time.time()
        files1 = get_cached_files(preprocessing_path, extension="hdf", max = 1000)
        first_call_time = time.time() - start

        # Second call - should use in-memory cache (should be much faster)
        start = time.time()
        files2 = get_cached_files(preprocessing_path, extension="hdf", max = 1000)
        second_call_time = time.time() - start

        # Verify results are the same
        assert files1 == files2

        # Second call should be significantly faster (at least 10x)
        # Only assert this if there are actually files to cache
        if len(files1) > 10:
            assert second_call_time < first_call_time / 10, \
                f"Second call ({second_call_time:.4f}s) should be much faster than first ({first_call_time:.4f}s)"

        print(f"First call: {first_call_time:.4f}s, Second call: {second_call_time:.4f}s")
        print(f"Speedup: {first_call_time / second_call_time:.1f}x")

    def test_config_and_explicit_directory_both_work(self, test_directory):
        """Test that both config-based and explicit directory work"""
        try:
            from aopy_nwb_conv.utils.config import Config
            config = Config()
            paths = config.get_paths()
            preprocessing_path = Path(paths.get('monkey_preprocessed'))

            if not preprocessing_path.exists():
                pytest.skip(f"Preprocessing directory does not exist: {preprocessing_path}")
        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # Get files from config
        print(preprocessing_path)
        config_files = get_cached_files(preprocessing_path, extension="hdf", max = 1000)

        print('The test directory is ' + str(test_directory))
        # Get files from explicit directory (test fixture)
        explicit_files = get_cached_files(test_directory, extension="hdf", force_refresh=True, max = 1000)

        # Both should return lists
        assert isinstance(config_files, list)
        assert isinstance(explicit_files, list)

        # They should be different (different directories)
        assert set(config_files) != set(explicit_files)

        # Config files should be from config path
        assert all(str(preprocessing_path) in f for f in config_files)

        # Explicit files should be from test directory
        assert all(str(test_directory) in f for f in explicit_files)

        print(f"Config path: {len(config_files)} files")
        print(f"Test directory: {len(explicit_files)} files")

    def test_force_refresh_with_config_path(self):
        """Test that force_refresh works with config-based paths"""
        try:
            from aopy_nwb_conv.utils.config import Config
            config = Config()
            paths = config.get_paths()
            preprocessing_path = Path(paths.get('monkey_preprocessed'))

            if not preprocessing_path.exists():
                pytest.skip(f"Preprocessing directory does not exist: {preprocessing_path}")
        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # First call - loads from disk cache or generates
        files1 = get_cached_files(preprocessing_path, extension="hdf", max = 1000)

        # Clear only in-memory cache
        global _cached_files, _cache_loaded
        _cached_files.clear()
        _cache_loaded.clear()

        # Second call - should load from disk cache
        files2 = get_cached_files(preprocessing_path, extension="hdf", max = 1000)

        assert files1 == files2

        print(f"Cache persistence verified: {len(files1)} files")

    def test_config_with_multiple_extensions(self):
        """Test loading multiple file types from config paths"""
        try:
            from aopy_nwb_conv.utils.config import Config
            config = Config()
            paths = config.get_paths()

            # Check both paths exist
            hdf_path = Path(paths.get('monkey_preprocessed'))
            nwb_path = Path(paths.get('nwb_output'))

            if not hdf_path.exists():
                pytest.skip(f"HDF directory does not exist: {hdf_path}")
            if not nwb_path.exists():
                pytest.skip(f"NWB directory does not exist: {nwb_path}")

        except Exception as e:
            pytest.skip(f"Config setup failed: {e}")

        # Load both file types
        hdf_files = get_cached_files(hdf_path, extension="hdf", max = 1000)
        nwb_files = get_cached_files(nwb_path, extension="nwb", max = 1000)

        # Verify they're from different directories
        if hdf_files and nwb_files:
            # Check that HDF files are from HDF directory
            assert all(str(hdf_path) in f for f in hdf_files)

            # Check that NWB files are from NWB directory
            assert all(str(nwb_path) in f for f in nwb_files)

            # Verify no overlap (assuming directories are different)
            if str(hdf_path) != str(nwb_path):
                assert set(hdf_files).isdisjoint(set(nwb_files))

        print(f"HDF files: {len(hdf_files)}, NWB files: {len(nwb_files)}")
# If you want to run tests with pytest
#if __name__ == "__main__":
#    pytest.main([__file__, "-v"])
