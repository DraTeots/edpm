# edpm/main.py

import os
import click

from edpm.engine.api import (
    pass_edpm_context,
    DB_FILE_PATH,
    ENV_CSH_PATH,
    ENV_SH_PATH,
    EdpmApi,
    print_packets_info
)
from edpm.engine.db import PacketStateDatabase
from edpm.engine.output import markup_print as mprint

# We import the version from __init__.py
from edpm import version

# CLI Commands from your submodules
from edpm.cli.env import env as env_group
from edpm.cli.install import install as install_group
from edpm.cli.find import find as find_group
from edpm.cli.req import req as requirements_command
from edpm.cli.set import set as set_command
from edpm.cli.rm import rm as rm_command
from edpm.cli.pwd import pwd as pwd_command
from edpm.cli.clean import clean as clean_command
from edpm.cli.info import info as info_command
from edpm.cli.config import config as config_command
from edpm.cli.mergedb import mergedb as mergedb_command


def print_first_time_message():
    mprint(
        """
The database file doesn't exist. Probably you run 'edpm' for one of the first times.

1. Install or check OS maintained required packages:
    > edpm req ubuntu              # for all packets edpm knows to build/install
    > edpm req ubuntu eicrecon     # for eicrecon and its dependencies only
   
   * - put 'ubuntu' for Debian or 'centos' for RHEL/CentOS. 
     (Future versions may support macOS or more granular versions.)

2. Set <b><blue>top-dir</blue></b> to start. This is where all missing packets will be installed.   
   > edpm --top-dir=<where-to-install-all>
   
3. (Optional) If you have CERN.ROOT installed (version >= 6.14.00):
   > edpm set root `$ROOTSYS`
   
   Similarly set paths for other installed dependencies:
   > edpm install eicrecon --missing --explain   # see missing dependencies
   > edpm set <name> <path>                      # register an existing dependency path
   
4. Then install all missing dependencies:
   > edpm install eicrecon --missing
   

P.S. - You can read this message any time with --help-first
       - edpm GitLab: https://gitlab.com/eic/edpm
       - This message will disappear after any command that makes changes
"""
    )
    click.echo()


@click.group(invoke_without_command=True)
@click.option('--manifest', default="", help="The manifest file. Default is package.edpm.yaml")
@click.option('--top-dir', default="", help="Where EDPM should install missing packages.")
@pass_edpm_context
@click.pass_context
def edpm_cli(ctx, ectx, manifest, top_dir):
    """
    EDPM stands for EIC Development Packet Manager.
    If you run this command with no subcommand, it prints the version
    and a short summary of installed/known packages.
    """
    assert isinstance(ectx, EdpmApi), "EdpmApi context not available."

    manifest_file = "package.edpm.yaml" if not str(manifest) else str(manifest)

    # Load db and modules from disk
    db_existed = ectx.load_shmoad_ugly_toad(manifest_file)  # False => couldn't load & used defaults

    # If user passed --top-dir, set it in the DB
    if top_dir:
        ectx.db.top_dir = os.path.abspath(os.path.normpath(top_dir))
        ectx.db.save()
        db_existed = True  # We forced a save => DB now exists

    # If no existing DB, show welcome message
    if not db_existed:
        print_first_time_message()
    else:
        # If no subcommand, print version and some DB info
        if ctx.invoked_subcommand is None:
            mprint("<b><blue>edpm</blue></b> v{}", version)
            mprint("<b><blue>top dir :</blue></b>\n  {}", ectx.db.top_dir)
            mprint("<b><blue>state db :</blue></b>\n  {}", ectx.config[DB_FILE_PATH])
            mprint("  (users are encouraged to inspect/edit it)")
            mprint("<b><blue>env files :</blue></b>\n  {}\n  {}", ectx.config[ENV_SH_PATH], ectx.config[ENV_CSH_PATH])
            print_packets_info(ectx.db)


# Register all subcommands
edpm_cli.add_command(install_group)
edpm_cli.add_command(find_group)
edpm_cli.add_command(env_group)
edpm_cli.add_command(requirements_command)
edpm_cli.add_command(set_command)
edpm_cli.add_command(rm_command)
edpm_cli.add_command(pwd_command)
edpm_cli.add_command(clean_command)
edpm_cli.add_command(info_command)
edpm_cli.add_command(config_command)
edpm_cli.add_command(mergedb_command)


def main():
    """
    Main entrypoint if users run `python -m edpm.main`
    or if you have a setup entrypoint referencing `edpm.main:main`.
    """
    edpm_cli()


# If users run "python -m edpm.main", the code below triggers the CLI.
if __name__ == '__main__':
    main()
