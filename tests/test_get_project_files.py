import pytest
import os
from unittest.mock import mock_open, patch
from lib.functions.cat_file import cat_file

@pytest.fixture
def mock_file_content():
    return "This is the content of the file."

def test_successful_file_read(tmp_path, mock_file_content):
    test_file = tmp_path / "test_file.txt"
    test_file.write_text(mock_file_content)

    result = cat_file(str(test_file))
    assert result["success"] == True
    assert result["contents"] == mock_file_content

def test_file_not_found():
    non_existent_file = "/path/to/non_existent_file.txt"
    result = cat_file(non_existent_file)
    assert result["success"] == False
    assert result["error"] == "File not found"
    assert f"The file '{non_existent_file}' does not exist." in result["reason"]

@patch('os.path.isfile', return_value=True)
@patch('builtins.open', side_effect=PermissionError)
def test_permission_denied(mock_open, mock_isfile):
    file_path = "/path/to/protected_file.txt"
    result = cat_file(file_path)
    assert result["success"] == False
    assert result["error"] == "Permission denied"
    assert f"You do not have permission to read the file '{file_path}'." in result["reason"]

@patch('os.path.isfile', return_value=True)
@patch('builtins.open', side_effect=IOError("Mock IO Error"))
def test_generic_exception(mock_open, mock_isfile):
    file_path = "/path/to/problematic_file.txt"
    result = cat_file(file_path)
    assert result["success"] == False
    assert result["error"] == "File reading failed"
    assert "Mock IO Error" in result["reason"]

@patch('os.path.isfile', return_value=True)
def test_empty_file(mock_isfile, tmp_path):
    test_file = tmp_path / "empty_file.txt"
    test_file.write_text("")

    result = cat_file(str(test_file))
    assert result["success"] == True
    assert result["contents"] == ""

@patch('os.path.isfile', return_value=True)
def test_large_file(mock_isfile):
    large_content = "A" * 1048576  # 1 MB of content
    with patch('builtins.open', mock_open(read_data=large_content)):
        result = cat_file("/path/to/large_file.txt")
        assert result["success"] == True
        assert result["contents"] == large_content

@pytest.mark.parametrize("file_path, expected_error, expected_reason", [
    ("", "Invalid input", "File path cannot be empty"),
    (None, "Invalid input", "Expected a string for file_path, got NoneType"),
    (123, "Invalid input", "Expected a string for file_path, got int"),
    ([], "Invalid input", "Expected a string for file_path, got list"),
    ({}, "Invalid input", "Expected a string for file_path, got dict"),
])
def test_invalid_file_path(file_path, expected_error, expected_reason):
    result = cat_file(file_path)
    assert result["success"] == False
    assert result["error"] == expected_error
    assert expected_reason in result["reason"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])