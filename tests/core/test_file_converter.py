import pytest
from pathlib import Path
from aopy_nwb_conv.core.file_converter import preproc_find_session_file_paths, raw_ecube_find_session_file_paths
from aopy_nwb_conv.utils.config import Config

from probeinterface import write_probeinterface, read_probeinterface
class TestFindSessionFilePaths:
    """Test find session file paths"""
    config = Config()
    preprocessed_path = config.get_paths()['monkey_preprocessed']
    test_subject = 'churro'
    test_te_id = 21077

    def test_config_working(self):
        """Test that config loads successfully"""
        assert self.config is not None
        paths = self.config.get_paths()
        assert 'monkey_preprocessed' in paths
        assert 'monkey_raw' in paths
        assert paths['monkey_preprocessed'].exists()

    def test_get_valid_preprocessed_file_paths(self):
        """Test that preprocessed file paths are found and categorized correctly"""
        session_paths = preproc_find_session_file_paths(self.test_subject, self.test_te_id)
        
        # Should return a dictionary
        assert isinstance(session_paths, dict)
        
        # Should have at least some file types
        assert len(session_paths) > 0
        
        # All values should be Path objects
        for path in session_paths.values():
            assert isinstance(path, Path)
            assert path.exists()
            assert path.suffix == '.hdf'
            assert str(self.test_te_id) in path.name

    def test_preprocessed_invalid_te_id(self):
        """Test that invalid TE ID returns empty or raises appropriate error"""
        invalid_te_id = 99999
        session_paths = preproc_find_session_file_paths(self.test_subject, invalid_te_id)
        
        # Should return empty dict when no files found
        assert len(session_paths) == 0

    def test_raw_ecube_find_session_file_paths(self):
        """Test that raw ecube session files are found and categorized correctly"""
        session_paths = raw_ecube_find_session_file_paths(self.test_te_id)
        
        # Should return a dictionary with expected categories
        assert isinstance(session_paths, dict)
        assert 'Analog' in session_paths
        assert 'Digital' in session_paths
        assert 'Headstage' in session_paths
        assert 'Settings' in session_paths
        
        # At least one category should have files
        total_files = sum(len(files) for files in session_paths.values())
        assert total_files > 0
        
        # All returned paths should be strings and exist
        for category, file_list in session_paths.items():
            for file_path in file_list:
                assert isinstance(file_path, str)
                assert Path(file_path).exists()

    def test_raw_ecube_invalid_te_id(self):
        """Test that invalid TE ID raises FileNotFoundError"""
        invalid_te_id = 99999
        
        with pytest.raises(FileNotFoundError, match=f"No raw ecube session found for TE ID {invalid_te_id}"):
            raw_ecube_find_session_file_paths(invalid_te_id)

    def test_raw_ecube_file_categorization(self):
        """Test that files are correctly categorized by type"""
        session_paths = raw_ecube_find_session_file_paths(self.test_te_id)
        
        # Settings files should contain 'settings' in filename
        for settings_file in session_paths['Settings']:
            assert 'settings' in Path(settings_file).name.lower()
        
        # Analog files should contain 'analog' (and not 'settings')
        for analog_file in session_paths['Analog']:
            filename = Path(analog_file).name.lower()
            assert 'analog' in filename
            assert 'settings' not in filename

class TestConvertAopyToNWB:
    """Test find session file paths"""
    config = Config()
    preprocessed_path = config.get_paths()['monkey_preprocessed']
    test_subject = 'churro'
    test_te_id = 21077

    def test_config_probe(self):
        t = self.config.get('probeinterface_paths')
        print(read_probeinterface(t['churro_fma']))
    #def test_conversion(self):
    #    convert_aopy_to_nwb(self.test_te_id, )