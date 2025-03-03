# cli/install.py

import os
import click
from edpm.engine.output import markup_print as mprint
from edpm.engine.api import EdpmApi  # EdpmApi is your new-based approach

@click.command()

@click.option('--force', is_flag=True, default=False,
              help="Force rebuild/reinstall even if already installed.")
@click.option('--top-dir', default="", help="Override or set top_dir in the lock file.")
@click.option('--explain', 'just_explain', is_flag=True, default=False,
              help="Print what would be installed but don't actually install.")
@click.argument('names', nargs=-1)
@click.pass_context
def install(ctx, names, top_dir, just_explain, force):
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
        edpm_api.top_dir = top_dir

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
        dep_names = names
        for pkg_name in names:
            # Lets check if package is in plan
            if not edpm_api.plan.has_package(pkg_name):
                mprint(f"<red>Error:</red> '{pkg_name}' is not in plan!")
                mprint(f"Please add it to plan either by editing the file or by <blue>'edpm add'</blue> command:")
                mprint(f"edpm add {pkg_name}")
                exit(1)     # Does it normal to terminate like this?


    # 4) Actually run the install logic
    edpm_api.install_dependency_chain(
        dep_names=dep_names,
        explain=just_explain,
        force=force
    )

    # 5) If not just_explain, optionally generate environment scripts
    if not just_explain:
        mprint("\nUpdating environment script files...\n")
        edpm_api.save_generator_scripts()
