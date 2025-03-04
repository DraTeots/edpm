import os
import pytest
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from edpm.cli.clean import clean_command
from edpm.engine.api import EdpmApi
from edpm.engine.lockfile import LockfileConfig
import click

@click.group()
@click.pass_context
def cli(ctx):
    pass

cli.add_command(clean_command)

@pytest.fixture
def runner():
    return CliRunner()

import os
import pytest
from edpm.engine.api import EdpmApi
from edpm.engine.planfile import PlanFile
from edpm.engine.lockfile import LockfileConfig
from ruamel.yaml import YAML

@pytest.fixture
def mock_api(tmp_path):
    """
    Creates minimal plan + lock files on disk so 'api.load_all()' doesn't fail.
    Also sets up an 'installed' package named 'mypkg'.
    """
    plan_path = tmp_path / "plan.edpm.yaml"
    lock_path = tmp_path / "plan-lock.edpm.yaml"

    # Write a minimal plan file
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

    # Mock a lock file in memory
    lock = LockfileConfig()
    lock.file_path = str(lock_path)
    lock.data = {
        "top_dir": str(tmp_path),
        "packages": {
            "mypkg": {
                "install_path": str(tmp_path / "mypkg_install"),
                "built_with_config": {
                    "build_path": str(tmp_path / "mypkg_build"),
                    "source_path": str(tmp_path / "mypkg_src")
                },
                "owned": True
            }
        }
    }
    api.lock = lock

    # Create physical directories so isdir() sees them
    os.makedirs(tmp_path / "mypkg_install", exist_ok=True)
    os.makedirs(tmp_path / "mypkg_build", exist_ok=True)
    os.makedirs(tmp_path / "mypkg_src", exist_ok=True)

    return api

def test_clean_success(runner, mock_api):
    """
    Test that clean_command removes 'mypkg' directories from disk when owned = True.
    We mock shutil.rmtree to confirm it's called with the correct directories.
    """
    # 1) Capture directories from the lock before calling 'clean'
    mypkg_data = mock_api.lock.data["packages"]["mypkg"]
    install_dir = mypkg_data["install_path"]
    build_dir   = mypkg_data["built_with_config"]["build_path"]
    source_dir  = mypkg_data["built_with_config"]["source_path"]

    with patch.object(shutil, 'rmtree', side_effect=MagicMock()) as mock_rmtree, \
            patch.object(mock_api.lock, 'save', side_effect=MagicMock()) as mock_lock_save, \
            patch.object(mock_api, 'save_generator_scripts', side_effect=MagicMock()) as mock_save_gens:

        # 2) Invoke the command
        result = runner.invoke(cli, ["clean", "mypkg"], obj=mock_api)
        assert result.exit_code == 0
        assert "Cleaned 'mypkg' installation" in result.output

        # 3) Verify the calls
        # We expect rmtree calls for install_dir, build_dir, source_dir
        calls = [call.args[0] for call in mock_rmtree.call_args_list]
        assert install_dir in calls
        assert build_dir in calls
        assert source_dir in calls

        mock_lock_save.assert_called_once()
        mock_save_gens.assert_called_once()

def test_clean_missing_install(runner, mock_api):
    """
    If the install_path is empty or the folder is missing, we show an error but do not rmtree anything.
    """
    # remove the install directory
    install_dir = mock_api.lock.data["packages"]["mypkg"]["install_path"]
    shutil.rmtree(install_dir)  # physically remove it

    with patch.object(shutil, 'rmtree', side_effect=MagicMock()) as mock_rmtree:
        result = runner.invoke(cli, ["clean", "mypkg"], obj=mock_api)
        assert result.exit_code == 0
        assert "not currently installed" in result.output
        mock_rmtree.assert_not_called()

def test_clean_not_in_lock(runner, mock_api):
    """
    If user tries to clean a package that isn't in the lock file.
    """
    result = runner.invoke(cli, ["clean", "someOtherPkg"], obj=mock_api)
    assert result.exit_code != 0
    assert "No installation info found for 'someOtherPkg'" in result.output

def test_clean_not_owned(runner, mock_api):
    """
    If is_owned=False, we skip removing from disk, just warn user.
    """
    mock_api.lock.data["packages"]["mypkg"]["owned"] = False
    with patch.object(shutil, 'rmtree', side_effect=MagicMock()) as mock_rmtree:
        result = runner.invoke(cli, ["clean", "mypkg"], obj=mock_api)
        assert result.exit_code == 0
        assert "is not owned by EDPM. Remove manually" in result.output
        mock_rmtree.assert_not_called()
