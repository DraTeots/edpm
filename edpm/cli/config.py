import click
from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.recipe import Recipe
from edpm.engine.output import markup_print as mprint


@click.command()
@click.argument('name_values', nargs=-1)
@pass_edpm_context
def config(ectx, name_values):
    """Sets build config for a packet

    If packet name is put, config goes into that packet. If no packet name is provided,
    config goes into global_config which affects all packet installations.

    Example:
        build_threads=4 jana branch=greenfield

    Explanation: global parameter 'build_threads' is set to 4, and 'jana' parameter  branch is set to 'greenfield'

    The example above is an extreme use case of this command and it is advised to split the contexts:
    >> edpm config build_threads=4
    >> edpm config jana branch=greenfield
    """

    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.load_db_if_exists()

    # We need at least some base configuration of recipes
    ectx.configure_recipes()

    if len(name_values) > 1:
        _set_configs(ectx, name_values)
    elif len(name_values) == 1:
        _show_configs(ectx, name_values[0])
    else:
        _show_configs(ectx, 'global')


def _show_configs(ectx, name):
    # get existing config
    if name == 'global':
        build_config = ectx.db.get_global_config()
    else:
        ectx.ensure_installer_known(name)
        build_config = ectx.db.get_config(name)

    mprint('<b><magenta>{}</magenta></b>:'.format(name))                      # pretty printing
    for param_name, value in build_config.items():
        mprint(' <b><blue>{}</blue></b>: {}'.format(param_name, value))

    # There is nothing more than 'global'
    if name == 'global':
        return

    mprint('<b><magenta>Default configs for {}</magenta></b>:'.format(name))  # pretty printing
    recipe = ectx.pm.recipes_by_name[name]
    assert isinstance(recipe, Recipe)

    for param_name, value in recipe.config.items():
        mprint(' <b><blue>{}</blue></b>: {}'.format(param_name, value))


def _set_configs(ectx, name_values):
    # Check that the packet name is from known packets
    config_blob = _process_name_values(name_values)

    for context_name in config_blob.keys():
        mprint('<b><magenta>{}</magenta></b>:'.format(context_name))  # pretty printing

        # get existing config
        if context_name == 'global':
            existing_config = ectx.db.get_global_config()
        else:
            ectx.ensure_installer_known(context_name)
            existing_config = ectx.db.get_config(context_name)

        updating_config = config_blob[context_name]

        existing_config.update(updating_config)  # update config
        ectx.db.save()  # save config

        # pretty printing the updated config
        for name, value in existing_config.items():
            mprint(' <b><blue>{}</blue></b>: {}'.format(name, value))


def _process_name_values(name_values):
    """Converts input parameters to a config map

    >>> _process_name_values(['build_threads=4', 'jana', 'branch=greenfield',  'build_threads=1'])
    {'global': {'build_threads': '4'}, 'jana': {'branch': 'greenfield', 'build_threads': '1'}}

    """

    context = 'global'
    result = {context: {}}

    for name_value in name_values:
        if '=' in name_value:
            name, value = tuple(name_value.split('=', 1))  # 1 as we want to split only the first occurrence
            result[context][name] = value
        else:
            context = name_value
            keys = list(result)
            if context not in keys:
                result[context] = {}

    # remove empty records:
    keys = list(result)   # to avoid RuntimeError: dictionary changed size during iteration
    for key in keys:
        if not result[key]:
            del result[key]

    return result
