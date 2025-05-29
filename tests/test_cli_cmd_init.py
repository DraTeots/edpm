import os
import pytest
from click.testing import CliRunner
import click
from unittest.mock import patch, MagicMock
from ruamel.yaml import YAML

from edpm.cli.init import init_command, get_templates_dir, list_available_templates, load_template_content
from edpm.engine.api import EdpmApi


@click.group()
@click.pass_context
def cli(ctx):
    pass


cli.add_command(init_command, "init")


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_api(tmp_path):
    """Create a minimal EdpmApi for testing."""
    plan_path = tmp_path / "plan.edpm.yaml"
    lock_path = tmp_path / "plan-lock.edpm.yaml"
    api = EdpmApi(plan_file=str(plan_path), lock_file=str(lock_path))
    return api


@pytest.fixture
def mock_templates_dir(tmp_path):
    """Create a mock templates directory with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create default template
    default_content = """# Default Template
global:
  config:
    cxx_standard: 17

packages:
  - root
"""
    (templates_dir / "default-plan.edpm.yaml").write_text(default_content)

    # Create EIC template
    eic_content = """# EIC Template
global:
  config:
    cxx_standard: 17

packages:
  - root
  - geant4
  - eicrecon
"""
    (templates_dir / "eic-plan.edpm.yaml").write_text(eic_content)

    # Create TDIS template
    tdis_content = """# TDIS Template  
global:
  config:
    cxx_standard: 17

packages:
  - root
  - geant4
  - jana2
"""
    (templates_dir / "tdis-plan.edpm.yaml").write_text(tdis_content)

    return str(templates_dir)


def test_list_templates_command(runner, mock_api, mock_templates_dir):
    """Test the --list-templates option."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "--list-templates"], obj=mock_api)
        assert result.exit_code == 0
        assert "Available templates:" in result.output
        assert "default" in result.output
        assert "eic" in result.output
        assert "tdis" in result.output


def test_init_default_template(runner, mock_api, mock_templates_dir):
    """Test initializing with default template."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init"], obj=mock_api)
        assert result.exit_code == 0
        assert "Using template: default" in result.output
        assert "Created EDPM plan:" in result.output

        # Check that the file was created with default content
        plan_path = mock_api.plan_file
        assert os.path.exists(plan_path)

        with open(plan_path, 'r') as f:
            content = f.read()
        assert "Default Template" in content
        assert "- root" in content


def test_init_eic_template(runner, mock_api, mock_templates_dir):
    """Test initializing with EIC template."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "-t", "eic"], obj=mock_api)
        assert result.exit_code == 0
        assert "Using template: eic" in result.output
        assert "Created EDPM plan:" in result.output

        # Check that the file was created with EIC content
        plan_path = mock_api.plan_file
        assert os.path.exists(plan_path)

        with open(plan_path, 'r') as f:
            content = f.read()
        assert "EIC Template" in content
        assert "- eicrecon" in content


def test_init_tdis_template(runner, mock_api, mock_templates_dir):
    """Test initializing with TDIS template."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "--template", "tdis"], obj=mock_api)
        assert result.exit_code == 0
        assert "Using template: tdis" in result.output
        assert "Created EDPM plan:" in result.output

        # Check that the file was created with TDIS content
        plan_path = mock_api.plan_file
        assert os.path.exists(plan_path)

        with open(plan_path, 'r') as f:
            content = f.read()
        assert "TDIS Template" in content
        assert "- jana2" in content


def test_init_nonexistent_template(runner, mock_api, mock_templates_dir):
    """Test error when requesting non-existent template."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "-t", "nonexistent"], obj=mock_api)
        assert result.exit_code == 0  # Function doesn't exit with error code, just prints error
        assert "Template 'nonexistent' not found" in result.output
        assert "Available templates: default, eic, tdis" in result.output


def test_init_force_overwrite(runner, mock_api, mock_templates_dir):
    """Test that --force overwrites existing files."""
    plan_path = mock_api.plan_file

    # Create existing file
    with open(plan_path, 'w') as f:
        f.write("existing content")

    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "-t", "eic", "--force"], obj=mock_api)
        assert result.exit_code == 0
        assert "Using template: eic" in result.output
        assert "Created EDPM plan:" in result.output

        # Check that the file was overwritten
        with open(plan_path, 'r') as f:
            content = f.read()
        assert "existing content" not in content
        assert "EIC Template" in content


def test_init_no_force_existing_file(runner, mock_api, mock_templates_dir):
    """Test that existing files are not overwritten without --force."""
    plan_path = mock_api.plan_file

    # Create existing file
    with open(plan_path, 'w') as f:
        f.write("existing content")

    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        result = runner.invoke(cli, ["init", "-t", "eic"], obj=mock_api)
        assert result.exit_code == 0
        assert "already exists" in result.output
        assert "Use --force to overwrite" in result.output

        # Check that the file was NOT overwritten
        with open(plan_path, 'r') as f:
            content = f.read()
        assert content == "existing content"


def test_templates_directory_functions(mock_templates_dir):
    """Test the helper functions for template management."""
    with patch('edpm.cli.init.get_templates_dir', return_value=mock_templates_dir):
        # Test list_available_templates
        templates = list_available_templates()
        assert templates == ["default", "eic", "tdis"]

        # Test load_template_content
        default_content = load_template_content("default")
        assert "Default Template" in default_content

        eic_content = load_template_content("eic")
        assert "EIC Template" in eic_content

        # Test loading non-existent template
        with pytest.raises(FileNotFoundError):
            load_template_content("nonexistent")


def test_no_templates_directory(runner, mock_api):
    """Test behavior when templates directory doesn't exist."""
    with patch('edpm.cli.init.get_templates_dir', return_value=None):
        # Test list templates
        result = runner.invoke(cli, ["init", "--list-templates"], obj=mock_api)
        assert result.exit_code == 0
        assert "No templates found" in result.output

        # Test init with template
        result = runner.invoke(cli, ["init", "-t", "eic"], obj=mock_api)
        assert result.exit_code == 0
        assert "Templates directory not found" in result.output