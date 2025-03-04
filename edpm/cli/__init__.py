import os
import click

from edpm.engine.api import EdpmApi, print_packets_info
from edpm.engine.output import markup_print as mprint
from edpm.version import version

# CLI Commands from your submodules
from edpm.cli.env import env_group
from edpm.cli.install import install_command
from edpm.cli.req import req_command
from edpm.cli.rm import rm_command
from edpm.cli.pwd import pwd_command
from edpm.cli.clean import clean_command
from edpm.cli.info import info_command
from edpm.cli.config import config_command
from edpm.cli.init import init_command
from edpm.cli.add import add_command

def print_first_time_message():
    mprint(
        """
No plan file found. It appears you're running 'edpm' for the first time.

Quick Start Guide:

1. Initialize a new plan file:
   > edpm init                   # Creates plan.edpm.yaml

2. Add and install packages:
   > edpm add clhep root         # Add a packages to the plan
   > edpm install                # Install the packages

3. By default, EDPM installs packages to './edpm-packages/'. 
   To use a different location:
   > edpm --top-dir=/path/to/storage
   This path is saved in the lock file for future use.

4. For pre-existing packages:
   > edpm add --existing root /path/to/existing/installation
   This registers external packages without reinstalling them.

Commands for packages:
   > edpm config <package>       # Set custom build flags
   > edpm pwd <package>          # Show installed package paths
   > edpm rm <package>           # Remove a package

For more help: edpm --help
Project repository: https://gitlab.com/DraTeots/edpm
"""
    )
    click.echo()


@click.group(invoke_without_command=True)
@click.option('--plan', default="", help="The plan file. Default is plan.edpm.yaml")
@click.option('--lock', default="", help="The lock file. Default is plan-lock.edpm.yaml")
@click.option('--top-dir', default="", help="Where EDPM should install missing packages.")
@click.pass_context
def edpm_cli(ctx, plan, lock, top_dir):
    """
    EDPM stands for EIC Development Packet Manager.
    If you run this command with no subcommand, it prints the version
    and a short summary of installed/known packages.
    """
    assert isinstance(ctx, click.Context), "EdpmApi context not available."

    # Get file paths from environment variables or use defaults
    plan_file = os.environ.get("EDPM_PLAN_FILE", "plan.edpm.yaml")
    lock_file = os.environ.get("EDPM_LOCK_FILE", "plan-lock.edpm.yaml")

    # Override with provided parameters if they exist
    if plan:
        plan_file = str(plan)
    if lock:
        lock_file = str(lock)

    if not os.path.isfile(plan_file) and ctx.invoked_subcommand != "init":
        print(f"Plan file does not exists (or there is no access to it): {plan_file}")
        click.echo("Running init command.")
        print_first_time_message()
        exit(1)

    api = EdpmApi(plan_file, lock_file)
    ctx.obj = api

    # Init command presumes there is no plan file. All other commands mean - we must load whatever we can
    if ctx.invoked_subcommand != "init":
        api.load_all()

    # Load db and modules from disk

    # If user passed --top-dir, set it in the DB
    if top_dir:
        if ctx.invoked_subcommand == "init":
            mprint("<b><red>ERROR</red></b> --top-dir flag is given with 'init' command, "
                   "which means the desired lock file doesn't exist yet and we can't save top-dir value. "
                   "Please run 'edpm init' without --top-dir flag and then use:\n"
                   f"edpm --top-dir={top_dir}\n\n")
            exit(1)
        api.lock.top_dir = os.path.abspath(os.path.normpath(top_dir))
        api.lock.save()

    # If no subcommand, print version and some package info
    if ctx.invoked_subcommand is None:
        mprint("<b><blue>edpm</blue></b> v{}", version)
        mprint("<b><blue>top dir :</blue></b>\n  {}", api.lock.top_dir)
        print_packets_info(api)


# Register all subcommands
edpm_cli.add_command(install_command)
edpm_cli.add_command(env_group)
edpm_cli.add_command(req_command)
edpm_cli.add_command(rm_command)
edpm_cli.add_command(pwd_command)
edpm_cli.add_command(clean_command)
edpm_cli.add_command(info_command)
edpm_cli.add_command(config_command)
edpm_cli.add_command(init_command)
edpm_cli.add_command(add_command)
