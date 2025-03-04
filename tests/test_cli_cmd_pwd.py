# tests/test_cli_cmd_pwd.py
import os
import pytest
from click.testing import CliRunner
import click
from unittest.mock import patch, MagicMock

from edpm.cli.pwd import pwd_command
from edpm.engine.api import EdpmApi

# Create a test CLI that includes only the 'pwd' command
@click.group()
@click.pass_context
def cli(ctx):
    pass

cli.add_command(pwd_command, "pwd")


@pytest.fixture
def runner():
    """Provides a Click CliRunner for capturing output."""
    return CliRunner()


@pytest.fixture
def mock_api():
    """Create a mock API with controlled behavior for testing"""
    api = MagicMock(spec=EdpmApi)
    api.top_dir = "/mock/top/dir"

    # Mock plan with a test package
    mock_plan = MagicMock()
    mock_plan.find_package.return_value = True  # Any package exists in plan
    mock_plan.find_package.side_effect = lambda name: name in ["test-pkg", "existing-pkg"]
    api.plan = mock_plan

    # Mock lock with test package installed
    mock_lock = MagicMock()
    mock_lock.is_installed.return_value = False  # Default: not installed
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


def test_pwd_no_args(runner, mock_api):
    """Test 'edpm pwd' with no arguments - should show top dir"""
    result = runner.invoke(cli, ["pwd"], obj=mock_api)
    assert result.exit_code == 0
    assert "/mock/top/dir" in result.output


def test_pwd_with_package(runner, mock_api):
    """Test 'edpm pwd test-pkg' - should show all paths"""
    result = runner.invoke(cli, ["pwd", "test-pkg"], obj=mock_api)
    assert result.exit_code == 0
    assert "Install path:" in result.output
    assert "/mock/top/dir/test-pkg/install" in result.output
    assert "Sources:" in result.output
    assert "/mock/top/dir/test-pkg/source" in result.output
    assert "Build dir:" in result.output
    assert "/mock/top/dir/test-pkg/build" in result.output
    assert "edpm 'owned' base path:" in result.output


def test_pwd_with_existing_package(runner, mock_api):
    """Test with an existing (not owned) package"""
    result = runner.invoke(cli, ["pwd", "existing-pkg"], obj=mock_api)
    assert result.exit_code == 0
    assert "Install path:" in result.output
    assert "/external/path/existing-pkg" in result.output
    assert "edpm 'owned' base path:" not in result.output  # Should not show for non-owned


def test_pwd_install_only(runner, mock_api):
    """Test 'edpm pwd test-pkg --install' - should only show install path"""
    result = runner.invoke(cli, ["pwd", "test-pkg", "--install"], obj=mock_api)
    assert result.exit_code == 0
    assert result.output.strip() == "/mock/top/dir/test-pkg/install"


def test_pwd_source_only(runner, mock_api):
    """Test 'edpm pwd test-pkg --source' - should only show source path"""
    result = runner.invoke(cli, ["pwd", "test-pkg", "--source"], obj=mock_api)
    assert result.exit_code == 0
    assert result.output.strip() == "/mock/top/dir/test-pkg/source"


def test_pwd_build_only(runner, mock_api):
    """Test 'edpm pwd test-pkg --build' - should only show build path"""
    result = runner.invoke(cli, ["pwd", "test-pkg", "--build"], obj=mock_api)
    assert result.exit_code == 0
    assert result.output.strip() == "/mock/top/dir/test-pkg/build"


def test_pwd_package_not_found(runner, mock_api):
    """Test with a package that doesn't exist in the plan"""
    result = runner.invoke(cli, ["pwd", "unknown-pkg"], obj=mock_api)
    assert result.exit_code != 0
    assert "Error: Package 'unknown-pkg' not found in the plan" in result.output


def test_pwd_package_not_installed(runner, mock_api):
    """Test with a package that exists in plan but is not installed"""
    # Temporarily modify the mock behavior
    original_side_effect = mock_api.lock.is_installed.side_effect
    mock_api.lock.is_installed.side_effect = lambda name: False

    result = runner.invoke(cli, ["pwd", "test-pkg"], obj=mock_api)

    # Restore original behavior
    mock_api.lock.is_installed.side_effect = original_side_effect

    assert result.exit_code != 0
    assert "Error: Package 'test-pkg' is not installed" in result.output