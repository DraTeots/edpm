# tests/test_lockfile.py

import os
import pytest
import tempfile
from unittest.mock import patch
from edpm.engine.lockfile import LockfileConfig

def test_lockfile_init():
    """Test initialization of LockfileConfig."""
    lock = LockfileConfig()
    assert lock.file_path == ""
    assert lock.data["file_version"] == LockfileConfig.DEFAULT_FILE_VERSION
    assert lock.data["top_dir"] == ""
    assert lock.data["packages"] == {}
    assert lock.is_loaded == False

def test_lockfile_load_save():
    """Test loading and saving a lock file."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create and save a lock file
        lock = LockfileConfig()
        lock.top_dir = "/test/dir"
        lock.data["packages"]["test"] = {"install_path": "/test/install"}
        lock.save(tmp_path)

        # Load it back and check
        lock2 = LockfileConfig()
        lock2.load(tmp_path)
        assert lock2.top_dir == "/test/dir"
        assert "test" in lock2.data["packages"]
        assert lock2.data["packages"]["test"]["install_path"] == "/test/install"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_lockfile_get_installed_package():
    """Test getting an installed package."""
    lock = LockfileConfig()
    lock.data["packages"]["test"] = {"install_path": "/test/install"}

    package = lock.get_installed_package("test")
    assert package["install_path"] == "/test/install"

    # Non-existent package should return empty dict
    assert lock.get_installed_package("nonexistent") == {}

def test_lockfile_is_installed():
    """Test checking if a package is installed."""
    lock = LockfileConfig()

    # Mock os.path.isdir to always return True for testing
    with patch('os.path.isdir', return_value=True):
        # Not installed yet
        assert lock.is_installed("test") == False

        # Add it with an install_path
        lock.data["packages"]["test"] = {"install_path": "/test/install"}
        assert lock.is_installed("test") == True

        # Empty install_path should return False
        lock.data["packages"]["empty"] = {"install_path": ""}
        assert lock.is_installed("empty") == False

def test_lockfile_update_package():
    """Test updating a package."""
    lock = LockfileConfig()

    # Update a non-existent package
    lock.update_package("test", {"install_path": "/test/install"})
    assert "test" in lock.data["packages"]
    assert lock.data["packages"]["test"]["install_path"] == "/test/install"

    # Update an existing package
    lock.update_package("test", {"version": "1.0"})
    assert lock.data["packages"]["test"]["install_path"] == "/test/install"
    assert lock.data["packages"]["test"]["version"] == "1.0"

def test_lockfile_get_installed_packages():
    """Test getting all installed packages."""
    lock = LockfileConfig()
    assert lock.get_installed_packages() == []

    lock.data["packages"]["test1"] = {}
    lock.data["packages"]["test2"] = {}

    packages = lock.get_installed_packages()
    assert len(packages) == 2
    assert "test1" in packages
    assert "test2" in packages

def test_lockfile_remove_package():
    """Test removing a package."""
    lock = LockfileConfig()
    lock.data["packages"]["test"] = {"install_path": "/test/install"}

    assert "test" in lock.data["packages"]
    lock.remove_package("test")
    assert "test" not in lock.data["packages"]

    # Removing a non-existent package should not raise an error
    lock.remove_package("nonexistent")  # Should not raise any exception

def test_lockfile_save_no_path():
    """Test saving without a path raises an error."""
    lock = LockfileConfig()
    with pytest.raises(ValueError, match="No file path to save lockfile"):
        lock.save()

def test_lockfile_top_dir_property():
    """Test the top_dir property getter and setter."""
    lock = LockfileConfig()
    assert lock.top_dir == ""

    lock.top_dir = "/new/path"
    assert lock.top_dir == "/new/path"
    assert lock.data["top_dir"] == "/new/path"

def test_lockfile_load_nonexistent_file():
    """Test loading a non-existent file."""
    lock = LockfileConfig()
    # Use a temp path that definitely doesn't exist
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = os.path.join(tmpdir, "nonexistent.yaml")
        lock.load(nonexistent_path)
        assert lock.file_path == nonexistent_path
        assert lock.is_loaded == False