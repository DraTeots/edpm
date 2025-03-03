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
              help="Arbitrary key=value pairs to add under the dependency config. E.g. --option cxx_standard=17.")
@click.argument("name", required=True)
@click.pass_context
def add_command(ctx, name, fetch, make, branch, location, url, option_list):
    """
    Updates the plan.edpm.yaml "packages" list to include a new entry.
    If no extra flags and 'name' is a known built-in recipe, we add it as a simple '- name'.
    Otherwise, we create a dictionary entry of the form:

        - name:
            fetch: ...
            make: ...
            <other fields>

    """
    api = ctx.obj  # Or however you typically instantiate the EdpmApi


    # 1) Check if 'name' already exists in the plan
    if api.plan.has_package(name):
        mprint("<red>Error:</red> A package named '{}' already exists in the plan.", name)
        raise click.Abort()

    # 2) Decide if we can add this as a simple string ("- root") or need a dict
    is_known_recipe = name in api.recipe_manager.recipes_by_name
    has_any_flags = any([fetch, make, branch, location, url, option_list])

    # If no flags, no extra config, and 'name' is a known built-in recipe => just "- name"
    if (not has_any_flags) and is_known_recipe:
        new_entry = name  # e.g.   packages: [ - root ]
    else:
        # Otherwise produce a dictionary entry:   packages: [ - name: {...} ]
        new_entry = {name: {}}
        config_block = new_entry[name]  # fill in fetch/make/etc.

        # Populate fetch
        if fetch:
            config_block["fetch"] = fetch
        elif url:
            # if user only gave --url, guess the fetcher
            # e.g. if ends with ".git", we treat it as "git"
            # if ends with ".tar.gz", treat it as "tarball"
            # or fallback to "git" if user says so.
            if url.endswith(".git"):
                config_block["fetch"] = "git"
            elif url.endswith(".tar.gz") or url.endswith(".tgz"):
                config_block["fetch"] = "tarball"
            else:
                config_block["fetch"] = "filesystem"  # or guess
        # If user gave neither 'fetch' nor 'url', you could leave it empty or default to manual.

        # Populate 'url' or 'location' field if provided
        if url:
            config_block["url"] = url
        if location:
            config_block["location"] = location

        # Populate make
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

    # 3) Append the new entry to the plan
    api.plan.data["packages"].append(new_entry)

    # 4) Save the plan
    api.plan.save(api.plan_file)

    # 5) Inform the user
    mprint("<green>Added dependency</green> '{}' to the plan.\nCheck '{}' to see or edit details.",
           name, api.plan_file)
