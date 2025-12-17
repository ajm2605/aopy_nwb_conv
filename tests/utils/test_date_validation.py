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






# Run tests
#if __name__ == "__main__":
    #pytest.main([__file__, "-v", "-s"])
