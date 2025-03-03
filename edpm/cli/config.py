import click

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint

@click.command()
@click.argument('name_values', nargs=-1)
@click.pass_context
def config(ctx, name_values):
    """
    Show or set build config for 'global' or for a specific dependency.

    Usage patterns:
      1) `edpm config` with no args => Show all global config
      2) `edpm config <depName>` => Show config for that dependency
      3) `edpm config key=val [depName key=val ...]` => Set global or per-dep config

    Examples:
      edpm config build_threads=4 cxx_standard=17
        => sets these two keys in global config

      edpm config root branch=master
        => sets 'branch=master' in the 'root' dependency

      edpm config
        => shows global config
      edpm config root
        => shows config for 'root' dependency
    """

    api = ctx.obj  # EdpmApi from click context
    api.load_all()

    if len(name_values) == 0:
        # Show global config
        _show_global_config(api)
        return

    if len(name_values) == 1 and '=' not in name_values[0]:
        # E.g. "edpm config root"
        dep_name = name_values[0]
        if dep_name == "global":
            _show_global_config(api)
        else:
            _show_dep_config(api, dep_name)
        return

    # Otherwise we treat them as "set" commands
    _set_configs(api, name_values)
    api.plan.save(api.plan_file)
    mprint("<green>Saved changes to</green> {}", api.plan_file)


def _show_global_config(api: EdpmApi):
    """
    Prints the keys under plan.data["global"]["config"].
    """
    plan_data = api.plan.data
    glob_cfg = plan_data.get("global", {}).get("config", {})
    mprint("<b><magenta>Global Config</magenta></b>:")
    if not glob_cfg:
        mprint("  <yellow>No global config found.</yellow>")
    else:
        for k, v in glob_cfg.items():
            mprint("  <b><blue>{}</blue></b>: {}", k, v)


def _show_dep_config(api: EdpmApi, dep_name: str):
    """
    Finds the given dependency in plan.data["packages"] and shows its dictionary fields.
    If it's just a string (like 'root'), we show that info.
    """
    entry = _find_package_entry(api, dep_name)
    if entry is None:
        mprint("<red>Error:</red> No dependency named '{}' in the plan.\n"
               "Try: edpm add {}  or set a recipe: edpm config {} recipe=<recipeName>", dep_name, dep_name, dep_name)
        return

    # If entry is just a string (like 'root'), show that
    if isinstance(entry, str):
        mprint("<magenta>'{}'</magenta> is currently just a simple entry.\n"
               "No custom config is stored for it. (Built-in recipe name: '{}')", dep_name, entry)
        return

    # Otherwise it's a dict like { depName: {...} }
    if isinstance(entry, dict):
        # entry looks like:  "mydep: { fetch: 'git', ... }"
        # So the top-level key is dep_name
        dep_data = entry.get(dep_name, {})
        mprint("<b><magenta>{}</magenta></b> config:", dep_name)
        if not dep_data:
            mprint("  <yellow>No fields set yet.</yellow>")
        else:
            for k, v in dep_data.items():
                mprint("  <b><blue>{}</blue></b>: {}", k, v)
    else:
        mprint("<red>Error:</red> Unexpected entry type for '{}'. Plan data might be malformed.", dep_name)


def _set_configs(api: EdpmApi, tokens):
    """
    Processes user tokens like:
      "build_threads=4"
      "cxx_standard=17"
      "root branch=master build_threads=2"

    We parse them into a structure of { context: {k: v, ...}, ... }.
    Then for each context, we update either:
      - global config, or
      - the named dependency

    *Important*: This approach matches the older pattern of "global" until we see a new token w/o '='.
    """
    groups = _process_tokens_into_contexts(tokens)

    plan_data = api.plan.data
    global_cfg = plan_data.setdefault("global", {}).setdefault("config", {})

    for context_name, kvs in groups.items():
        if context_name == "global":
            # merge into plan_data["global"]["config"]
            for k, v in kvs.items():
                global_cfg[k] = v
            mprint("<b>Updated global config:</b>")
            for k, val in global_cfg.items():
                mprint("  {} = {}", k, val)
        else:
            # update a dependency
            _update_dep_config(api, context_name, kvs)


def _update_dep_config(api: EdpmApi, dep_name: str, kvs: dict):
    """
    - If 'dep_name' doesn't exist, we require 'recipe=...' or we show an error.
    - If 'dep_name' is a string, convert it to a dict with 'recipe=<that string>'.
    - Finally, merge kvs into the dict.
    """
    packages = api.plan.data.setdefault("packages", [])

    idx, existing_entry = _find_package_entry_with_index(api, dep_name, return_index=True)

    if existing_entry is None:
        # Creating brand-new dependency => must have recipe=...
        recipe_val = kvs.get("recipe", None)
        if not recipe_val:
            # Show the error the test expects
            mprint("<red>No dependency named '{}' in the plan, and no 'recipe=...' provided.</red>", dep_name)
            return
        # Otherwise, create new dictionary
        new_dict = {dep_name: {"recipe": recipe_val}}
        packages.append(new_dict)
        idx = len(packages) - 1
        existing_entry = new_dict

    # If existing entry is a string, convert it
    if isinstance(existing_entry, str):
        # e.g. "root" => { "root": {"recipe": "root"} }
        new_dict = {dep_name: {"recipe": existing_entry}}
        packages[idx] = new_dict
        existing_entry = new_dict

    # Now we have a dict: { dep_name: {...} }
    if isinstance(existing_entry, dict):
        dep_dict = existing_entry.setdefault(dep_name, {})
        # Merge kvs
        for k, v in kvs.items():
            dep_dict[k] = v

        mprint("<b>Updated config for <magenta>{}</magenta>:</b>", dep_name)
        for kk, vv in dep_dict.items():
            mprint("  {} = {}", kk, vv)


def _process_tokens_into_contexts(tokens):
    """
    Given something like:
      ["build_threads=4", "root", "branch=master", "build_threads=2", "mylib", "url=https://..."]

    We interpret everything until we hit a token w/o '=' as belonging to 'global' context, then switch context.

    Returns a dict of form:
      {
        "global": {"build_threads": "4"},
        "root":   {"branch": "master", "build_threads": "2"},
        "mylib":  {"url": "https://..."}
      }

    """
    result = {}
    current_context = "global"
    result[current_context] = {}

    for token in tokens:
        if '=' in token:
            # param=value
            param, val = token.split('=', 1)
            result[current_context][param] = val
        else:
            # new context
            current_context = token
            if current_context not in result:
                result[current_context] = {}

    # Clean out empty contexts if needed
    # (We generally keep 'global' even if empty)
    return result


def _find_package_entry(api: EdpmApi, dep_name: str):
    """
    Returns the plan 'packages' entry (string or dict) that matches 'dep_name', or None if not found.

    The plan might have an item like:
      - root
      - root: { recipe: "root", branch: "main" }
      - mylib: { fetch: "git", ... }
    """
    packages = api.plan.data.get("packages", [])
    for item in packages:
        # item can be a string (e.g. "root") or a dict like { "root": {...} }
        if isinstance(item, str):
            if item == dep_name:
                return item
        elif isinstance(item, dict):
            # If there's exactly one key, compare it to dep_name
            # or for safety we can check if dep_name is in item
            if dep_name in item.keys():
                return item
    return None


def _find_package_entry_with_index(api: EdpmApi, dep_name: str, return_index=False):
    """
    Same as _find_package_entry but also returns the index in the packages list if found,
    so we can modify it in place.
    """
    packages = api.plan.data.setdefault("packages", [])
    for i, item in enumerate(packages):
        if isinstance(item, str):
            if item == dep_name:
                return (i, item) if return_index else item
        elif isinstance(item, dict):
            if dep_name in item:
                return (i, item) if return_index else item
    return (None, None) if return_index else None
