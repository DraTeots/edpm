# cli/info.py

import click
from edpm.engine.output import markup_print as mprint
from edpm.engine.api import EdpmApi

@click.command()
@click.option('--cmake', 'flag_cmake', is_flag=True, default=False, help="Show info in terms of CMake flags (example).")
@click.pass_context
def info(ctx, flag_cmake):
    """
    Prints information about the EDPM state.
    e.g. which packages are installed, top_dir, etc.
    """
    # Ensure plan & lock are loaded
    ectx = ctx.obj
    if not ectx.plan or not ectx.lock.file_path:
        ectx.load_manifest_and_lock("plan.edpm.yaml", "plan-lock.edpm.yaml")

    # Print top_dir
    top_dir = ectx.get_top_dir()
    mprint("Top dir: {}", top_dir)

    # Show installed packages
    installed = []
    for dep_name in ectx.lock.get_all_dependencies():
        if ectx.lock.is_installed(dep_name):
            dep_data = ectx.lock.get_dependency(dep_name)
            ipath = dep_data.get("install_path")
            installed.append((dep_name, ipath))

    if installed:
        mprint("\n<magenta>Installed packages:</magenta>")
        for dep_name, ipath in installed:
            mprint("  <blue>{}</blue> at {}", dep_name, ipath)
    else:
        mprint("\nNo installed packages found in the lock file.")

    if flag_cmake:
        # Example usage: generate some -D flags
        # This is an ad-hoc example, as you had in old code
        # In new code, you'd decide how to interpret the installed paths.
        cmake_flags = []
        for dep_name, ipath in installed:
            # Suppose you map each dep_name to a cmake variable, e.g. MYLIB_PATH
            var_name = f"{dep_name.upper()}_DIR"  # or a real mapping
            cmake_flags.append(f'-D{var_name}="{ipath}"')
        mprint("\nCMake style flags:\n{}", " ".join(cmake_flags))
