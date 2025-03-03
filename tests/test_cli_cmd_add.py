# tests/test_cli_cmd_add.py
import os
import json
import pytest
from click.testing import CliRunner
import click

from edpm.cli.add import add_command
from edpm.engine.api import EdpmApi
from edpm.engine.planfile import PlanFile
from ruamel.yaml import YAML

# Create a test CLI that includes only the 'add' command.
@click.group()
@click.pass_context
def cli(ctx):
    pass

cli.add_command(add_command, "add")


@pytest.fixture
def runner():
    """Provides a Click CliRunner for capturing output."""
    return CliRunner()


@pytest.fixture
def temp_plan(tmp_path):
    """
    Creates a minimal plan.edpm.yaml file and a matching EdpmApi that references it.
    We do the same with a lock file.
    Returns (api, plan_path, lock_path).
    """
    plan_path = tmp_path / "plan.edpm.yaml"
    lock_path = tmp_path / "plan-lock.edpm.yaml"

    # minimal plan data
    minimal_plan = {
        "global": {
            "config": {},
            "environment": []
        },
        "packages": []
    }
    yaml = YAML()
    with plan_path.open("w", encoding="utf-8") as f:
        yaml.dump(minimal_plan, f)

    # Create an EdpmApi that references those files
    api = EdpmApi(plan_file=str(plan_path), lock_file=str(lock_path))
    # We won't write the lock file for now, but you could create a minimal lock if needed.
    return api, plan_path, lock_path


@pytest.fixture
def mock_recipe_manager(monkeypatch):
    """
    Patch EdpmApi's recipe_manager to simulate known recipes.
    Suppose 'root' and 'geant4' are recognized, everything else is unknown.
    """
    from edpm.engine.recipe_manager import RecipeManager
    class MockRecipeManager(RecipeManager):
        def __init__(self):
            super().__init__()
            self.recipes_by_name = {
                "root": lambda: None,   # We won't use real classes, just placeholders
                "geant4": lambda: None
            }
    def mock_load_installers(self, modules_dir=None, package_name="edpm.recipes"):
        self.recipes_by_name = {
            "root": None,
            "geant4": None
        }

    monkeypatch.setattr(RecipeManager, "__init__", MockRecipeManager.__init__)
    monkeypatch.setattr(RecipeManager, "load_installers", mock_load_installers)


def test_add_simple_known_recipe(runner, temp_plan, mock_recipe_manager):
    """
    If user does 'edpm add root' with no flags, we expect packages: ["root"] in the plan.
    """
    api, plan_path, _ = temp_plan

    # Load once so the plan is not None. Then set the mock recipe manager
    api.load_all()

    # Run: edpm add root
    result = runner.invoke(cli, ["add", "root"], obj=api)
    assert result.exit_code == 0
    assert "Added dependency 'root' to the plan." in result.output

    # Verify the plan
    with open(plan_path, "r", encoding="utf-8") as f:
        data = YAML().load(f)
    packages = data["packages"]
    assert len(packages) == 1
    assert packages[0] == "root"


def test_add_known_recipe_with_version(runner, temp_plan, mock_recipe_manager):
    """
    e.g. 'edpm add root@v6.32.0' => packages: ["root@v6.32.0"]
    """
    api, plan_path, _ = temp_plan
    api.load_all()

    result = runner.invoke(cli, ["add", "root@v6.32.0"], obj=api)
    assert result.exit_code == 0
    # check output
    assert "Added dependency 'root@v6.32.0' to the plan." in result.output

    # verify plan
    with open(plan_path, "r", encoding="utf-8") as f:
        data = YAML().load(f)
    pkgs = data["packages"]
    assert pkgs == ["root@v6.32.0"]


def test_add_known_recipe_with_flags(runner, temp_plan, mock_recipe_manager):
    """
    If user does 'edpm add root@v6.32.0 --fetch=git', it should produce a dict:
      - root:
          version: v6.32.0
          fetch: git
    """
    api, plan_path, _ = temp_plan
    api.load_all()

    result = runner.invoke(cli, ["add", "root@v6.32.0", "--fetch=git"], obj=api)
    assert result.exit_code == 0
    assert "Added dependency 'root@v6.32.0' to the plan." in result.output

    # parse the plan
    with open(plan_path, "r", encoding="utf-8") as f:
        data = YAML().load(f)
    pkgs = data["packages"]
    assert len(pkgs) == 1
