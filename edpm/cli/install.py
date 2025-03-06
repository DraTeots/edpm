# cli/install.py


import click
from edpm.engine.output import markup_print as mprint
from edpm.engine.api import EdpmApi  # EdpmApi is your new-based approach

@click.command("install")
@click.option('--force', is_flag=True, default=False,
              help="Force rebuild/reinstall even if already installed.")
@click.option('--top-dir', default="", help="Override or set top_dir in the lock file.")
@click.option('--explain', 'just_explain', is_flag=True, default=False,
              help="Print what would be installed but don't actually install.")
@click.option('--add', '-a', is_flag=True, default=False,
              help="Automatically add packages to the plan if not already present.")
@click.argument('names', nargs=-1)
@click.pass_context
def install_command(ctx, names, add, top_dir, just_explain, force):
    """
    Installs packages (and their dependencies) from the plan, updating the lock file.

    Use Cases:
      1) 'edpm install' with no arguments installs EVERYTHING in the plan.
      2) 'edpm install <pkg>' adds <pkg> to the plan if not present, then installs it.
    """

    edpm_api = ctx.obj
    # assert isinstance(edpm_api, EdpmApi)

    # 2) Possibly override top_dir
    if top_dir:
        edpm_api.top_dir = top_dir

    # 3) If no arguments => install everything from the plan
    if not names:
        # "dep_names" = all from the plan
        dep_names = [dep.name for dep in edpm_api.plan.packages()]
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
                if add:
                    # Auto-add the package to the plan with --add/-a flag
                    mprint(f"<yellow>Package '{pkg_name}' not in plan.</yellow> "
                           f"Adding it automatically (-a,--add flag)")
                    # Call the add_command logic to add the package
                    try:
                        # Simple approach: just append the package name as a string to the packages list
                        edpm_api.plan.add_package(pkg_name)
                        edpm_api.plan.save(edpm_api.plan_file)
                        mprint(f"<green>Added '{pkg_name}' to the plan.</green>")
                    except Exception as e:
                        mprint(f"<red>Error:</red> Failed to add '{pkg_name}' to plan: {str(e)}")
                        exit(1)
                else:
                    # Without --add flag, show an error and suggest using it
                    mprint(f"<red>Error:</red> '{pkg_name}' is not in plan!")
                    mprint(f"Options:")
                    mprint(f"1. Add it to plan by editing the file")
                    mprint(f"2. Use <blue>'edpm add {pkg_name}'</blue> command")
                    mprint(f"3. Use <blue>'edpm install --add {pkg_name}'</blue> to add and install")
                    exit(1)

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
