import os
import sys
import click
from typing import Dict, List, Set, Tuple, Optional

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint

@click.command()
@click.argument('os_name', nargs=1, metavar='<os-name>')
@click.argument('package_names', nargs=-1, metavar='<package-names>')
@click.option('--optional', 'print_mode', flag_value='optional', help="Print optional packages")
@click.option('--required', 'print_mode', flag_value='required', help="Print required packages")
@click.option('--all', 'print_mode', flag_value='all', help="Print all packages (ready for package manager install)")
@click.option('--all-titles', 'print_mode', flag_value='all_titles', help="Print all packages (human readable)", default=True)
def req_command(ctx, os_name, package_names, print_mode):
    """Get list of system requirements for specified packages.

    Example:
        edpm req ubuntu root
        edpm req centos root geant4
    """
    assert isinstance(ctx.obj, EdpmApi)
    api = ctx.obj
    api.load_all()

    # OS mapping - define supported OS types and aliases
    os_aliases = {
        "ubuntu": "ubuntu",
        "debian": "ubuntu",  # Use ubuntu packages for debian
        "centos": "centos",
        "rhel": "centos",    # Use centos packages for RHEL
        "fedora": "centos",  # Use centos packages for fedora
    }

    # Check if OS is supported
    if os_name.lower() not in os_aliases:
        mprint('<red><b>ERROR</b></red>: OS name "{}" is unknown\nKnown OS names are:', os_name)
        for name in sorted(os_aliases.keys()):
            mprint('   {}', name)
        sys.exit(1)

    normalized_os = os_aliases[os_name.lower()]

    # Get requirements
    required_pkgs, optional_pkgs = gather_requirements(api, normalized_os, package_names)

    # Display results according to print_mode
    if print_mode == 'optional':
        mprint(" ".join(optional_pkgs))
    elif print_mode == 'required':
        mprint(" ".join(required_pkgs))
    elif print_mode == 'all':
        mprint(" ".join(required_pkgs + optional_pkgs))
    else:  # all_titles
        mprint("<blue><b>REQUIRED</b></blue>:")
        for pkg in sorted(required_pkgs):
            mprint("  {}", pkg)

        if optional_pkgs:
            mprint("\n<blue><b>OPTIONAL</b></blue>:")
            for pkg in sorted(optional_pkgs):
                mprint("  {}", pkg)


def gather_requirements(api: EdpmApi, normalized_os: str, package_names: Tuple[str]) -> Tuple[List[str], List[str]]:
    """Gather requirements from packages and their recipes."""
    required_pkgs: Set[str] = set()
    optional_pkgs: Set[str] = set()

    # If no packages specified, get requirements for all packages in the plan
    if not package_names:
        package_names = [p.name for p in api.plan.packages()]

    # Get global requirements if they exist
    global_config = api.plan.global_config()
    global_require = global_config.get("require", {})

    # Extract from global require section
    os_reqs = global_require.get(normalized_os, {})
    if isinstance(os_reqs, list):
        required_pkgs.update(os_reqs)
    elif isinstance(os_reqs, dict):
        required_pkgs.update(os_reqs.get("required", []))
        optional_pkgs.update(os_reqs.get("optional", []))

    # Get package-specific requirements
    for pkg_name in package_names:
        # Get the package from the plan
        pkg = api.plan.find_package(pkg_name)
        if not pkg:
            mprint('<yellow>Warning:</yellow> Package "{}" not found in the plan', pkg_name)
            continue

        # Check for require section in package config
        if hasattr(pkg, 'config') and isinstance(pkg.config, dict):
            pkg_require = pkg.config.get("require", {})
            os_reqs = pkg_require.get(normalized_os, {})
            if isinstance(os_reqs, list):
                required_pkgs.update(os_reqs)
            elif isinstance(os_reqs, dict):
                required_pkgs.update(os_reqs.get("required", []))
                optional_pkgs.update(os_reqs.get("optional", []))

        # Also check if there's a recipe with os_dependencies
        recipe_name = pkg_name
        # Try to get recipe class from recipe manager
        recipe_cls = api.recipe_manager.recipes_by_name.get(recipe_name)
        if recipe_cls:
            if hasattr(recipe_cls, 'os_dependencies') and isinstance(recipe_cls.os_dependencies, dict):
                # Extract from recipe's os_dependencies
                required = recipe_cls.os_dependencies.get('required', {}).get(normalized_os, "")
                optional = recipe_cls.os_dependencies.get('optional', {}).get(normalized_os, "")

                if required:
                    if isinstance(required, str):
                        required_pkgs.update(required.split())
                    elif isinstance(required, list):
                        required_pkgs.update(required)

                if optional:
                    if isinstance(optional, str):
                        optional_pkgs.update(optional.split())
                    elif isinstance(optional, list):
                        optional_pkgs.update(optional)

    # Make sure no package is both required and optional
    optional_pkgs = optional_pkgs - required_pkgs

    return list(required_pkgs), list(optional_pkgs)