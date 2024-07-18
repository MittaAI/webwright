import pytest
import platform
import subprocess
from unittest.mock import patch, MagicMock
from lib.functions.browser import (
    find_chrome_executable,
    find_edge_executable,
    find_safari_executable,
    browser
)

is_windows = platform.system() == "Windows"
is_macos = platform.system() == "Darwin"

@pytest.fixture
def mock_platform_windows():
    with patch('platform.system', return_value='Windows'):
        yield

@pytest.fixture
def mock_platform_darwin():
    with patch('platform.system', return_value='Darwin'):
        yield

@pytest.mark.skipif(not is_windows, reason="Windows-specific test")
def test_find_chrome_executable_windows(mock_platform_windows):
    with patch('os.path.exists', return_value=True):
        assert find_chrome_executable() == r"C:\Program Files\Google\Chrome\Application\chrome.exe"

@pytest.mark.skipif(not is_macos, reason="macOS-specific test")
def test_find_chrome_executable_darwin(mock_platform_darwin):
    with patch('os.path.exists', return_value=True):
        assert find_chrome_executable() == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

@pytest.mark.skipif(not is_windows, reason="Windows-specific test")
def test_find_edge_executable_windows(mock_platform_windows):
    with patch('os.path.exists', return_value=True):
        assert find_edge_executable() == r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

@pytest.mark.skipif(not is_macos, reason="macOS-specific test")
def test_find_safari_executable_darwin(mock_platform_darwin):
    assert find_safari_executable() == "/Applications/Safari.app/Contents/MacOS/Safari"

@pytest.mark.parametrize("platform_mock, browser_path, expected_browser", [
    pytest.param('mock_platform_windows', r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Chrome", marks=pytest.mark.skipif(not is_windows, reason="Windows-specific test")),
    pytest.param('mock_platform_windows', r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "Edge", marks=pytest.mark.skipif(not is_windows, reason="Windows-specific test")),
    pytest.param('mock_platform_darwin', "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "Chrome", marks=pytest.mark.skipif(not is_macos, reason="macOS-specific test")),
    pytest.param('mock_platform_darwin', "/Applications/Safari.app/Contents/MacOS/Safari", "Safari", marks=pytest.mark.skipif(not is_macos, reason="macOS-specific test")),
])
def test_browser_success(request, platform_mock, browser_path, expected_browser):
    request.getfixturevalue(platform_mock)
    with patch('subprocess.Popen') as mock_popen:
        with patch('lib.functions.browser.find_chrome_executable', return_value=browser_path if expected_browser == "Chrome" else ""):
            with patch('lib.functions.browser.find_edge_executable', return_value=browser_path if expected_browser == "Edge" else ""):
                with patch('lib.functions.browser.find_safari_executable', return_value=browser_path if expected_browser == "Safari" else ""):
                    result = browser("https://example.com")
                    assert result["success"] == True
                    assert expected_browser in result["message"]
                    mock_popen.assert_called_once_with([browser_path, "https://example.com"])

@pytest.mark.skipif(not is_windows, reason="Windows-specific test")
def test_browser_failure_windows():
    with patch('platform.system', return_value='Windows'):
        with patch('lib.functions.browser.find_chrome_executable', return_value=""):
            with patch('lib.functions.browser.find_edge_executable', return_value=""):
                result = browser("https://example.com")
                assert result["success"] == False
                assert "Neither Chrome nor Edge executables were found" in result["message"]

@pytest.mark.skipif(not is_macos, reason="macOS-specific test")
def test_browser_failure_macos():
    with patch('platform.system', return_value='Darwin'):
        with patch('lib.functions.browser.find_chrome_executable', return_value=""):
            with patch('lib.functions.browser.find_safari_executable', return_value=""):
                result = browser("https://example.com")
                assert result["success"] == False
                assert "Neither Chrome nor Safari executables were found" in result["message"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])