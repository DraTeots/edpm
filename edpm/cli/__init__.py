
import os
import click


from edpm.engine.api import EdpmApi, print_packets_info
from edpm.engine.db import PacketStateDatabase
from edpm.engine.output import markup_print as mprint

# We import the version from __init__.py
from edpm.version import version

# CLI Commands from your submodules
from edpm.cli.env import env_group
from edpm.cli.install import install as install_group
from edpm.cli.find import find as find_group
from edpm.cli.req import req as requirements_command
from edpm.cli.set import set as set_command
from edpm.cli.rm import rm as rm_command
from edpm.cli.pwd import pwd as pwd_command
from edpm.cli.clean import clean_command
from edpm.cli.info import info as info_command
from edpm.cli.config import config as config_command
from edpm.cli.init import init as init_command
from edpm.cli.add import add_command

def print_first_time_message():
    mprint(
        """
The plan file doesn't exist. It might be, that you are running 'edpm' for the first time.

1. Install or check OS-managed packages:
    > edpm init                  # To initialize plan.edpm.yaml
    > edpm install root          # for eicrecon and its dependencies only

   (Use 'ubuntu' for Debian/Ubuntu, 'centos' for RHEL/CentOS, etc. 
    Future versions may support macOS or more granularity.)

2. By default, EDPM installs dependencies locally under './edpm-packages/' in your project. 
   If you'd prefer a different location (e.g., on a larger disk), run:
    > edpm --top-dir=/bigdisk/edpm
   This path will be saved in the lock file so you don't have to specify it again.

3. (Optional) If you already have certain dependencies installed (e.g. CERN ROOT),
   you can register their locations:
    > edpm set root /path/to/existing/ROOT
    > edpm set <name> <path>

   Or discover missing dependencies:
    > edpm install eicrecon --missing --explain

4. Then install all missing dependencies:
    > edpm install eicrecon --missing

P.S. - You can display this message at any time with --help-first.
       - edpm GitLab: https://gitlab.com/DraTeots/edpm
       - This message will disappear once the lock file is created or updated.
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

    plan_file = "plan.edpm.yaml" if not str(plan) else str(plan)
    lock_file = "plan-lock.edpm.yaml" if not str(lock) else str(lock)

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
        api.lock.top_dir = os.path.abspath(os.path.normpath(top_dir))
        api.lock.save()
        db_existed = True  # We forced a save => DB now exists

    # If no existing DB, show welcome message

    # If no subcommand, print version and some DB info
    if ctx.invoked_subcommand is None:
        mprint("<b><blue>edpm</blue></b> v{}", version)
        mprint("<b><blue>top dir :</blue></b>\n  {}", api.lock.top_dir)
        mprint("  (users are encouraged to inspect/edit it)")
        # mprint("<b><blue>env files :</blue></b>\n  {}\n  {}", api.config[ENV_SH_PATH], api.config[ENV_CSH_PATH])
        print_packets_info(api)


# Register all subcommands
edpm_cli.add_command(install_group)
# edpm_cli.add_command(find_group)
edpm_cli.add_command(env_group)
# edpm_cli.add_command(requirements_command)
# edpm_cli.add_command(set_command)
# edpm_cli.add_command(rm_command)
# edpm_cli.add_command(pwd_command)
# edpm_cli.add_command(clean_command)
edpm_cli.add_command(info_command)
edpm_cli.add_command(config_command)
edpm_cli.add_command(init_command)
edpm_cli.add_command(add_command)
