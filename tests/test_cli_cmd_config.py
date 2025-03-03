# tests/test_cli_cmd_config.py
import pytest
from click.testing import CliRunner
import click
from ruamel.yaml import YAML
import os

# Import your actual config command
from edpm.cli.config import config as config_command
# And the EdpmApi
from edpm.engine.api import EdpmApi

@click.group()
@click.pass_context
def cli(ctx):
    pass

# Add the config command
cli.add_command(config_command, "config")

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_plan(tmp_path):
    """
    Creates a minimal plan.edpm.yaml with an empty 'packages' list
    and an empty global config. Then instantiates an EdpmApi
    pointing to it, calling load_all() so 'api.plan' is not None.
    """
    plan_path = tmp_path / "plan.edpm.yaml"
    lock_path = tmp_path / "plan-lock.edpm.yaml"

    # Minimal plan
    initial_plan = {
        "global": {
            "config": {}
        },
        "packages": []
    }
    yaml = YAML()
    with plan_path.open("w", encoding="utf-8") as f:
        yaml.dump(initial_plan, f)

    # Create the EdpmApi
    api = EdpmApi(plan_file=str(plan_path), lock_file=str(lock_path))
    api.load_all()  # Ensures api.plan is now a valid PlanFile object

    return api, plan_path, lock_path

@pytest.mark.usefixtures("temp_plan")
def test_show_global_config(runner, temp_plan):
    api, plan_path, lock_path = temp_plan
    # No arguments => show global config
    result = runner.invoke(cli, ["config"], obj=api)
    assert result.exit_code == 0
    assert "Global Config" in result.output
    assert "No global config found" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_set_global_config(runner, temp_plan):
    api, plan_path, _ = temp_plan
    result = runner.invoke(cli, ["config", "build_threads=4", "cxx_standard=17"], obj=api)
    assert result.exit_code == 0
    assert "Updated global config" in result.output
    assert "build_threads = 4" in result.output
    assert "cxx_standard = 17" in result.output
    assert "Saved changes to" in result.output

    # Reload from disk
    api.load_all()
    glob_cfg = api.plan.data["global"]["config"]
    assert glob_cfg["build_threads"] == "4"
    assert glob_cfg["cxx_standard"] == "17"

@pytest.mark.usefixtures("temp_plan")
def test_show_dep_not_found(runner, temp_plan):
    api, _, _ = temp_plan
    result = runner.invoke(cli, ["config", "fakeDep"], obj=api)
    assert result.exit_code == 0
    assert "No dependency named 'fakeDep' in the plan" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_create_new_dep(runner, temp_plan):
    api, plan_path, _ = temp_plan
    # Provide 'recipe=git'
    result = runner.invoke(cli, ["config", "mydep", "recipe=git", "url=https://some.git"], obj=api)
    assert result.exit_code == 0
    assert "Updated config for mydep" in result.output
    assert "recipe = git" in result.output
    assert "url = https://some.git" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_create_new_dep_no_recipe(runner, temp_plan):
    """
    The code should produce an error if user tries to create a
    brand-new dependency but does NOT specify recipe=...
    """
    api, _, _ = temp_plan
    result = runner.invoke(cli, ["config", "unicorn", "branch=magic"], obj=api)
    assert result.exit_code == 0
    # Should show the error (per the test expectation).
    assert "No dependency named 'unicorn' in the plan, and no 'recipe=...' provided" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_convert_string_dep_to_dict(runner, temp_plan):
    """
    If packages: ["root"] and we do 'edpm config root branch=main',
    we convert "root" => { "root": { recipe: "root", branch: "main" } }
    """
    api, plan_path, _ = temp_plan

    # Manually store packages: ["root"]
    api.plan.data["packages"] = ["root"]
    api.plan.save(api.plan_file)

    result = runner.invoke(cli, ["config", "root", "branch=main"], obj=api)
    assert result.exit_code == 0
    assert "convert 'root' to dict" not in result.output  # optional
    assert "Updated config for root" in result.output
    # The code should mention "recipe = root" as well
    assert "recipe = root" in result.output
    assert "branch = main" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_show_dep_dict(runner, temp_plan):
    api, plan_path, _ = temp_plan
    # Insert a dictionary-based dep
    api.plan.data["packages"] = [
        {"foo": {"recipe": "git", "branch": "dev"}}
    ]
    api.plan.save(api.plan_file)

    result = runner.invoke(cli, ["config", "foo"], obj=api)
    assert result.exit_code == 0
    assert "foo config:" in result.output
    assert "recipe: git" in result.output
    assert "branch: dev" in result.output

@pytest.mark.usefixtures("temp_plan")
def test_update_existing_dep(runner, temp_plan):
    api, plan_path, _ = temp_plan
    # Already have {"mylib": {"recipe": "git", "url": "old"}}
    api.plan.data["packages"] = [
        {"mylib": {"recipe": "git", "url": "https://old.git"}}
    ]
    api.plan.save(api.plan_file)

    result = runner.invoke(cli, ["config", "mylib", "url=https://new.git", "branch=featureX"], obj=api)
    assert result.exit_code == 0
    assert "Updated config for mylib" in result.output
    assert "url = https://new.git" in result.output
    assert "branch = featureX" in result.output

    # Confirm it's saved
    api.load_all()
    pkgs = api.plan.data["packages"]
    dep_dict = pkgs[0]["mylib"]
    assert dep_dict["recipe"] == "git"
    assert dep_dict["url"] == "https://new.git"
    assert dep_dict["branch"] == "featureX"
