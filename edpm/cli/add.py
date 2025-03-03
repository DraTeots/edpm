import os
import click

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint

@click.command("add", help="Add a new dependency entry to the plan file.")
@click.option("--fetch", default="", help="Fetcher type or URL (git/tarball/filesystem or autodetect from URL).")
@click.option("--make", default="", help="Maker type (cmake/autotools/manual/custom).")
@click.option("--branch", default="", help="Branch/tag (main, master, v1.2, etc.) if git fetcher.")
@click.option("--location", default="", help="Location/path if manual or filesystem fetcher.")
@click.option("--url", default="", help="Repo or tarball URL if fetch=git or fetch=tarball.")
@click.option("--option", "option_list", multiple=True,
              help="Arbitrary key=value pairs that go into dependency config. E.g. --option cxx_standard=17.")
@click.argument("raw_name", required=True)
@click.pass_context
def add_command(ctx, raw_name, fetch, make, branch, location, url, option_list):
    """
    Updates the plan.edpm.yaml "packages" list to include a new entry.

    Examples:
      edpm add root
      edpm add root@v6.32.0
      edpm add mylib --fetch=git --url=...
    """
    api: EdpmApi = ctx.obj

    # Ensure plan is loaded or show an error
    if not api.plan:
        try:
            api.load_all()
        except FileNotFoundError:
            click.echo(
                "No plan file found. Please run 'edpm init' or specify --plan=... \n"
                "Cannot add dependency because the plan is not available."
            )
            raise click.Abort()
        if not api.plan:
            click.echo(
                "Error: EDPM plan data is not available (api.plan is still None). "
                "Please ensure plan is initialized."
            )
            raise click.Abort()

    # Split out the optional version part. e.g. "root@v6.32.0" => pkg_name="root", version_part="v6.32.0"
    pkg_name = raw_name
    version_part = ""
    if '@' in raw_name:
        parts = raw_name.split('@', 1)
        pkg_name = parts[0]
        version_part = parts[1]

    # Check if this package name already exists
    if api.plan.has_package(pkg_name):
        mprint("<red>Error:</red> A package named '{}' already exists in the plan.", pkg_name)
        raise click.Abort()

    # Check if it's a known recipe
    is_known_recipe = (pkg_name in api.recipe_manager.recipes_by_name)

    # Consider only actual CLI flags as "any_flags"
    # (We do NOT treat version_part as a "flag" for the logic below)
    any_flags = any([fetch, make, branch, location, url, option_list])

    # Decide how to store the item in 'packages'
    # 1) If known recipe, no other flags, and possibly version_part => single string
    if is_known_recipe and not any_flags:
        if version_part:
            # e.g. "root@v6.32.0"
            new_entry = f"{pkg_name}@{version_part}"
        else:
            # e.g. "root"
            new_entry = pkg_name
    else:
        # Otherwise produce a dictionary
        new_entry = {pkg_name: {}}
        config_block = new_entry[pkg_name]

        # If we have a version from '@', store it in 'version'
        if version_part:
            config_block["version"] = version_part

        # Populate fetch
        if fetch:
            config_block["fetch"] = fetch
        elif url:
            # autodetect fetch type from url if user didn't specify
            if url.endswith(".git"):
                config_block["fetch"] = "git"
            elif url.endswith(".tar.gz") or url.endswith(".tgz"):
                config_block["fetch"] = "tarball"
            else:
                config_block["fetch"] = "filesystem"

        # Populate URL or location
        if url:
            config_block["url"] = url
        if location:
            config_block["location"] = location

        # Make
        if make:
            config_block["make"] = make

        # Branch
        if branch:
            config_block["branch"] = branch

        # Additional options
        for opt in option_list:
            if "=" in opt:
                k, v = opt.split("=", 1)
                config_block[k.strip()] = v.strip()
            else:
                mprint("<yellow>Warning:</yellow> Ignoring malformed --option '{}'; expected key=value.", opt)

    # Append and save
    api.plan.data["packages"].append(new_entry)
    api.plan.save(api.plan_file)

    mprint("<green>Added dependency</green> '{}' to the plan.\nCheck plan-file to see or edit details:\n{}",
           raw_name, api.plan_file)
