

import pytest

from aopy_nwb_conv.core.data_locator import data_locator
from aopy_nwb_conv.utils.config import Config
from aopy_nwb_conv.utils.date_validation import get_valid_preprocessed_dates


class TestDateValidation:
    """Test date validation in data locator."""

#    @pytest.mark.parametrize("date_str,expected", [
#        ("2024-03-15", True),
#        ("2024-02-30", False),  # Invalid date
#        ("15-03-2024", False),  # Wrong format
#        ("2024/03/15", False),  # Wrong separator
#        ("20240315", False),    # No separators
#    ])

    def test_get_valid_preprocessed_dates(self):
        """Test retrieval of valid dates for a subject."""
        config = Config()
        assert config is not None, "User must specify a config file"
        paths = config.get_paths()
        subjects = config.get_nhp_subjects()
        assert subjects is not None, "NHP subjects must be defined in config"
        print(config.get_date_format())
        all_folders = []
        #print(subjects[0:1])
        #for key, subject in subjects[0:1].items():
        key = list(subjects.keys())[0]
        subject = subjects[key]
        print(f"Subject code: {key}, Name: {subject}")
        folders = get_valid_preprocessed_dates(paths['monkey_preprocessed'], subject)
        all_folders.extend(folders)


        assert len(all_folders) > 0, "No valid preprocessed folders found."

    #def test_date_validation(self, date_str, expected):
    #    """Test date validation logic."""
    #    locator = data_locator("/path/to/test/data")
    #    is_valid = locator._is_valid_date(date_str)
    #    assert is_valid == expected

def test_subject_validation():
    """Test that invalid subject IDs raise an error."""
    locator = data_locator("/path/to/test/data")
    with pytest.raises(ValueError):
        locator.locate_session("InvalidSubject!", "2024-03-15", "session_001")

def test_locate_session_basic():
    """Test basic session location functionality."""
    # This test will fail initially - that's expected!
    locator = data_locator("/path/to/test/data")
    session = locator.locate_session("MonkeyA", "2024-03-15", "session_001")

    assert session.subject_id == "MonkeyA"
    assert session.session_id == "session_001"
    assert session.file_manifest is not None
