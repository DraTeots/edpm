# cli/config.py

import click
from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint


@click.command()
@click.argument('name_values', nargs=-1)
@click.pass_context
def config(ctx, name_values):
    """
    Sets or shows build config for dependencies or global config.

    Usage patterns:
      1) No arguments => show global config
      2) One argument  => show config for 'global' or that dependency
      3) Multiple arguments => set config

    Example to set global build_threads and set 'jana' branch:
      edpm config build_threads=4 jana branch=greenfield

    Explanation:
      - 'build_threads=4' goes into global config
      - 'jana' becomes a new context
      - 'branch=greenfield' is set in the 'jana' dependency config
    """

    # Ensure plan is loaded
    ectx = ctx.obj
    if not ectx.plan:
        ectx.load_manifest_and_lock("plan.edpm.yaml", "plan-lock.edpm.yaml")

    if len(name_values) == 0:
        # Show global config
        _show_configs(ectx, 'global')
    elif len(name_values) == 1:
        # Could be 'global' or a dependency name
        maybe_name = name_values[0]
        _show_configs(ectx, maybe_name)
    else:
        # parse them as set-commands
        _set_configs(ectx, name_values)


def _show_configs(ectx: EdpmApi, name: str):
    """
    Show configuration for either 'global' or a specific dependency.
    """
    if name == 'global':
        mprint("<b><magenta>global</magenta></b>:")
        for k, v in ectx.plan.global_config.items():
            mprint(" <b><blue>{}</blue></b>: {}", k, v)
        return

    # Otherwise, it’s a dependency name
    dep = ectx.plan.find_package(name)
    if not dep:
        mprint("<red>Error:</red> No dependency named '{}' in the plan.\n"
               "Create one with:\n  edpm config {} recipe=<recipe_name>\n", name, name)
        return

    # Print user-set config from the plan
    mprint("<b><magenta>{}</magenta></b>:", name)
    dep_dict = dep.to_dict()  # Fields like recipe, branch, cmake_flags, etc.
    for k, v in dep_dict.items():
        if k in ["name", "recipe"]:
            continue
        mprint(" <b><blue>{}</blue></b>: {}", k, v)

    mprint("\n<b><magenta>Recipe</magenta></b>: {}", dep.recipe)


def _set_configs(ectx: EdpmApi, name_values):
    """
    Parse multiple tokens of the form:
       global build_threads=4
       root branch=greenfield ...
    Then update the plan accordingly.
    """
    # parse them into { context_name -> {param: value, ...} }
    config_blob = _process_name_values(name_values)

    # For each context, update either 'plan.global_config' or a dependency
    for context_name, kvpairs in config_blob.items():
        if context_name == 'global':
            _update_global_config(ectx, kvpairs)
        else:
            _update_dep_config(ectx, context_name, kvpairs)

    # Save the plan so changes persist
    ectx.plan.save("plan.edpm.yaml")


def _update_global_config(ectx: EdpmApi, kvpairs: dict):
    """
    Merge fields into ectx.plan.global_config
    """
    mprint("<b><magenta>global</magenta></b>:")
    for k, v in kvpairs.items():
        ectx.plan.global_config[k] = v

    # show final
    for k, v in ectx.plan.global_config.items():
        mprint(" <b><blue>{}</blue></b>: {}", k, v)


def _update_dep_config(ectx: EdpmApi, dep_name: str, kvpairs: dict):
    """
    1) If the dependency doesn't exist:
       - If 'recipe' is in kvpairs, create a new dependency with that recipe.
       - Otherwise, error out.
    2) Merge param=val into that dependency's fields (branch, cmake_flags, etc.).
    3) Show final result.
    """
    dep = ectx.plan.find_package(dep_name)
    if not dep:
        # Possibly the user is creating a brand-new dependency
        recipe = kvpairs.get("recipe", None)
        if not recipe:
            mprint("<red>Error:</red> No dependency named '{}' in the plan, and no 'recipe=...' provided.\n"
                   "Please do:\n  edpm config {} recipe=<recipe_name>\n", dep_name, dep_name)
            return
        # Create new dependency
        ectx.plan.add_dependency(name=dep_name, recipe=recipe)

        # Now that it’s created, retrieve it
        dep = ectx.plan.find_package(dep_name)

    # Now dep exists, merge fields
    # e.g. if kvpairs has branch=..., we do dep.branch = ...
    # or if kvpairs has cxx_standard=..., we do dep.cxx_standard=...
    # Implementation depends on your DependencyEntry structure
    # We'll just set them in dep._raw_data or so. For demonstration:
    for k, v in kvpairs.items():
        if k == "recipe":
            dep.recipe = v
        elif hasattr(dep, k):
            setattr(dep, k, v)
        else:
            # Maybe put it in the underlying dict if you have a generic approach
            dep._raw_data[k] = v

    # Show final
    mprint("<b><magenta>{}</magenta></b>:", dep_name)
    final_dict = dep.to_dict()
    for k, v in final_dict.items():
        if k in ["name"]:
            continue
        mprint(" <b><blue>{}</blue></b>: {}", k, v)


def _process_name_values(name_values):
    """
    Converts input parameters to a config map of the form:
      {
        context_name: {param_name: param_value, ...},
        ...
      }

    If we see a token with '=', we treat it as param=value for the current context.
    If we see a token WITHOUT '=', it is a new context name.

    Example:
      _process_name_values(["build_threads=4", "jana", "branch=greenfield", "build_threads=1"])
      => {"global": {"build_threads": "4"}, "jana": {"branch": "greenfield", "build_threads": "1"}}
    """
    context = 'global'
    result = {context: {}}

    for nv in name_values:
        if '=' in nv:
            param, val = nv.split('=', 1)
            result[context][param] = val
        else:
            # Switch context
            context = nv
            if context not in result:
                result[context] = {}

    # Remove empty records if any
    empty_keys = [k for k, v in result.items() if not v]
    for ek in empty_keys:
        if ek != 'global':  # Usually we keep 'global' even if empty
            del result[ek]

    return result
