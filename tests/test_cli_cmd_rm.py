# tests/test_cli_cmd_rm.py
import os
import pytest
from click.testing import CliRunner
import click
from unittest.mock import patch, MagicMock

from edpm.cli.rm import rm_command
from edpm.engine.api import EdpmApi

# Create a test CLI that includes only the 'rm' command
@click.group()
@click.pass_context
def cli(ctx):
    pass

cli.add_command(rm_command, "rm")


@pytest.fixture
def runner():
    """Provides a Click CliRunner for capturing output."""
    return CliRunner()


@pytest.fixture
def mock_api():
    """Create a mock API with controlled behavior for testing"""
    api = MagicMock(spec=EdpmApi)

    # Mock plan with test packages
    mock_plan = MagicMock()
    mock_plan.find_package.side_effect = lambda name: name in ["test-pkg", "existing-pkg"]
    api.plan = mock_plan

    # Mock lock with test packages installed
    mock_lock = MagicMock()
    mock_lock.is_installed.side_effect = lambda name: name in ["test-pkg", "existing-pkg"]

    # Set up mock package data
    test_pkg_data = {
        "install_path": "/mock/top/dir/test-pkg/install",
        "source_path": "/mock/top/dir/test-pkg/source",
        "build_path": "/mock/top/dir/test-pkg/build",
        "owned": True
    }

    existing_pkg_data = {
        "install_path": "/external/path/existing-pkg",
        "owned": False
    }

    def get_installed_package(name):
        if name == "test-pkg":
            return test_pkg_data
        elif name == "existing-pkg":
            return existing_pkg_data
        return None

    mock_lock.get_installed_package.side_effect = get_installed_package
    api.lock = mock_lock

    return api


@patch('os.path.exists', return_value=True)
def test_rm_owned_package_auto(mock_exists, runner, mock_api):
    """Test removing an owned package with default auto mode"""
    with patch('shutil.rmtree') as mock_rmtree:
        result = runner.invoke(cli, ["rm", "test-pkg"], obj=mock_api)

        # Check command output
        assert result.exit_code == 0
        assert "Removing package:" in result.output
        assert "/mock/top/dir/test-pkg/install" in result.output

        # Verify lock file was updated
        mock_api.lock.remove_package.assert_called_once_with("test-pkg")
        mock_api.lock.save.assert_called_once()

        # Verify environment scripts were updated
        mock_api.save_generator_scripts.assert_called_once()

        # Verify folders were removed
        assert mock_rmtree.call_count == 3  # install, source, build folders


@patch('os.path.exists', return_value=True)
def test_rm_nonowned_package_auto(mock_exists, runner, mock_api):
    """Test removing a non-owned package with default auto mode - should not remove folders"""
    with patch('shutil.rmtree') as mock_rmtree:
        result = runner.invoke(cli, ["rm", "existing-pkg"], obj=mock_api)

        # Check command output
        assert result.exit_code == 0
        assert "Removing package:" in result.output
        assert "/external/path/existing-pkg" in result.output
        assert "Package is not 'owned' by edpm" in result.output

        # Verify lock file was updated
        mock_api.lock.remove_package.assert_called_once_with("existing-pkg")
        mock_api.lock.save.assert_called_once()

        # Verify environment scripts were updated
        mock_api.save_generator_scripts.assert_called_once()

        # Verify folders were NOT removed
        mock_rmtree.assert_not_called()


@patch('os.path.exists', return_value=True)
def test_rm_nonowned_package_all(mock_exists, runner, mock_api):
    """Test removing a non-owned package with --all flag - should remove folders"""
    with patch('shutil.rmtree') as mock_rmtree:
        result = runner.invoke(cli, ["rm", "existing-pkg", "--all"], obj=mock_api)

        # Check command output
        assert result.exit_code == 0
        assert "Removing package:" in result.output

        # Verify lock file was updated
        mock_api.lock.remove_package.assert_called_once_with("existing-pkg")

        # Verify environment scripts were updated
        mock_api.save_generator_scripts.assert_called_once()

        # Verify folder was removed (despite not being owned)
        mock_rmtree.assert_called_once_with("/external/path/existing-pkg")


@patch('os.path.exists', return_value=True)
def test_rm_lock_only(mock_exists, runner, mock_api):
    """Test removing just the lock entry with --lock flag"""
    with patch('shutil.rmtree') as mock_rmtree:
        result = runner.invoke(cli, ["rm", "test-pkg", "--lock"], obj=mock_api)

        # Check command output
        assert result.exit_code == 0

        # Verify lock file was updated
        mock_api.lock.remove_package.assert_called_once_with("test-pkg")

        # Verify environment scripts were updated
        mock_api.save_generator_scripts.assert_called_once()

        # Verify folders were NOT removed
        mock_rmtree.assert_not_called()


def test_rm_package_not_found(runner, mock_api):
    """Test removing a package that's not in the plan"""
    result = runner.invoke(cli, ["rm", "unknown-pkg"], obj=mock_api)

    # Check command output
    assert result.exit_code != 0
    assert "Package 'unknown-pkg' not found in the plan" in result.output

    # Verify lock file was not updated
    mock_api.lock.remove_package.assert_not_called()
    mock_api.lock.save.assert_not_called()


def test_rm_package_not_installed(runner, mock_api):
    """Test removing a package that's in the plan but not installed"""
    # Temporarily modify the mock behavior
    original_side_effect = mock_api.lock.is_installed.side_effect
    mock_api.lock.is_installed.side_effect = lambda name: False

    result = runner.invoke(cli, ["rm", "test-pkg"], obj=mock_api)

    # Restore original behavior
    mock_api.lock.is_installed.side_effect = original_side_effect

    # Check command output
    assert result.exit_code != 0
    assert "Package 'test-pkg' is not installed" in result.output

    # Verify lock file was not updated
    mock_api.lock.remove_package.assert_not_called()
    mock_api.lock.save.assert_not_called()