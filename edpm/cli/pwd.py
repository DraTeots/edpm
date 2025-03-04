import os

import click

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint

# Constants for lock file keys
INSTALL_PATH = "install_path"
SOURCE_PATH = "source_path"
BUILD_PATH = "build_path"
IS_OWNED = "owned"


@click.command("pwd")
@click.argument('packet_names', nargs=-1, metavar='<packet-name>')
@click.option('--install', 'print_mode', flag_value='install', help="Print installation directory")
@click.option('--build', 'print_mode', flag_value='build', help="Print build directory")
@click.option('--source', 'print_mode', flag_value='source', help="Print source directory")
@click.option('--all', 'print_mode', default=True, flag_value='all', help="Print all information on the package")
@click.pass_context
def pwd_command(ctx, packet_names, print_mode):
    """Shows directories related to the active package

    Remark:
        Running `edpm` command shows the directories too, but this command shows the dir
        for a package and can be used in scripts and whatsoever

    Usage:
        edpm pwd                  # shows the edpm top dir
        edpm pwd <packet-name>    # shows paths for <packet-name>
        edpm pwd <packet-name> --install  # only shows installation path

    """
    api = ctx.obj
    assert isinstance(api, EdpmApi)

    # Ensure lock file exists
    api.ensure_lock_exists()

    # Load plan and lock if not already loaded
    if not api.plan or not api.lock:
        api.load_all()

    # Without arguments, show top directory
    if not packet_names:
        mprint(api.top_dir)
        return

    # Get package information
    packet_name = packet_names[0]

    # Check if package exists in plan
    if not api.plan.find_package(packet_name):
        mprint("<red>Error:</red> Package '{}' not found in the plan.", packet_name)
        raise click.Abort()

    # Check if package is installed
    if not api.lock.is_installed(packet_name):
        mprint("<red>Error:</red> Package '{}' is not installed.", packet_name)
        raise click.Abort()

    # Get package data from lock file
    install_data = api.lock.get_installed_package(packet_name)

    # Display requested information
    if print_mode == 'install':
        _print_single_path(install_data, INSTALL_PATH)
    elif print_mode == 'build':
        _print_single_path(install_data, BUILD_PATH)
    elif print_mode == 'source':
        _print_single_path(install_data, SOURCE_PATH)
    else:
        _pretty_print_all(install_data)


def _print_single_path(install_data, what_path):
    if what_path in install_data:
        print(install_data[what_path])


def _pretty_print_all(install_data):
    # Display installation path
    pwd_path = install_data.get(INSTALL_PATH, "")
    if pwd_path:
        mprint("<blue><b>Install path: </b></blue>\n{}", pwd_path)

    # For packages owned by EDPM, show the base directory
    if install_data.get(IS_OWNED, True):
        base_path = os.path.dirname(pwd_path) if pwd_path else ""
        if base_path:
            mprint("<blue><b>edpm 'owned' base path: </b></blue>\n{}", base_path)

    # Source path if known
    if SOURCE_PATH in install_data:
        mprint("<blue><b>Sources: </b></blue>\n{}", install_data[SOURCE_PATH])

    # Build path if known
    if BUILD_PATH in install_data:
        mprint("<blue><b>Build dir: </b></blue>\n{}", install_data[BUILD_PATH])