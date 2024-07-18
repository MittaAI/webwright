import pytest
from unittest.mock import patch
from lib.functions.clear_screen import clear_screen  # Adjust this import path to match your project structure.

@pytest.mark.parametrize("os_name, expected_command", [
    ('Windows', 'cls'),  # For Windows OS
    ('Linux', 'clear'),  # For Linux OS
    ('Darwin', 'clear')  # For MacOS
])
def test_clear_screen(os_name, expected_command):
    with patch('os.system') as mock_system:
        with patch('platform.system', return_value=os_name):
            result = clear_screen()
            mock_system.assert_called_once_with(expected_command)
            assert result['success'] == True

def test_clear_screen_failure():
    with patch('os.system', side_effect=Exception("Test Exception")):
        with patch('platform.system', return_value='Windows'):
            result = clear_screen()
            assert result['success'] == False
            assert result['error'] == "Test Exception"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
