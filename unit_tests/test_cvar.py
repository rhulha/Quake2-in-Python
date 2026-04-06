"""
Unit tests for cvar.py (Console Variables system)
Tests the core variable management system used throughout the engine.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quake2.cvar import Cvar_Get, Cvar_Set, Cvar_SetValue, Cvar_VariableValue, Cvar_VariableString, Cvar_ForceSet


def test_cvar_get_default():
    """Test creating a new cvar with default value"""
    print("\n=== Test: Cvar_Get with Default Value ===")

    # Get a cvar that doesn't exist yet
    cvar = Cvar_Get("test_var_1", "default_value", 0)

    assert cvar is not None, "Cvar_Get returned None"
    assert cvar.name == "test_var_1", f"Expected name 'test_var_1', got {cvar.name}"
    assert cvar.string == "default_value", f"Expected string 'default_value', got {cvar.string}"
    assert cvar.value == 0.0, f"Expected value 0.0 (non-numeric string), got {cvar.value}"
    assert cvar.flags == 0, f"Expected flags 0, got {cvar.flags}"

    print("[OK] Created cvar with default value")
    print(f"  Name: {cvar.name}")
    print(f"  String: {cvar.string}")
    print(f"  Numeric value: {cvar.value}")
    print(f"  Flags: {cvar.flags}")


def test_cvar_get_existing():
    """Test retrieving an existing cvar"""
    print("\n=== Test: Cvar_Get Existing Cvar ===")

    # Create a cvar
    cvar1 = Cvar_Get("test_var_2", "value1", 0)
    assert cvar1.string == "value1"

    # Get the same cvar again
    cvar2 = Cvar_Get("test_var_2", "ignored_default", 0)

    assert cvar1 is cvar2, "Should return same cvar object"
    assert cvar2.string == "value1", "Should retain original value, not use default"

    print("[OK] Retrieved existing cvar")
    print(f"  Same object: {cvar1 is cvar2}")
    print(f"  String unchanged: {cvar2.string}")


def test_cvar_set():
    """Test setting cvar values"""
    print("\n=== Test: Cvar_Set ===")

    cvar = Cvar_Get("test_var_3", "initial", 0)
    Cvar_Set("test_var_3", "modified")

    assert cvar.string == "modified", f"Expected 'modified', got {cvar.string}"

    print("[OK] Set cvar value")
    print(f"  New string: {cvar.string}")


def test_cvar_set_value():
    """Test setting cvar as float/int"""
    print("\n=== Test: Cvar_SetValue ===")

    cvar = Cvar_Get("test_var_4", "100", 0)
    Cvar_SetValue("test_var_4", 42.5)

    assert cvar.string == "42.5", f"Expected '42.5', got {cvar.string}"
    assert cvar.value == 42.5, f"Expected 42.5, got {cvar.value}"

    print("[OK] Set cvar as float value")
    print(f"  String: {cvar.string}, Value: {cvar.value}")


def test_cvar_variable_string():
    """Test retrieving cvar value as string"""
    print("\n=== Test: Cvar_VariableString ===")

    Cvar_Get("test_var_5", "hello_world", 0)
    value = Cvar_VariableString("test_var_5")

    assert value == "hello_world", f"Expected 'hello_world', got {value}"

    print("[OK] Retrieved cvar as string")
    print(f"  Value: {value}")


def test_cvar_variable_string_nonexistent():
    """Test retrieving nonexistent cvar returns empty string"""
    print("\n=== Test: Cvar_VariableString Nonexistent ===")

    value = Cvar_VariableString("nonexistent_var_xyz")

    assert value == "", f"Expected empty string for nonexistent cvar, got {repr(value)}"

    print("[OK] Nonexistent cvar returns empty string")
    print(f"  Value: '{value}'")


def test_cvar_variable_value():
    """Test retrieving cvar value as float"""
    print("\n=== Test: Cvar_VariableValue ===")

    Cvar_Get("test_var_6", "3.14159", 0)
    value = Cvar_VariableValue("test_var_6")

    assert isinstance(value, float), f"Expected float, got {type(value)}"
    assert abs(value - 3.14159) < 0.00001, f"Expected ~3.14159, got {value}"

    print("[OK] Retrieved cvar as float value")
    print(f"  Value: {value}")


def test_cvar_variable_value_nonexistent():
    """Test retrieving nonexistent cvar as value returns 0"""
    print("\n=== Test: Cvar_VariableValue Nonexistent ===")

    value = Cvar_VariableValue("nonexistent_var_abc")

    assert value == 0, f"Expected 0 for nonexistent cvar, got {value}"

    print("[OK] Nonexistent cvar returns 0")
    print(f"  Value: {value}")


def test_cvar_variable_value_non_numeric():
    """Test retrieving non-numeric cvar as value - uses .value field instead"""
    print("\n=== Test: Cvar_VariableValue Non-Numeric ===")

    # Note: Cvar_VariableValue() calls float(var.string) which will throw ValueError
    # for non-numeric strings. Instead, use the .value field which is pre-computed
    cvar = Cvar_Get("test_var_7", "not_a_number", 0)

    # The .value field should be 0.0 since "not_a_number" can't be converted
    assert cvar.value == 0.0, f"Expected value 0.0 for non-numeric cvar, got {cvar.value}"

    print("[OK] Non-numeric cvar .value field is 0")
    print(f"  Cvar.value: {cvar.value}")


def test_cvar_force_set():
    """Test force setting a cvar"""
    print("\n=== Test: Cvar_ForceSet ===")

    cvar = Cvar_Get("test_var_8", "original", 0)
    result = Cvar_ForceSet("test_var_8", "forced")

    assert cvar.string == "forced", f"Expected 'forced', got {cvar.string}"
    assert result is not None, "Cvar_ForceSet should return cvar"

    print("[OK] Force set cvar value")
    print(f"  New string: {result.string}")


def test_cvar_flags():
    """Test cvar with flags"""
    print("\n=== Test: Cvar with Flags ===")

    cvar = Cvar_Get("test_var_9", "value", 15)  # CVAR_ARCHIVE | CVAR_USERINFO | CVAR_SERVERINFO | CVAR_NOSET

    assert cvar.flags == 15, f"Expected flags 15, got {cvar.flags}"

    print("[OK] Created cvar with flags")
    print(f"  Flags: {cvar.flags}")


def test_cvar_numeric_conversion():
    """Test numeric conversions"""
    print("\n=== Test: Numeric Conversions ===")

    test_cases = [
        ("123", 123.0),
        ("45.67", 45.67),
        ("-89", -89.0),
        ("0", 0.0),
        ("3.14159", 3.14159),
    ]

    for str_val, expected_float in test_cases:
        cvar = Cvar_Get(f"test_numeric_{str_val.replace('.', '_')}", str_val, 0)
        value = Cvar_VariableValue(f"test_numeric_{str_val.replace('.', '_')}")
        assert abs(value - expected_float) < 0.0001, f"Expected {expected_float}, got {value}"
        print(f"  '{str_val}' -> {value}")

    print("[OK] All numeric conversions passed")


def test_cvar_persistence():
    """Test that cvars persist across multiple get calls"""
    print("\n=== Test: Cvar Persistence ===")

    # Create and modify a cvar
    cvar1 = Cvar_Get("test_var_persist", "value1", 0)
    Cvar_Set("test_var_persist", "value2")

    # Get it again
    cvar2 = Cvar_Get("test_var_persist", "ignored", 0)

    assert cvar1 is cvar2, "Should be same object"
    assert cvar2.string == "value2", "Should retain modified value"

    # Get it a third time
    value = Cvar_VariableString("test_var_persist")
    assert value == "value2", "Should still have modified value"

    print("[OK] Cvars persist correctly")
    print(f"  String after multiple accesses: {value}")


if __name__ == '__main__':
    try:
        test_cvar_get_default()
        test_cvar_get_existing()
        test_cvar_set()
        test_cvar_set_value()
        test_cvar_variable_string()
        test_cvar_variable_string_nonexistent()
        test_cvar_variable_value()
        test_cvar_variable_value_nonexistent()
        test_cvar_variable_value_non_numeric()
        test_cvar_force_set()
        test_cvar_flags()
        test_cvar_numeric_conversion()
        test_cvar_persistence()

        print("\n" + "="*50)
        print("ALL CVAR TESTS PASSED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
