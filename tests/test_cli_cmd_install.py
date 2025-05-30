import os
import pytest
import click
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from edpm.cli.install import install_command
from edpm.engine.api import EdpmApi
from edpm.engine.planfile import PlanFile


@pytest.fixture
def mock_edpm_api():
    """Create a mock EdpmApi object with necessary attributes."""
    api = MagicMock(spec=EdpmApi)
    api.plan = MagicMock()
    api.plan_file = "test_plan.edpm.yaml"
    return api


@pytest.fixture
def cli_runner():
    """Return a Click CLI test runner."""
    return CliRunner()


def test_install_no_arguments(mock_edpm_api, cli_runner):
    """Test 'edpm install' with no arguments - should install all packages in plan."""
    # Setup mock API
    # Create proper mock packages with name attributes that return strings
    pkg1 = MagicMock()
    pkg1.name = "pkg1"
    pkg2 = MagicMock()
    pkg2.name = "pkg2"
    mock_edpm_api.plan.packages.return_value = [pkg1, pkg2]

    # We need to make the instance check pass by patching isinstance
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"

    # Should call install_dependency_chain with all package names as a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1", "pkg2"],
        explain=False,
        force=False
    )
    # Should call save_generator_scripts
    mock_edpm_api.save_generator_scripts.assert_called_once()


def test_install_no_packages_in_plan(mock_edpm_api, cli_runner):
    """Test 'edpm install' when there are no packages in the plan."""
    # Setup mock API
    mock_edpm_api.plan.packages.return_value = []

    # We need to make the instance check pass by patching isinstance
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"
    assert "No dependencies in the plan" in result.output

    # Should not call install_dependency_chain
    mock_edpm_api.install_dependency_chain.assert_not_called()


def test_install_with_specific_package(mock_edpm_api, cli_runner):
    """Test 'edpm install pkg1' with a package that exists in the plan."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = True

    # We need to make the instance check pass by patching isinstance
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["pkg1"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"

    # Should check if package exists
    mock_edpm_api.plan.has_package.assert_called_once_with("pkg1")

    # Should call install_dependency_chain with the specified package as a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1"],
        explain=False,
        force=False
    )
    # Should call save_generator_scripts
    mock_edpm_api.save_generator_scripts.assert_called_once()


def test_install_package_not_in_plan_without_add_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install pkg1' with a package not in the plan without --add flag."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = False

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command with capturing SystemExit
        result = cli_runner.invoke(install_command, ["pkg1"], obj=mock_edpm_api)

    # Verify (exit code 1 is OK here since the code calls exit(1))
    assert result.exit_code == 1, "Should exit with error code when package not in plan"
    assert "not in plan" in result.output
    assert "Options:" in result.output

    # Should not call install_dependency_chain
    mock_edpm_api.install_dependency_chain.assert_not_called()


def test_install_package_not_in_plan_with_add_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install --add pkg1' with a package not in the plan."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = False

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--add", "pkg1"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"
    assert "Adding it automatically" in result.output

    # Should add package to plan
    mock_edpm_api.plan.add_package.assert_called_once_with("pkg1")
    mock_edpm_api.plan.save.assert_called_once_with(mock_edpm_api.plan_file)

    # Should call install_dependency_chain with a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1"],
        explain=False,
        force=False
    )


def test_install_multiple_packages_with_add_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install --add pkg1 pkg2' with some packages not in the plan."""
    # Setup mock API
    # pkg1 exists, pkg2 doesn't
    mock_edpm_api.plan.has_package.side_effect = lambda pkg: pkg == "pkg1"

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--add", "pkg1", "pkg2"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"
    assert "Adding it automatically" in result.output

    # Should check both packages
    assert mock_edpm_api.plan.has_package.call_count == 2

    # Should add only pkg2 to plan
    mock_edpm_api.plan.add_package.assert_called_once_with("pkg2")
    mock_edpm_api.plan.save.assert_called_once_with(mock_edpm_api.plan_file)

    # Should call install_dependency_chain with both packages as a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1", "pkg2"],
        explain=False,
        force=False
    )


def test_install_with_explain_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install --explain pkg1' which should not perform actual install."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = True

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--explain", "pkg1"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"

    # Should call install_dependency_chain with explain=True and a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1"],
        explain=True,
        force=False
    )

    # Should NOT call save_generator_scripts
    mock_edpm_api.save_generator_scripts.assert_not_called()


def test_install_with_force_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install --force pkg1' which should force reinstall."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = True

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--force", "pkg1"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"

    # Should call install_dependency_chain with force=True and a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1"],
        explain=False,
        force=True
    )


def test_install_with_top_dir_flag(mock_edpm_api, cli_runner):
    """Test 'edpm install --top-dir=/custom/path pkg1' which should set custom top directory."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = True

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--top-dir", "/custom/path", "pkg1"], obj=mock_edpm_api)

    # Verify
    assert result.exit_code == 0, f"Command failed with error: {result.output}"

    # Should set top_dir
    assert mock_edpm_api.top_dir == "/custom/path"

    # Then proceed with install with a list
    mock_edpm_api.install_dependency_chain.assert_called_once_with(
        dep_names=["pkg1"],
        explain=False,
        force=False
    )


def test_install_add_package_failure(mock_edpm_api, cli_runner):
    """Test when adding a package with --add flag fails."""
    # Setup mock API
    mock_edpm_api.plan.has_package.return_value = False
    mock_edpm_api.plan.add_package.side_effect = Exception("Failed to add package")

    # Make the instance check pass
    with patch('edpm.cli.install.isinstance', return_value=True):
        # Run the command
        result = cli_runner.invoke(install_command, ["--add", "pkg1"], obj=mock_edpm_api)

    # Verify (should fail with exit code 1)
    assert result.exit_code == 1, "Command should exit with error code on package add failure"
    assert "Failed to add" in result.output

    # Should try to add package
    mock_edpm_api.plan.add_package.assert_called_once_with("pkg1")

    # Should not proceed with install
    mock_edpm_api.install_dependency_chain.assert_not_called()