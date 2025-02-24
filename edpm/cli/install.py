# cli/install.py

import os
import click
from edpm.engine.output import markup_print as mprint
from edpm.engine.api import EdpmApi  # EdpmApi is your new-based approach

@click.command()
@click.option('--missing', 'dep_mode', flag_value='missing', default=True,
              help="Installs only missing dependencies (default).")
@click.option('--single', 'dep_mode', flag_value='single',
              help="Installs only the specified package(s), ignoring whether they're installed.")
@click.option('--force', 'dep_mode', flag_value='single',
              help="Alias for --single. Force reinstall of a single package.")
@click.option('--all', 'dep_mode', flag_value='all',
              help="Installs all dependencies from the plan, even if installed.")
@click.option('--top-dir', default="", help="Override or set top_dir in the lock file.")
@click.option('--explain', 'just_explain', is_flag=True, default=False,
              help="Print what would be installed but don't actually install.")
@click.option('--deps-only', is_flag=True, default=False,
              help="Install only the dependencies, not the specified package(s).")
@click.argument('names', nargs=-1)
@click.pass_context
def install(ctx, dep_mode, names, top_dir, just_explain, deps_only):
    """
    Installs packages (and their dependencies) from the plan, updating the lock file.

    Use Cases:
      1) 'edpm install' with no arguments installs EVERYTHING in the plan.
      2) 'edpm install <pkg>' adds <pkg> to the plan if not present, then installs it.
    """

    edpm_api = ctx.obj
    assert isinstance(edpm_api, EdpmApi)

    # 2) Possibly override top_dir
    if top_dir:
        edpm_api.set_top_dir(top_dir)

    # 3) If no arguments => install everything from the plan
    if not names:
        # "dep_names" = all from the plan
        dep_names = [dep.name for dep in edpm_api.plan.dependencies()]
        if not dep_names:
            mprint("<red>No dependencies in the plan!</red> "
                   "Please add packages or run 'edpm install <pkg>' to auto-add.")
            return
    else:
        # If user provided package names, let's auto-add them to the plan if not present
        # Then those become dep_names
        dep_names = []
        for pkg_name in names:
            # If the package is missing in the plan, add it automatically
            if not edpm_api.plan.has_dependency(pkg_name):
                mprint(f"<red>Error:</red> '{pkg_name}' is not in plan!")
                mprint(f"Please add it to plan either by editing the file or by <blue>'edpm add'</blue> command")
                exit(1)     # Does it normal to terminate like this?

            dep_names.append(pkg_name)

    # 4) Actually run the install logic
    edpm_api.install_dependency_chain(
        dep_names=dep_names,
        mode=dep_mode,
        explain=just_explain,
        deps_only=deps_only
    )

    # 5) If not just_explain, optionally generate environment scripts
    if not just_explain:
        mprint("\nUpdating environment script files...\n")
        edpm_api.save_shell_environment(shell="bash")
        edpm_api.save_shell_environment(shell="csh")
