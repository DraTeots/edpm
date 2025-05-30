# tests/test_install_version_override.py
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from ruamel.yaml import YAML

from edpm.cli.install import install_command
from edpm.engine.api import EdpmApi
from edpm.engine.recipe import Recipe
from edpm.engine.config import ConfigNamespace
from edpm.engine.fetchers import GitFetcher
import click


@click.group()
@click.pass_context
def cli(ctx):
    pass


cli.add_command(install_command)


class TestVersionRecipe(Recipe):
    """A test recipe that captures the final config for verification."""

    def __init__(self, config=None):
        # Simulate a recipe with default version (like fmt recipe)
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/test/test.git',
            'branch': 'v1.0.0'  # Default version with 'v' prefix
        }
        super().__init__(config)
        self.final_config = dict(self.config)
        self.calls = []

    def preconfigure(self):
        self.calls.append("preconfigure")
        # Simulate GitFetcher.preconfigure() behavior
        version = self.config.get("version", "")
        branch = self.config.get("branch", "")
        if version:
            if branch:
                print(f"'version'='{version}' is explicitly set and overrides 'branch'='{branch}'")
            self.config["branch"] = version

        # Set paths
        app_path = str(self.config.get("app_path", "/tmp"))
        self.config["install_path"] = os.path.join(app_path, "test-install")
        self.config["source_path"] = os.path.join(app_path, "test-source")
        self.config["build_path"] = os.path.join(app_path, "test-build")

        # Store final config after version override
        self.final_config = dict(self.config)

    def fetch(self):
        self.calls.append("fetch")

    def patch(self):
        self.calls.append("patch")

    def build(self):
        self.calls.append("build")

    def install(self):
        self.calls.append("install")

    def post_install(self):
        self.calls.append("post_install")


@pytest.fixture
def runner():
    return CliRunner()


def test_install_with_add_flag_preserves_user_version():
    """
    Test that when user specifies 'edpm install -a package@version',
    the user-specified version overrides the recipe's default version.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup plan and lock files
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")
        lock_path = os.path.join(tmpdir, "lock.edpm.yaml")

        # Create minimal plan file (initially empty packages)
        plan_data = {
            "global": {"config": {}},
            "packages": []
        }
        yaml = YAML()
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f)

        # Create minimal lock file
        lock_data = {
            "file_version": 1,
            "top_dir": tmpdir,
            "packages": {}
        }
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f)

        # Initialize API
        api = EdpmApi(plan_file=plan_path, lock_file=lock_path)

        # Create test recipe
        test_recipe = TestVersionRecipe(ConfigNamespace(app_path=tmpdir))

        # Create runner
        runner = CliRunner()

        # Patch external interactions
        with patch("edpm.engine.commands.run"), \
                patch("edpm.engine.commands.workdir"), \
                patch("edpm.engine.generators.environment_generator.EnvironmentGenerator.save_environment_with_infile"), \
                patch.object(api.recipe_manager, "create_recipe") as mock_create_recipe:
            # Make create_recipe return our test recipe
            mock_create_recipe.return_value = test_recipe

            # Run installation with --add flag and version specification
            result = runner.invoke(cli, ["install", "--add", "testpkg@2.5.0"], obj=api)

            # Verify command succeeded
            assert result.exit_code == 0, f"Command failed: {result.output}"
            assert "Adding it automatically" in result.output
            assert "Added 'testpkg@2.5.0' to the plan" in result.output

            # Verify recipe was called
            assert test_recipe.calls == [
                "preconfigure", "fetch", "patch", "build", "install", "post_install"
            ]

            # THE KEY TEST: Verify that user version (2.5.0) overrode default version (v1.0.0)
            assert test_recipe.final_config["branch"] == "2.5.0", \
                f"Expected branch to be user version '2.5.0', but got '{test_recipe.final_config.get('branch')}'"

            # Verify the version field was set correctly
            assert test_recipe.final_config["version"] == "2.5.0", \
                f"Expected version to be '2.5.0', but got '{test_recipe.final_config.get('version')}'"

            # Verify plan file was updated correctly
            api.load_all()  # Reload to see saved changes
            packages = api.plan.packages()
            assert len(packages) == 1
            pkg = packages[0]
            assert pkg.name == "testpkg"
            assert pkg.config["version"] == "2.5.0"

            # Verify lock file was updated
            package_info = api.lock.get_installed_package("testpkg")
            assert "install_path" in package_info
            built_config = package_info["built_with_config"]
            assert built_config["branch"] == "2.5.0"  # User version should be in final config
            assert built_config["version"] == "2.5.0"


def test_install_default_version_when_no_version_specified():
    """
    Test that when user specifies 'edpm install -a package' (no version),
    the recipe's default version is used.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup plan and lock files
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")
        lock_path = os.path.join(tmpdir, "lock.edpm.yaml")

        # Create minimal plan file (initially empty packages)
        plan_data = {
            "global": {"config": {}},
            "packages": []
        }
        yaml = YAML()
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f)

        # Create minimal lock file
        lock_data = {
            "file_version": 1,
            "top_dir": tmpdir,
            "packages": {}
        }
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f)

        # Initialize API
        api = EdpmApi(plan_file=plan_path, lock_file=lock_path)

        # Create test recipe
        test_recipe = TestVersionRecipe(ConfigNamespace(app_path=tmpdir))

        # Create runner
        runner = CliRunner()

        # Patch external interactions
        with patch("edpm.engine.commands.run"), \
                patch("edpm.engine.commands.workdir"), \
                patch("edpm.engine.generators.environment_generator.EnvironmentGenerator.save_environment_with_infile"), \
                patch.object(api.recipe_manager, "create_recipe") as mock_create_recipe:
            # Make create_recipe return our test recipe
            mock_create_recipe.return_value = test_recipe

            # Run installation with --add flag but NO version specification
            result = runner.invoke(cli, ["install", "--add", "testpkg"], obj=api)

            # Verify command succeeded
            assert result.exit_code == 0, f"Command failed: {result.output}"

            # THE KEY TEST: Verify that default version (v1.0.0) was used since no user version was specified
            assert test_recipe.final_config["branch"] == "v1.0.0", \
                f"Expected branch to be default version 'v1.0.0', but got '{test_recipe.final_config.get('branch')}'"

            # No version field should be set (since user didn't specify one)
            assert "version" not in test_recipe.final_config or test_recipe.final_config["version"] == "", \
                f"Expected no version field, but got '{test_recipe.final_config.get('version')}'"


def test_git_fetcher_version_override():
    """
    Test that GitFetcher.preconfigure() correctly handles version override.
    """
    # Test config with both default branch and user version
    config = {
        "branch": "v1.0.0",  # Default from recipe
        "version": "2.5.0",  # User specified
        "url": "https://github.com/test/test.git",
        "source_path": "/tmp/test"
    }

    fetcher = GitFetcher(config)

    # Call preconfigure to trigger version override logic
    fetcher.preconfigure()

    # Verify that user version overrode default branch
    assert fetcher.config["branch"] == "2.5.0", \
        f"Expected branch to be overridden to '2.5.0', but got '{fetcher.config['branch']}'"

    # Verify clone command uses correct version
    clone_cmd = fetcher.config["clone_command"]
    assert "-b 2.5.0" in clone_cmd, \
        f"Expected clone command to use '-b 2.5.0', but got: {clone_cmd}"


def test_git_fetcher_no_version_override():
    """
    Test that GitFetcher.preconfigure() preserves default branch when no version is specified.
    """
    # Test config with only default branch, no user version
    config = {
        "branch": "v1.0.0",  # Default from recipe
        "url": "https://github.com/test/test.git",
        "source_path": "/tmp/test"
    }

    fetcher = GitFetcher(config)

    # Call preconfigure
    fetcher.preconfigure()

    # Verify that default branch was preserved
    assert fetcher.config["branch"] == "v1.0.0", \
        f"Expected branch to remain 'v1.0.0', but got '{fetcher.config['branch']}'"

    # Verify clone command uses default branch
    clone_cmd = fetcher.config["clone_command"]
    assert "-b v1.0.0" in clone_cmd, \
        f"Expected clone command to use '-b v1.0.0', but got: {clone_cmd}"