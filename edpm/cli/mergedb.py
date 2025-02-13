import io
import os

import click

from edpm.engine.api import pass_edpm_context, EdpmApi, print_packets_info
from edpm.engine.output import markup_print as mprint


# @click.group(invoke_without_command=True)
@click.command()
@click.argument('import_file', nargs=1)
@pass_edpm_context
@click.pass_context
def mergedb(ctx, ectx, import_file):
    """Merges packet installation data into existing DB

    This command might be useful if one has DB installation and users
    would like to use centrally installed packages overriding some of them
    with new packages
    """

    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    if not os.path.isfile(import_file):
        exit("Error! file '{}' does not exists or is not a file".format(import_file))


    # update_install will add or update the packet install. We set it active as it make sense...

    ectx.merge_external_db(import_file)
    ectx.db.save()

    # Update environment scripts
    mprint("Updating environment script files...\n")
    ectx.save_default_bash_environ()
    ectx.save_default_csh_environ()

    mprint("DB after the update:\n")

    print_packets_info(ectx.db)

