import shutil
import tempfile
from pathlib import Path

import pytest

from aopy_nwb_conv.utils.date_validation import (
    _cache_loaded,
    _cached_files,
    cache_files_by_extension,
    clear_cache,
    find_file_ext,
    get_cached_files,
)


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


class TestFindFileExt:
    """Test the find_file_ext function"""

    def test_find_hdf_files(self, test_directory):
        """Test finding HDF files"""
        hdf_files = find_file_ext(test_directory, "hdf")

        assert len(hdf_files) == 4
        assert all(f.endswith('.hdf') for f in hdf_files)

    def test_find_nwb_files(self, test_directory):
        """Test finding NWB files"""
        nwb_files = find_file_ext(test_directory, "nwb")

        assert len(nwb_files) == 2
        assert all(f.endswith('.nwb') for f in nwb_files)

    def test_find_with_leading_dot(self, test_directory):
        """Test that leading dot is handled correctly"""
        hdf_files_no_dot = find_file_ext(test_directory, "hdf")
        hdf_files_with_dot = find_file_ext(test_directory, ".hdf")

        assert hdf_files_no_dot == hdf_files_with_dot

    def test_find_nonexistent_extension(self, test_directory):
        """Test finding files with extension that doesn't exist"""
        result = find_file_ext(test_directory, "xyz")

        assert result == []

    def test_recursive_search(self, test_directory):
        """Test that search is recursive"""
        hdf_files = find_file_ext(test_directory, "hdf")

        # Should find files in root, subdir1, and subdir1/nested
        nested_file = str(test_directory / "subdir1" / "nested" / "file4.hdf")
        assert any(nested_file in f for f in hdf_files)

    def test_empty_directory(self):
        """Test finding files in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = find_file_ext(temp_dir, "hdf")
            assert result == []


class TestCacheFilesByExtension:
    """Test the cache_files_by_extension function"""

    def test_cache_creation(self, test_directory):
        """Test that cache is created correctly"""
        cached_files = cache_files_by_extension(test_directory, "hdf")

        assert len(cached_files) == 4
        assert all(isinstance(f, str) for f in cached_files)
        assert all(f.endswith('.hdf') for f in cached_files)

    def test_in_memory_cache(self, test_directory):
        """Test that in-memory cache is used on second call"""
        # First call - should scan
        files1 = cache_files_by_extension(test_directory, "hdf")

        # Second call - should use memory cache
        files2 = cache_files_by_extension(test_directory, "hdf")

        assert files1 == files2

        # Check that cache key exists
        cache_key = f"{test_directory}_hdf"
        assert cache_key in _cached_files

    def test_disk_cache_persistence(self, test_directory):
        """Test that disk cache persists"""
        from aopy_nwb_conv.utils.cache import get_temp_cache_path

        cache_path = get_temp_cache_path("file_cache_hdf.pkl")

        # First call - creates cache
        files1 = cache_files_by_extension(test_directory, "hdf")

        # Clear in-memory cache
        clear_cache()

        # Second call - should load from disk
        files2 = cache_files_by_extension(test_directory, "hdf")

        assert files1 == files2
        assert cache_path.exists()

        # Cleanup
        cache_path.unlink()

    def test_force_refresh(self, test_directory):
        """Test that force_refresh regenerates cache"""
        # First call
        cache_files_by_extension(test_directory, "hdf")

        # Add a new file
        (test_directory / "new_file.hdf").touch()

        # Without force_refresh - should use cache (won't see new file)
        files2 = cache_files_by_extension(test_directory, "hdf")
        assert len(files2) == 4

        # With force_refresh - should see new file
        files3 = cache_files_by_extension(test_directory, "hdf", force_refresh=True)
        assert len(files3) == 5

    def test_custom_cache_path(self, test_directory):
        """Test using custom cache path"""
        with tempfile.TemporaryDirectory() as temp_cache_dir:
            custom_cache = Path(temp_cache_dir) / "my_custom_cache.pkl"

            files = cache_files_by_extension(
                test_directory,
                "hdf",
                cache_path=custom_cache
            )

            assert len(files) == 4
            assert custom_cache.exists()

    def test_multiple_extensions_isolated(self, test_directory):
        """Test that different extensions have separate caches"""
        hdf_files = cache_files_by_extension(test_directory, "hdf")
        print(hdf_files)
        nwb_files = cache_files_by_extension(test_directory, "nwb")

        assert len(hdf_files) == 4
        assert len(nwb_files) == 2

        # Check that both cache keys exist
        hdf_key = f"{test_directory}_hdf"
        nwb_key = f"{test_directory}_nwb"
        assert hdf_key in _cached_files
        assert nwb_key in _cached_files

    def test_cache_with_empty_directory(self):
        """Test caching empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cached_files = cache_files_by_extension(temp_dir, "hdf")
            assert cached_files == []


class TestGetCachedFiles:
    """Test the get_cached_files function"""

    def test_get_cached_files_with_directory(self, test_directory):
        """Test get_cached_files with explicit directory"""
        files = get_cached_files(test_directory, "hdf", max = 1000)

        assert len(files) == 4
        assert all(f.endswith('.hdf') for f in files)

    def test_get_cached_files_default_extension(self, test_directory):
        """Test that default extension is 'hdf'"""
        files = get_cached_files(test_directory)

        assert all(f.endswith('.hdf') for f in files)

    def test_get_cached_files_different_extensions(self, test_directory):
        """Test getting files with different extensions"""
        hdf_files = get_cached_files(test_directory, "hdf")
        nwb_files = get_cached_files(test_directory, "nwb")

        assert len(hdf_files) == 4
        assert len(nwb_files) == 2

    @pytest.mark.skip(reason="Requires Config setup - optional test")
    def test_get_cached_files_from_config_hdf(self):
        """Test getting HDF files from config path"""
        # This test requires proper Config setup
        # Uncomment and modify when Config is available

        # files = get_cached_files(extension="hdf")
        # assert isinstance(files, list)
        # assert all(f.endswith('.hdf') for f in files)
        pass

    @pytest.mark.skip(reason="Requires Config setup - optional test")
    def test_get_cached_files_from_config_nwb(self):
        """Test getting NWB files from config path"""
        # This test requires proper Config setup

        # files = get_cached_files(extension="nwb")
        # assert isinstance(files, list)
        # assert all(f.endswith('.nwb') for f in files)
        pass

    def test_get_cached_files_invalid_extension_no_config(self):
        """Test that unsupported extension without directory raises error"""
        with pytest.raises(ValueError, match="No default config path"):
            get_cached_files(extension="xyz")


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

# Run tests
#if __name__ == "__main__":
    #pytest.main([__file__, "-v", "-s"])
