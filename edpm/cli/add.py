import click
import os
from edpm.engine.output import markup_print as mprint
from edpm.engine.api import EdpmApi

# Maps a recipe type to a list of (argument_name, config_key) pairs
# telling us how to interpret positional arguments.
#
# Example:
#   "manual": [("location", "location")]
#     -> For "manual", the first positional argument is stored in config["location"].
#
#   "git-cmake": [("repo", "repo_address")]
#     -> For "git-cmake", the first positional argument is stored in config["repo_address"].
# You can add more advanced logic or multiple arguments if needed.
RECIPE_POSITIONAL_MAP = {
    "manual": [("location", "location")],
    "git-cmake": [("repo", "repo_address")],
    # Add more if needed:
    # "git-automake": [("repo", "repo_address")]
    # "pip-install":  [("package", "package_name")]
}

@click.command()
@click.option("-t", "--type", "recipe_type", default="",
              help="The recipe type (e.g. manual, git-cmake). If omitted, the first argument is used as both 'name' and 'recipe' if recognized.")
@click.option("--branch", default="", help="Shortcut for config.branch=... (common for git-based recipes).")
@click.option("--location", default="", help="Shortcut for config.location=... (common for manual recipes).")
@click.option("--repo", default="", help="Shortcut for config.repo_address=... (common for git-based recipes).")
@click.option("--option", "option_list", multiple=True, help="Arbitrary key=value pairs that go into config. E.g. --option cxx_standard=20.")
@click.argument("name", required=True)
@click.argument("extra_args", nargs=-1, required=False)
@click.pass_context
def add(ctx, recipe_type, branch, location, repo, option_list, name, extra_args):
    """
    Add a new dependency to the EDPM manifest without installing it.

    Examples:
      edpm add root
         -> Adds a 'root' recipe with name='root'.

      edpm add --type=manual my_root /home/user/root45
         -> Adds a 'manual' recipe named 'my_root', config.location=/home/user/root45

      edpm add --type=git-cmake fmt https://github.com/fmtlib/fmt.git --branch=11.1.3
         -> Adds a 'git-cmake' recipe named 'fmt', config.repo_address=..., config.branch=11.1.3
    """
    api = ctx.obj
    assert isinstance(api, EdpmApi)

    # 2) If --type not given, we guess the user typed something like "root",
    #    meaning name="root" + recipe="root".
    #    We'll check if "root" is recognized by the manager as a known recipe.
    if not recipe_type:
        # If 'name' is recognized as a known recipe name:
        known = api.pm.recipes_by_name.keys()
        if name in known:
            recipe_type = name
        else:
            mprint(
                "<red>No --type provided and '{}' is not a known recipe name.</red>\n"
                "Please specify, e.g. '--type=manual' or another known type.",
                name
            )
            return

    # 3) Build the new dependency data
    new_dep = {
        "recipe": recipe_type,  # e.g. "manual", "git-cmake", "root", etc.
        "name": name,
        "config": {},
        "environment": [],
        "external-requirements": {}
    }

    # 4) Map positional arguments if any
    #    e.g. for "manual", we expect one arg => config["location"] = that arg
    #         for "git-cmake", we expect one arg => config["repo_address"] = that arg
    recipe_pos_map = RECIPE_POSITIONAL_MAP.get(recipe_type, [])
    if recipe_pos_map:
        # For each (arg_label, config_key) pair, if we have a positional arg, assign it
        for i, (arg_label, cfg_key) in enumerate(recipe_pos_map):
            if i < len(extra_args):
                new_dep["config"][cfg_key] = extra_args[i]
        # If user gave more than what's needed, you might store them in a leftover or warn them

    # 5) Apply shortcut flags: --branch, --location, --repo
    if branch:
        new_dep["config"]["branch"] = branch
    if location:
        new_dep["config"]["location"] = location
    if repo:
        new_dep["config"]["repo_address"] = repo

    # 6) Parse --option multiple key=value pairs
    #    e.g. --option cxx_standard=20 => new_dep["config"]["cxx_standard"] = "20"
    for opt in option_list:
        if "=" in opt:
            k, v = opt.split("=", 1)
            new_dep["config"][k.strip()] = v.strip()
        else:
            mprint("<red>Ignoring malformed --option '{}'. Expected key=value.</red>", opt)

    # 7) Check if name already exists in the manifest
    if api.manifest.has_dependency(name):
        mprint("<red>Error:</red> A dependency named '{}' already exists in the manifest.", name)
        return

    # 8) Actually add it to the manifest
    api.manifest.data["dependencies"].append(new_dep)

    # 9) Save the manifest
    api.manifest.save(api.manifest_file)

    mprint("<green>Added dependency '{}</green>' with recipe='{}'.\nCheck package.edpm.yaml to customize further.",
           name, recipe_type)
