тьббь# EXAMPLE EMPTY COMMAND to copy paste to create a new one

import click

from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.output import markup_print as mprint


# @click.group(invoke_without_command=True)
@click.command()
@click.argument('packet_name', nargs=1)
@click.argument('install_path', nargs=1)
@pass_edpm_context
@click.pass_context
def example_command(ctx, ectx, packet_name, install_path):
    """example_command - Description

    \b
    Example:
      example_command ...
      example_command ...
    """

    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    # Check that the packet name is from known packets
    ectx.ensure_installer_known(packet_name)

    # update_install will add or update the packet install. We set it active as it make sense...
    from edpm.engine.db import IS_ACTIVE
    ectx.db.update_install(packet_name, install_path, {IS_ACTIVE: True})
    ectx.db.save()

    # Update environment scripts
    mprint("Updating environment script files...\n")
    ectx.save_default_bash_environ()
    ectx.save_default_csh_environ()
