import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from ruamel.yaml import YAML

from edpm.engine.api import EdpmApi
from edpm.engine.recipe_manager import RecipeManager
from edpm.cli.req import req_command, gather_requirements


class TestRecipe:
    name = "test_recipe"

    os_dependencies = {
        'required': {
            'ubuntu': "test-lib-dev test-common",
            'centos': "test-lib-devel test-common"
        },
        'optional': {
            'ubuntu': "test-optional",
            'centos': "test-optional"
        }
    }


def test_gather_requirements():
    """Test the gathering of requirements from recipes and plan file."""

    # Mock the EdpmApi and RecipeManager
    api = MagicMock()
    api.recipe_manager = MagicMock()
    api.plan = MagicMock()

    # Create a test package in the plan
    test_pkg = MagicMock()
    test_pkg.name = "test"
    test_pkg.config = {
        "require": {
            "ubuntu": {
                "required": ["plan-required-pkg"],
                "optional": ["plan-optional-pkg"],
            }
        }
    }

    # Mock finding the package
    api.plan.find_package = MagicMock(return_value=test_pkg)

    # Mock the recipe
    api.recipe_manager.recipes_by_name = {
        "test": TestRecipe
    }

    # Test gathering requirements
    required, optional = gather_requirements(api, "ubuntu", ("test",))

    # Verify results
    assert "plan-required-pkg" in required
    assert "test-lib-dev" in required
    assert "test-common" in required

    assert "plan-optional-pkg" in optional
    assert "test-optional" in optional

    # Required packages shouldn't be in optional
    assert "test-lib-dev" not in optional


def test_gather_requirements_global():
    """Test gathering requirements with global requirements."""

    # Mock the EdpmApi and RecipeManager
    api = MagicMock()
    api.recipe_manager = MagicMock()
    api.plan = MagicMock()

    # Mock global requirements
    api.plan.global_config = MagicMock(return_value={
        "require": {
            "ubuntu": {
                "required": ["global-required-pkg"],
                "optional": ["global-optional-pkg"]
            }
        }
    })

    # Create a test package in the plan
    test_pkg = MagicMock()
    test_pkg.name = "test"
    test_pkg.config = {}

    # Mock finding the package
    api.plan.find_package.return_value = test_pkg

    # Mock the recipe with no dependencies
    api.recipe_manager.recipes_by_name = {}

    # Test gathering requirements
    required, optional = gather_requirements(api, "ubuntu", ("test",))

    # Verify results
    assert "global-required-pkg" in required
    assert "global-optional-pkg" in optional


def test_gather_requirements_with_list():
    """Test gathering requirements when they're given as a list instead of dict."""

    # Mock the EdpmApi and RecipeManager
    api = MagicMock()
    api.recipe_manager = MagicMock()
    api.plan = MagicMock()

    # Create a test package in the plan
    test_pkg = MagicMock()
    test_pkg.name = "test"
    test_pkg.config = {
        "require": {
            "ubuntu": ["list-pkg1", "list-pkg2"]
        }
    }

    # Mock finding the package
    api.plan.find_package = MagicMock(return_value=test_pkg)

    # Mock the recipe
    api.recipe_manager.recipes_by_name = {}

    # Test gathering requirements
    required, optional = gather_requirements(api, "ubuntu", ("test",))

    # Verify results
    assert "list-pkg1" in required
    assert "list-pkg2" in required
    assert not optional  # Should be empty