import click

from edpm.engine.api import pass_edpm_context
from edpm.engine.db import PacketStateDatabase


@click.group(invoke_without_command=True)
@pass_edpm_context
@click.pass_context
def find(ctx, ectx):
    assert (isinstance(ectx.db, PacketStateDatabase))

    db = ectx.db

    click.echo("installed packets:")

    print(db.installed)
    click.echo("missing packets:")
    print(db.missing)

    if not db.top_dir:

        click.echo("Provide the top dir to install things to:")
        click.echo("Run edpm with --top-dir=<packets top dir>")
        return

    ctx.invoke('root install')



