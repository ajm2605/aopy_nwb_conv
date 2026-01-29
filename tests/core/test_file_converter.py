import pytest
from pathlib import Path
from aopy_nwb_conv.core.file_converter import preproc_find_session_file_paths, raw_ecube_filepath_metadata, parse_ecube_raw_files, convert_aopy_to_nwb
from aopy_nwb_conv.utils.config import Config

from aopy.data.bmi3d import load_ecube_metadata
from probeinterface import write_probeinterface, read_probeinterface
from aopy_nwb_conv.utils.date_validation import default_extract_date_from_string
from aopy.data.db import lookup_sessions
import numpy as np

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
        session_paths = raw_ecube_filepath_metadata(self.test_subject, self.test_te_id)
        
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


class TestRawEcubeFilepathMetadata:
    """Test raw_ecube_filepath_metadata function"""
    config = Config()
    test_te_id = 21077
    
    def test_metadata_structure(self):
        """Test that metadata has correct structure"""
        metadata = raw_ecube_filepath_metadata(self.test_te_id)

        assert metadata is not None
        assert 'Analog' in metadata
        assert 'Digital' in metadata
        assert 'Headstage' in metadata
    
    def test_metadata_contains_file_paths(self):
        """Test that each category's metadata contains file_paths key"""
        metadata = raw_ecube_filepath_metadata(self.test_te_id)
        
        for category, metadata_dict in metadata.items():
            # Each category should have a metadata dictionary
            assert isinstance(metadata_dict, dict)
            
            # Should contain file_paths key
            assert 'file_paths' in metadata_dict
            
            # file_paths should be a list
            assert isinstance(metadata_dict['file_paths'], list)
    
    def test_metadata_file_paths_exist(self):
        """Test that all file paths in metadata actually exist"""
        metadata = raw_ecube_filepath_metadata(self.test_te_id)
        
        for category, metadata_dict in metadata.items():
            for file_path in metadata_dict['file_paths']:
                # Should be a string path
                assert isinstance(file_path, str)
                
                # Path should exist
                assert Path(file_path).exists()
    
    def test_metadata_has_additional_info(self):
        """Test that metadata contains more than just file_paths"""
        metadata = raw_ecube_filepath_metadata(self.test_te_id)
        
        # At least one category should have metadata beyond file_paths
        has_additional_metadata = False
        for category, metadata_dict in metadata.items():
            if len(metadata_dict.keys()) > 1:  # More than just 'file_paths'
                has_additional_metadata = True
                break
        
        assert has_additional_metadata, "Metadata should contain information beyond just file_paths"
    
    def test_metadata_file_categorization(self):
        """Test that files in each category match their category name"""
        metadata = raw_ecube_filepath_metadata(self.test_te_id)
        
        
        # Analog files should contain 'analog' (and not 'settings')
        for analog_file in metadata['Analog']['file_paths']:
            filename = Path(analog_file).name.lower()
            assert 'analog' in filename
            assert 'settings' not in filename
        
        # Digital files should contain 'digital'
        for digital_file in metadata['Digital']['file_paths']:
            filename = Path(digital_file).name.lower()
            assert 'digital' in filename
            assert 'settings' not in filename
        
        # Headstage files should contain 'headstage'
        for headstage_file in metadata['Headstage']['file_paths']:
            filename = Path(headstage_file).name.lower()
            assert 'headstage' in filename
            assert 'settings' not in filename

class TestConvertAopyToNWB:
    """Test find session file paths"""
    config = Config()
    preprocessed_path = config.get_paths()['monkey_preprocessed']
    test_subject = 'churro'
    test_te_id = 21077

    entry = lookup_sessions(subject=test_subject, id=test_te_id)[0]

    def test_config_probe(self):
        t = self.config.get_probes()
        print(t['churro_fma'])
    
    def test_conversion(self):
        recording, data, metadata, prb = convert_aopy_to_nwb(self.entry, None)
        #print(self.config.get_paths())
        print(metadata)
        print(data.dtype)
        print(recording)