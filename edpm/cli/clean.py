import click
import os
import shutil

from edpm.engine.api import EdpmApi
from edpm.engine.commands import run
from edpm.engine.output import markup_print as mprint


@click.command("clean", help="Remove installed data for a package from disk (if EDPM owns it).")
@click.argument("dep_name", required=True)
@click.pass_context
def clean_command(ctx, dep_name):
    """Removes package installation and updates lock file"""
    api = ctx.obj
    assert isinstance(api, EdpmApi), "EdpmApi context not available."
    api.load_all()  # Ensure plan & lock are loaded

    # Get dependency data from lock file
    dep_data = api.lock.get_installed_package(dep_name)
    if not dep_data:
        mprint("<red>Error:</red> No installation info found for '{}'. Not in lock file.", dep_name)
        raise click.Abort()

    # Get installation metadata
    install_path = dep_data.get("install_path", "")
    config = dep_data.get("built_with_config", {})
    is_owned = dep_data.get("owned", True)

    # Validate installation exists
    if not install_path or not os.path.isdir(install_path):
        mprint("<red>Error:</red> '{}' is not currently installed.", dep_name)
        raise click.Abort()

    # Check ownership
    if not is_owned:
        mprint("<yellow>Note:</yellow> '{}' is not owned by EDPM. Remove manually:\n  {}", dep_name, install_path)
        return

    # Cleanup directories
    dirs_to_remove = [
        config.get("source_path", ""),
        config.get("build_path", ""),
        install_path
    ]

    removed = False
    for path in filter(None, dirs_to_remove):
        if os.path.exists(path):
            mprint("Removing <magenta>{}</magenta>...", path)
            shutil.rmtree(path, ignore_errors=True)
            removed = True

    if not removed:
        mprint("No installation directories found for '{}'", dep_name)
        return

    # Update lock file
    api.lock.update_package(dep_name, {
        "install_path": "",
        "built_with_config": {}
    })
    api.lock.save()

    # Regenerate environment
    mprint("\nRebuilding environment scripts...")
    api.save_shell_environment(shell="bash")
    api.save_shell_environment(shell="csh")

    mprint("<green>Success:</green> Cleaned '{}' installation", dep_name)