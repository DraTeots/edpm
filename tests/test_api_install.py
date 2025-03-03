import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from ruamel.yaml import YAML

from edpm.engine.api import EdpmApi
from edpm.engine.recipe import Recipe
from edpm.engine.config import ConfigNamespace

class TestRecipe(Recipe):
    """A test recipe that tracks method calls without doing real work."""

    def __init__(self, config=None):
        config = config or ConfigNamespace()
        super().__init__(config)
        self.calls = []

    def preconfigure(self):
        self.calls.append("preconfigure")
        # Set paths that would normally be set by use_common_dirs_scheme
        app_path = str(self.config.get("app_path", "/tmp"))
        self.config["install_path"] = os.path.join(app_path, "test-install")
        self.config["source_path"] = os.path.join(app_path, "test-source")
        self.config["build_path"] = os.path.join(app_path, "test-build")

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


def test_install_dependency():
    """Test that installing a dependency works correctly."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup plan and lock files
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")
        lock_path = os.path.join(tmpdir, "lock.edpm.yaml")

        # Create minimal plan file with a test package
        plan_data = {
            "global": {"config": {}},
            "packages": ["test"]
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
        test_recipe = TestRecipe(ConfigNamespace(app_path=tmpdir))

        # Patch external interactions
        with patch("edpm.engine.commands.run"), \
                patch("edpm.engine.commands.workdir"), \
                patch("edpm.engine.generators.environment_generator.EnvironmentGenerator.save_environment_with_infile"), \
                patch.object(api.recipe_manager, "create_recipe") as mock_create_recipe:

            # Make create_recipe return our test recipe
            mock_create_recipe.return_value = test_recipe

            # Load plan and lock
            api.load_all()

            # Run installation
            api.install_dependency_chain(dep_names=["test"], force=False)

            # Verify recipe methods were called in order
            assert test_recipe.calls == [
                "preconfigure", "fetch", "patch", "build", "install", "post_install"
            ]

            # Verify lock file was updated
            api.lock.load(lock_path)  # Reload to see saved changes
            assert "test" in api.lock.get_installed_packages()
            package_info = api.lock.get_installed_package("test")
            assert "install_path" in package_info
            assert package_info["install_path"] == os.path.join(tmpdir, "test-install")
            assert "built_with_config" in package_info


def test_install_already_installed():
    """Test installing a package that's already installed."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup plan and lock files
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")
        lock_path = os.path.join(tmpdir, "lock.edpm.yaml")

        # Create plan file
        plan_data = {
            "global": {"config": {}},
            "packages": ["test"]
        }
        yaml = YAML()
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f)

        # Create lock file with test package already installed
        install_path = os.path.join(tmpdir, "existing-install")
        os.makedirs(install_path, exist_ok=True)  # Create the directory so it exists

        lock_data = {
            "file_version": 1,
            "top_dir": tmpdir,
            "packages": {
                "test": {
                    "install_path": install_path,
                    "built_with_config": {"some_key": "some_value"}
                }
            }
        }
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f)

        # Initialize API
        api = EdpmApi(plan_file=plan_path, lock_file=lock_path)

        # Create test recipe
        test_recipe = TestRecipe(ConfigNamespace(app_path=tmpdir))

        # Patch external interactions
        with patch("edpm.engine.commands.run"), \
                patch("edpm.engine.commands.workdir"), \
                patch("edpm.engine.generators.environment_generator.EnvironmentGenerator.save_environment_with_infile"), \
                patch.object(api.recipe_manager, "create_recipe") as mock_create_recipe:

            # Setup the mock
            mock_create_recipe.return_value = test_recipe

            # Load plan and lock
            api.load_all()

            # Run installation - shouldn't actually do anything since it's already installed
            api.install_dependency_chain(dep_names=["test"], force=False)

            # Verify recipe was not used (no methods called)
            assert not test_recipe.calls

            # Verify lock file still has the original data
            api.lock.load(lock_path)
            assert "test" in api.lock.get_installed_packages()
            package_info = api.lock.get_installed_package("test")
            assert package_info["install_path"] == install_path
            assert package_info["built_with_config"] == {"some_key": "some_value"}


def test_install_with_force():
    """Test that force=True reinstalls even if already installed."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup plan and lock files
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")
        lock_path = os.path.join(tmpdir, "lock.edpm.yaml")

        # Create plan file
        plan_data = {
            "global": {"config": {}},
            "packages": ["test"]
        }
        yaml = YAML()
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f)

        # Create lock file with test package already installed
        install_path = os.path.join(tmpdir, "existing-install")
        os.makedirs(install_path, exist_ok=True)

        lock_data = {
            "file_version": 1,
            "top_dir": tmpdir,
            "packages": {
                "test": {
                    "install_path": install_path,
                    "built_with_config": {"some_key": "original_value"}
                }
            }
        }
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f)

        # Initialize API
        api = EdpmApi(plan_file=plan_path, lock_file=lock_path)

        # Create test recipe
        test_recipe = TestRecipe(ConfigNamespace(app_path=tmpdir))

        # Patch external interactions
        with patch("edpm.engine.commands.run"), \
                patch("edpm.engine.commands.workdir"), \
                patch("edpm.engine.generators.environment_generator.EnvironmentGenerator.save_environment_with_infile"), \
                patch.object(api.recipe_manager, "create_recipe") as mock_create_recipe:

            # Setup mock to return our test recipe
            mock_create_recipe.return_value = test_recipe

            # Load plan and lock
            api.load_all()

            # Run installation with force=True to trigger reinstall
            api.install_dependency_chain(dep_names=["test"], force=True)

            # Verify recipe methods were called (force reinstall should use the recipe)
            assert test_recipe.calls == [
                "preconfigure", "fetch", "patch", "build", "install", "post_install"
            ]

            # Verify lock file was updated with new paths
            api.lock.load(lock_path)
            assert "test" in api.lock.get_installed_packages()
            package_info = api.lock.get_installed_package("test")
            assert package_info["install_path"] == os.path.join(tmpdir, "test-install")
            assert "built_with_config" in package_info
            # Original values should be replaced
            assert package_info["built_with_config"].get("some_key") != "original_value"