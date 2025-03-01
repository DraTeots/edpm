import click
import os

from edpm.engine.api import EdpmApi
from edpm.engine.commands import run
from edpm.engine.output import markup_print as mprint


@click.command("clean", help="Remove installed data for a package from disk (if EDPM owns it).")
@click.argument("dep_name", required=True)
@click.pass_context
def clean_command(ctx, dep_name):
    """
    Usage:
        edpm clean <dep-name>

    This command removes the source/build/install directories from disk if they
    exist and if EDPM owns the package. It also updates the lock file and regenerates
    the environment scripts.
    """
    api = ctx.obj
    assert isinstance(api, EdpmApi), "EdpmApi context not available."

    # Ensure plan & lock loaded
    api.load_all()  # loads plan & lock files

    # Check if dependency is in the lock file
    dep_data = api.lock.get_dependency(dep_name)
    if not dep_data:
        mprint("<red>Error:</red> No installation info found for '{}'. Not in lock file.", dep_name)
        raise click.Abort()

    # The typical key is "install_path". If it’s empty, presumably not installed.
    install_path = dep_data.get("install_path", "")
    if not install_path or not os.path.isdir(install_path):
        mprint("<red>Error:</red> '{}' is not currently installed (lock file has no valid install_path).", dep_name)
        raise click.Abort()

    # If you store ownership as "owned": true/false in the lock, check it:
    # (Or rename the key to 'is_owned' if your system differs.)
    is_owned = dep_data.get("owned", True)  # default to True if absent
    if not is_owned:
        mprint("<yellow>Note:</yellow> '{}' is not owned by EDPM. You must remove it manually:\n  {}",
               dep_name, install_path)
        return

    # Print some info for user
    mprint("<blue>Cleaning install of '{}' at:</blue>\n  {}", dep_name, install_path)

    # Remove the disk directories if listed in the lock
    # Common fields might be "source_path", "build_path", "install_path"
    removed_any = False
    for path_key in ["source_path", "build_path", "install_path"]:
        path_val = dep_data.get(path_key, "")
        if path_val and os.path.isdir(path_val):
            mprint("Removing <magenta>{}</magenta> ...", path_val)
            run(f'rm -rf "{path_val}"')
            removed_any = True
        # Clear it in the lock data
        dep_data[path_key] = ""

    if not removed_any:
        mprint("No directories found on disk to remove (maybe partially cleaned already).")

    # Overwrite the lock data (removing the paths but still leaving the recipe config).
    api.lock.update_dependency(dep_name, dep_data)
    api.lock.save()

    # Regenerate environment scripts for bash & csh
    mprint("\nRebuilding environment scripts...\n")
    api.save_shell_environment(shell="bash")
    api.save_shell_environment(shell="csh")

    mprint("<green>Done!</green> '{}' has been cleaned.\n", dep_name)
