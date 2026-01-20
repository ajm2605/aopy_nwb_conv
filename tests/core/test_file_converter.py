import pytest

from aopy_nwb_conv.core.file_converter import preproc_find_session_file_paths
from aopy_nwb_conv.utils.config import Config
from aopy_nwb_conv.utils.date_validation import get_valid_preprocessed_dates


class TestFindSessionFilePaths:
    """Test find session file paths"""
    config = Config()
    preprocessed_path = config.get_paths()['monkey_preprocessed']
    test_subject = 'churro'
    test_te_id = 21077


    def test_get_valid_preprocessed_file_paths(self):
        session_paths = preproc_find_session_file_paths(self.test_subject, self.test_te_id)
        print(session_paths)

    def test_config_working(self):
        print(self.config.get_paths())
        assert self.config is not None