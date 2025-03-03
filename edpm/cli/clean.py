import os
import shutil

import click
from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint


@click.command("clean", help="Remove installed data for a package from disk (if EDPM owns it).")
@click.argument("dep_name", required=True)
@click.pass_context
def clean_command(ctx, dep_name):
    """
    Removes the installed data for DEP_NAME from disk if EDPM 'owns' it.
    Then clears out the lock file's 'install_path', etc.
    """
    api: EdpmApi = ctx.obj
    api.load_all()  # Ensure plan & lock are loaded

    # 1) Check if the package is installed in the lock
    install_data = api.lock.get_installed_package(dep_name)
    if not install_data:
        mprint("<red>Error:</red> No installation info found for '{}'. Not in lock file.", dep_name)
        raise click.Abort()

    install_path = install_data.get("install_path", "")
    config = install_data.get("built_with_config", {})
    is_owned = install_data.get("owned", True)  # or however you mark "ownership"

    # 2) If no valid install_path or the directory doesn't exist => can't clean
    if not install_path or not os.path.isdir(install_path):
        mprint("<red>Error:</red> '{}' is not currently installed (or directory missing).", dep_name)
        if not is_owned:
            mprint("<yellow>Note:</yellow> '{}' is not owned by EDPM. Remove manually:\n  {}", dep_name, install_path)
        else:
            mprint("<yellow>Nothing to clean on disk for '{}'.</yellow>", dep_name)
        return

    # 3) If EDPM owns it, remove the directories: install_path, build_path, source_path, etc.
    if is_owned:
        dirs_to_remove = [
            install_path,
            config.get("build_path", ""),
            config.get("source_path", "")
        ]
        for path in dirs_to_remove:
            if path and os.path.isdir(path):
                mprint("Removing <magenta>{}</magenta>...", path)
                shutil.rmtree(path, ignore_errors=True)
    else:
        mprint("<yellow>Note:</yellow> '{}' is not owned by EDPM. Remove manually:\n  {}", dep_name, install_path)

    # 4) Update the lock file => clear out install_path (so it’s no longer "installed")
    api.lock.update_package(dep_name, {
        "install_path": "",
        "built_with_config": {}
    })
    api.lock.save()

    # 5) Optionally rebuild environment scripts
    mprint("\nRebuilding environment scripts...")
    api.save_generator_scripts()

    mprint("<green>Success:</green> Cleaned '{}' installation", dep_name)
