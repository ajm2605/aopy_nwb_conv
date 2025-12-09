import pytest
from pathlib import Path

"""from aopy_nwb_conv.core.data_locator import DataLocator

def test_subject_validation():
    """Test that invalid subject IDs raise an error."""
    locator = DataLocator("/path/to/test/data")
    with pytest.raises(ValueError):
        locator.locate_session("InvalidSubject!", "2024-03-15", "session_001")

def test_locate_session_basic():
    """Test basic session location functionality."""
    # This test will fail initially - that's expected!
    locator = DataLocator("/path/to/test/data")
    session = locator.locate_session("MonkeyA", "2024-03-15", "session_001")
    
    assert session.subject_id == "MonkeyA"
    assert session.session_id == "session_001"
    assert session.file_manifest is not None"""