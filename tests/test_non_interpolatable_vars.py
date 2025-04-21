import unittest
import main

def test_non_interpolatable_variables():
    """Test that the NON_INTERPOLATABLE_VARIABLES list has no duplicates."""
    assert main.NON_INTERPOLATABLE_VARIABLES == ["error", "winddirection", "rain", "barometric_trend"]
    
    # Check each element appears only once
    for var in main.NON_INTERPOLATABLE_VARIABLES:
        assert main.NON_INTERPOLATABLE_VARIABLES.count(var) == 1, f"{var} appears multiple times"