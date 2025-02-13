import os

import click

from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.db import INSTALL_PATH, IS_OWNED, SOURCE_PATH, BUILD_PATH
from edpm.engine.output import markup_print as mprint


# @click.group(invoke_without_command=True)
@click.command()
@click.argument('packet_names', nargs=-1, metavar='<packet-name>')
@click.option('--install', 'print_mode', flag_value='install', help="Print installation directory")
@click.option('--build', 'print_mode', flag_value='build', help="Print build directory")
@click.option('--source', 'print_mode', flag_value='source', help="Print source directory")
@click.option('--all', 'print_mode', default=True, flag_value='all', help="Print all information on the package")


@pass_edpm_context
@click.pass_context
def pwd(ctx, ectx, packet_names, print_mode):
    """Shows a directory related to the active packet

    Remark:
        Running `edpm` command shows the directories too, but this command shows the dir
        for a package and can be used in scripts and whatsoever

    Usage:
        edpm cd                  # cd-s to edpm top dir
        edpm cd <packet-name>    # cd-s to <packet-name> installation dir

    """
    from edpm.engine.db import INSTALL_PATH, IS_OWNED, SOURCE_PATH, BUILD_PATH
    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    # Check that the packet name is from known packets
    if not packet_names:
        pwd_path = ectx.db.top_dir
        mprint(pwd_path)

    else:
        # Get installation data for the active install
        packet_name = packet_names[0]
        ectx.ensure_installer_known(packet_name)
        install_data = ectx.db.get_active_install(packet_name)
        if not install_data:
            mprint("No active installation data found for the packet '{}'", packet_name)
            raise click.Abort()

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
    # If edpm 'owns' an installation at this point we assume that parent directory usually is needed
    # Like if edpm owns 'root' it is assumed that <top-dir>/root is needed rather than <top-dir>/root/root-v6-...
    pwd_path = install_data[INSTALL_PATH]
    mprint("<blue><b>Install path: </b></blue>\n{}", pwd_path)

    if install_data[IS_OWNED]:
        pwd_path = os.path.dirname(pwd_path)
        mprint("<blue><b>edpm 'owned' base path: </b></blue>\n{}", pwd_path)

    # Source path if known
    if SOURCE_PATH in install_data:
        mprint("<blue><b>Sources: </b></blue>\n{}", install_data[SOURCE_PATH])

    if BUILD_PATH in install_data:
        mprint("<blue><b>Build dir: </b></blue>\n{}", install_data[BUILD_PATH])

    # os.chdir(cd_path)




