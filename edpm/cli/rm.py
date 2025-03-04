import click
import os
import shutil

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint


_help_option_lock = "Removes only lock file record without touching installation"
_help_option_all = "Removes lock record and package folder from disk"
_help_option_auto = "Removes from lock and disk if(!) the package is owned by edpm"


@click.command("rm")
@click.argument('package_name', nargs=1, metavar='<package-name>')
@click.option('--lock', 'mode', flag_value='lock', help=_help_option_lock)
@click.option('--all', 'mode', flag_value='all', help=_help_option_all)
@click.option('--auto', 'mode', flag_value='auto', help=_help_option_auto, default=True)
@click.pass_context
def rm_command(ctx, package_name, mode):
    """Removes a package.
    By default, deletes record from edpm lock file and the disk folders if the package is 'owned' by edpm.

    Usage:
        edpm rm <package-name>         # removes the package
        edpm rm <package-name> --lock  # removes only from lock file
        edpm rm <package-name> --all   # forces removal of all files even for non-owned packages

    """
    api = ctx.obj
    assert isinstance(api, EdpmApi)

    # Ensure lock file exists
    api.ensure_lock_exists()

    # Load plan and lock if not already loaded
    if not api.plan or not api.lock:
        api.load_all()

    # Check if package exists
    if not api.plan.find_package(package_name):
        mprint("<red>Error:</red> Package '{}' not found in the plan.", package_name)
        raise click.Abort()

    # Check if package is installed
    if not api.lock.is_installed(package_name):
        mprint("<red>Error:</red> Package '{}' is not installed.", package_name)
        raise click.Abort()

    # Get package data
    package_data = api.lock.get_installed_package(package_name)
    install_path = package_data.get("install_path", "")

    mprint("<blue><b>Removing package: </b></blue> {}", package_name)
    mprint("<blue><b>Installation path: </b></blue> {}\n", install_path)

    # Determine if we should remove folders based on mode and ownership
    remove_folders = False
    if mode == 'all':
        remove_folders = True
    elif mode == 'auto':
        remove_folders = package_data.get("owned", True)
        if not remove_folders:
            mprint("<b>(!)</b> Package is not 'owned' by edpm. The record is removed from lock file but\n"
                   "<b>(!)</b> you have to remove the folder manually:\n{}\n", install_path)

    # Remove package from lock file
    api.lock.remove_package(package_name)
    api.lock.save()

    # Update environment scripts
    mprint("Updating environment script files...\n")
    api.save_generator_scripts()

    # Remove folders if needed
    if remove_folders and os.path.exists(install_path):
        mprint("Removing installation folder from disk...\n")
        try:
            shutil.rmtree(install_path)
            mprint("<green>Successfully removed folder:</green> {}", install_path)
        except Exception as e:
            mprint("<red>Error removing folder:</red> {}", str(e))

        # Remove source and build folders if they exist
        source_path = package_data.get("source_path", "")
        if source_path and os.path.exists(source_path):
            try:
                shutil.rmtree(source_path)
                mprint("<green>Successfully removed source folder:</green> {}", source_path)
            except Exception as e:
                mprint("<red>Error removing source folder:</red> {}", str(e))

        build_path = package_data.get("build_path", "")
        if build_path and os.path.exists(build_path):
            try:
                shutil.rmtree(build_path)
                mprint("<green>Successfully removed build folder:</green> {}", build_path)
            except Exception as e:
                mprint("<red>Error removing build folder:</red> {}", str(e))

    mprint("<green>Package '{}' has been removed.</green>", package_name)