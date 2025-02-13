import click

from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.output import markup_print as mprint


_help_option_db = "Removes only DB record"
_help_option_all = "Removes DB record and packet folder from disk"
_help_option_auto = "Removes from DB and disk if(!) the packet is owned by edpm"


# @click.group(invoke_without_command=True)
@click.command()
@click.argument('packet_name', nargs=1, metavar='<packet-name>')
@click.argument('install_paths', nargs=-1, metavar='<path>')
@click.option('--db', 'mode', flag_value='db', help=_help_option_db)
@click.option('--all', 'mode', flag_value='all', help=_help_option_all)
@click.option('--auto', 'mode', flag_value='auto', help=_help_option_auto, default=True)
@pass_edpm_context
@click.pass_context
def rm(ctx, ectx, packet_name, install_paths, mode):
    """Removes a packet.
    By default deletes record from edpm DB and the disk folders if the packet is 'owned' by edpm.

    Usage:
        edpm rm <packet-name>         # removes active install of the packet
        edpm rm <packet-name> <path>  # removes the install with the path

    """
    from edpm.engine.db import INSTALL_PATH, IS_OWNED, SOURCE_PATH, BUILD_PATH
    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    # Check that the packet name is from known packets
    ectx.ensure_installer_known(packet_name)

    if not install_paths:
        install_data = ectx.db.get_active_install(packet_name)
        if not install_data:
            print("No active installation data found for the packet {}".format(packet_name))
            raise click.Abort()
        else:
            print("No path provided. <b>Using 'active' install</b>")
    else:
        install_path = install_paths[0]     # todo multiple paths
        install_data = ectx.db.get_install(packet_name, install_path)
        if not install_data:
            print("No active installation data found for the packet {} and path:\n{}"
                  .format(packet_name, install_path))
            raise click.Abort()

    mprint("<blue><b>Removing install with path: </b></blue>")
    mprint("  {}\n", install_data[INSTALL_PATH])

    remove_folder = False
    if mode == 'all':
        remove_folder = True
    if mode == 'auto':
        remove_folder = install_data[IS_OWNED]
        if not remove_folder:
            mprint("<b>(!)</b> the packet is not 'owned' by edpm. The record is removed from DB but\n"
                   "<b>(!)</b>you have to remove the folder manually:\n{}\n", install_data[INSTALL_PATH])

    ectx.db.remove_install(packet_name, install_data[INSTALL_PATH])
    ectx.db.save()

    # Update environment scripts
    mprint("Updating environment script files...\n")
    ectx.save_default_bash_environ()
    ectx.save_default_csh_environ()

    # remove the folder
    if remove_folder:
        mprint("...trying to remove the folder from disk...\n")
        from edpm.engine.commands import run

        run('rm -rf "{}"'.format(install_data[INSTALL_PATH]))

        if SOURCE_PATH in install_data:
            run('rm -rf "{}"'.format(install_data[SOURCE_PATH]))

        if BUILD_PATH in install_data:
            run('rm -rf "{}"'.format(install_data[BUILD_PATH]))
