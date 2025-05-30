import click
from edpm.engine.output import markup_print as mprint


@click.command("install")
@click.option('--force', is_flag=True, default=False, help="Force rebuild/reinstall even if already installed.")
@click.option('--top-dir', default="", help="Override or set top_dir in the lock file.")
@click.option('--explain', 'just_explain', is_flag=True, default=False, help="Print what would be installed but don't actually install.")
@click.option('--add', '-a', is_flag=True, default=False, help="Automatically add packages to the plan if not already present.")
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
        # Parse package names to extract base names (without @version)
        dep_names = []
        for pkg_name in names:
            # Parse package name to extract base name and version
            base_name = pkg_name
            user_version = None
            if '@' in pkg_name:
                base_name, user_version = pkg_name.split('@', 1)

            dep_names.append(base_name)

            # Check if package is in plan (using base name)
            if not edpm_api.plan.has_package(base_name):
                if add:
                    # Auto-add the package to the plan with --add/-a flag
                    mprint(f"<yellow>Package '{pkg_name}' not in plan.</yellow> "
                           f"Adding it automatically (-a,--add flag)")
                    # Call the add_command logic to add the package
                    try:
                        # Add the full package name (with version) to the plan
                        edpm_api.plan.add_package(pkg_name)
                        edpm_api.plan.save(edpm_api.plan_file)
                        mprint(f"<green>Added '{pkg_name}' to the plan.</green>")
                    except Exception as e:
                        mprint(f"<red>Error:</red> Failed to add '{pkg_name}' to plan: {str(e)}")
                        exit(1)
                else:
                    # Without --add flag, show an error and suggest using it
                    _print_error_not_in_plan(pkg_name)
                    exit(1)
            else:
                # Package exists in plan - check for version conflicts
                if user_version:
                    existing_pkg = edpm_api.plan.find_package(base_name)
                    existing_version = existing_pkg.config.get("version", "")

                    if existing_version and existing_version != user_version:
                        _print_error_version_conflict(base_name, existing_version, user_version)
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


def _print_error_not_in_plan(pkg_name):
    mprint(f"<red>Error:</red> '{pkg_name}' is not in plan!")
    mprint(f"Options:")
    mprint(f"1. Add it to plan by editing the file")
    mprint(f"2. Use <blue>'edpm add {pkg_name}'</blue> command")
    mprint(f"3. Use <blue>'edpm install --add {pkg_name}'</blue> to add and install")


def _print_error_version_conflict(base_name, existing_version, user_version):
    mprint(f"<red>Error:</red> Version conflict for package '{base_name}'!")
    mprint(f"  Plan has version: <blue>{existing_version}</blue>")
    mprint(f"  You specified: <blue>{user_version}</blue>")
    mprint(f"")
    mprint(f"Options:")
    mprint(f"1. Edit the plan file to change the version")
    mprint(f"2. Use <blue>'edpm config {base_name} version={user_version}'</blue> to update the plan")
    mprint(f"3. Install without specifying version: <blue>'edpm install {base_name}'</blue>")
