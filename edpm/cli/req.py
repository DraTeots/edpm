
import click

from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.output import markup_print as mprint

# @click.group(invoke_without_command=True)
@click.command()
@click.argument('os_name', nargs=1, metavar='<os-name>')
@click.argument('args', nargs=-1, metavar='<packet-names>')
@click.option('--optional', 'print_mode', flag_value='optional', help="Print optional packages")
@click.option('--required', 'print_mode', flag_value='required', help="Print required packages")
@click.option('--all', 'print_mode', flag_value='all', help="Print all packages (ready for packet manager install)")
@click.option('--all-titles', 'print_mode', flag_value='all_titles', help="Print all packages (human readable)", default=True)
@pass_edpm_context
@click.pass_context
def req(ctx, ectx, os_name, args, print_mode):
    """req - Shows required packages that can be installed by operating system.

    \b
    Example:
      req ubuntu22
      req centos7 eicrecon
      req centos8 root clhep

    By adding --optional, --required, --all flags you can use this command with packet managers:\n
      apt install `edpm req ubuntu --all`

    Known OS: ubuntu18 ubuntu22 centos7 centos8

    Aliases: rhel, rhel7, rhel8, mint, debian, ubuntu
    """

    os_aliases = {
        "ubuntu": "ubuntu22",
        "rhel": "centos8",
        "rhel7": "centos7",
        "rhel8": "centos8",
        "mint": "ubuntu22",
        "debian": "ubuntu18"
    }

    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    # We have some args, first is os name like 'ubuntu' or 'centos'
    known_os = ectx.req_get_known_os()

    if os_name in os_aliases.keys():
        os_name = os_aliases[os_name]

    if os_name not in known_os:
        mprint('<red><b>ERROR</b></red>: name "{}" is unknown\nKnown os names are:', os_name)
        for name in known_os:
            mprint('   {}', name)
        click.echo(ctx.get_help())
        ctx.exit(1)

    # We have something like 'ubuntu eicrecon'
    required, optional = ectx.req_get_deps(os_name, args)

    if print_mode == "optional":
        mprint(" ".join(optional))
    elif print_mode == "required":
        mprint(" ".join(required))
    elif print_mode == "all":
        mprint(" ".join(optional + required))
    else:
        # print all with juman readable titles
        mprint("<blue><b>REQUIRED</b></blue>:")
        mprint(" ".join(required))
        mprint("<blue><b>OPTIONAL</b></blue>:")
        mprint(" ".join(optional))
