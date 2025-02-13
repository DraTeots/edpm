import os
import click
import copy

from edpm.engine.api import pass_edpm_context, EdpmApi
from edpm.engine.db import PacketStateDatabase, BUILT_WITH_CONFIG
from edpm.engine.output import markup_print as mprint
from edpm.engine.recipe_manager import RecipeManager, InstallationRequest


@click.command()
@click.option('--missing', 'dep_mode', flag_value='missing', help="Installs only missing dependencies", default=True)
@click.option('--single', 'dep_mode', flag_value='single', help="Installs only this package")
@click.option('--force', 'dep_mode', flag_value='single', help="Force installation of a single package (same as --single)")
@click.option('--all', 'dep_mode', flag_value='all', help="Installs all dependencies by edpm")
@click.option('--path', 'install_path', default='', help="Is not implemented")
@click.option('--build-threads', '-j', 'build_threads', default=0, help="Build threads count")
@click.option('--explain', 'just_explain', default=False, is_flag=True, help="Prints what is to be installed (but do nothing)")
@click.option('--deps-only', 'deps_only', default=False, is_flag=True, help="Installs only dependencies but not the packet itself")
@click.argument('names', nargs=-1)
@pass_edpm_context
@click.pass_context
def install(ctx, ectx, dep_mode, names, install_path="", build_threads=4, just_explain=False, deps_only=False):
    """Installs packets (and all dependencies)

    \b
    Examples:
      > edpm install eicrecon --missing    # install eicrecon and all missing dependencies
      > edpm install rave --single      # install just rave package, dependencies are not checked
      > edpm install eicrecon --all        # install all eicrecon dependencies by edpm
                                        # even if user pointed some deps to external places

    \b
    --explain flag may be used to see what dependencies packet has and what is missing

      > edpm install eicrecon --missing --explain   # print what to be installed but not install

    """

    db = ectx.db
    pm = ectx.pm
    assert isinstance(ectx, EdpmApi)
    assert isinstance(db, PacketStateDatabase)
    assert isinstance(pm, RecipeManager)

    # Check if packet_name is all, missing or for known packet
    for name in names:
        ectx.ensure_installer_known(name)

    # Ok, looks like we are going to install something

    # If no db...
    if not db.exists():
        mprint("<green>creating database...</green>")
        db.save()

    # Lets check if we have top_dir
    if not db.top_dir:
        _print_help_no_top_path()
        raise click.Abort()

    # Install packets
    # set the tag we want to install
    requests = []
    for name in names:
        # make config overrides
        config = {}
        config.update(db.get_global_config())
        config.update(db.get_config(name))
        if build_threads:
            config['build_threads'] = build_threads

        # make installation request and add to the list
        request = InstallationRequest(pm.recipes_by_name[name], dep_mode, config, just_explain, deps_only)
        requests.append(request)

    for request in requests:
        _install_with_deps(ectx, request)

    # Update environment scripts if it is not just an explanation
    if not just_explain:
        mprint("Updating environment script files...\n")
        ectx.save_default_bash_environ()
        ectx.save_default_csh_environ()

    if ctx.invoked_subcommand is None:
        pass
        # click.echo('I was invoked without subcommand')
    else:
        pass
        # click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

def _build_deps_requests(ectx, initial_request):
    assert isinstance(initial_request, InstallationRequest)
    assert isinstance(ectx, EdpmApi)

    install_chain_names = ectx.pm.get_installation_chain_names(initial_request.name, initial_request.deps_only)

    requests = []                       # resulting InstallationRequests
    for name in install_chain_names:

        # Set installation mode to 'single' and 'deps_only' for all except initial request
        if name != initial_request.name:
            mode = 'single'
            deps_only = False
        else:
            mode = initial_request.mode
            deps_only = initial_request.deps_only

        config = {}
        config.update(ectx.db.get_global_config())
        config.update(ectx.db.get_config(name))
        config['build_threads'] = initial_request.config_overrides.get('build_threads', 4)

        # Create installation requrest

        request = InstallationRequest(ectx.pm.recipes_by_name[name],
                                      mode,
                                      config,
                                      initial_request.just_explain,
                                      deps_only)

        # Set right deirectory name in config overwrites
        request.config_overrides['app_path'] = os.path.join(ectx.db.top_dir, name)
        requests.append(request)
    return requests


def _install_packet(ectx, request):
    """Installs packet using its 'installation instruction' class"""

    assert isinstance(request, InstallationRequest)
    assert isinstance(ectx, EdpmApi)

    db = ectx.db
    install_path = os.path.join(db.top_dir, request.name)

    # set_app_path setups parameters (formats all string variables) for this particular path
    request.update_installer_config()
    request.recipe.setup(ectx.db)

    # Pretty header
    mprint("<magenta>=========================================</magenta>")
    mprint("<green> INSTALLING</green> : <blue>{}</blue>", request.name)
    mprint("<magenta>=========================================</magenta>\n")

    # (!) here we actually install the packet
    try:
        request.recipe.step_install()
    except OSError as err:
        mprint("<red>Installation stopped because of the error</red> : {}", err)
        exit(1)

    # if we are here, the packet is installed
    mprint("<green>{} installation step done!</green>\n", request.name)

    # Add to DB that we installed a packet
    mprint("Adding path to database...\n   This {} installation is set as <blue>selected</blue>", request.name)

    from edpm.engine.db import IS_OWNED, IS_ACTIVE, SOURCE_PATH, BUILD_PATH
    updating_data = {
        IS_OWNED: True,
        IS_ACTIVE: True,
        SOURCE_PATH: request.recipe.source_path,
        BUILD_PATH:  request.recipe.build_path,
        BUILT_WITH_CONFIG: request.recipe.config
    }
    db.update_install(request.recipe.name, request.recipe.install_path, updating_data)
    db.save()


def _install_with_deps(ectx, target_request):
    assert isinstance(target_request, InstallationRequest)
    assert isinstance(ectx, EdpmApi)

    try:
        must_exist_chain = _build_deps_requests(ectx, target_request)
    except KeyError as err:
        mprint("<red>Error finding one of the dependencies:</red>")
        print(err)
        exit(1)

    #
    # First. Hit 'setup' function on all dependencies.
    # This will allow us to build the right environment for nonexistent packets
    # If this is just a single packet install it will do no harm
    for request in must_exist_chain:
        # To call setup we need some installation path. Those are dependencies and we only know how to
        # install them to top_dir. So we don't care and set simple os.path.join(...)
        request.config_overrides['app_path'] = os.path.join(ectx.db.top_dir, request.name)
        request.update_installer_config()
        request.recipe.setup(ectx.db)

    #
    # Let's see what is missing and tell it to the user
    missing_chain = []
    mprint("\nCurrent status of the packet and dependencies:")
    for request in must_exist_chain:
        data = ectx.db.get_active_install(request.name)
        if not data:
            mprint("   <blue>{:<9}</blue> : not installed", request.name)
            missing_chain.append(request)
        else:
            is_owned_str = '(owned)' if data['is_owned'] else ''
            mprint("   <blue>{:<9}</blue> : {} {}", request.name, data['install_path'], is_owned_str)

    #
    # Select packets to install. mode tells what we should do with dependencies
    if target_request.mode == 'missing':
        # select only missing packets
        process_chain = [request for request in must_exist_chain if request in missing_chain]
    elif target_request.mode == 'single':
        # single = we only one packet
        process_chain = [target_request]
    elif target_request.mode == 'all':
        # all - we just overwrite everything
        process_chain = [request for request in must_exist_chain]
    else:
        raise NotImplementedError("installation dependencies mode is not in [missing, single, all]")

    #
    # Is there something to build?
    if not process_chain:
        mprint("Nothing to build and install!")
        return

    # Print user what is going to be built
    mprint("\n <b>INSTALLATION ORDER</b>:")
    for request in process_chain:
        mprint("   <blue>{:<6}</blue> : {}", request.name, request.recipe.install_path)

    # It is just explanation
    if target_request.just_explain:
        return

    # Set environment before build
    ectx.update_python_env(process_chain, target_request.mode)  # set environment spitting on existing missing

    #
    for request in process_chain:
        _install_packet(ectx, request)

def _print_help_no_top_path():
    mprint("<red>(!)</red> installation directory is not set <red>(!)</red>\n"
           "edpm doesn't know where to install missing packets\n\n"
           "<b><blue>what to do:</blue></b>\n"
           "  Provide the top dir to install things to:\n"
           "     edpm --top-dir=<path to top dir>\n"
           "  Less recommended. Provide each install command with --path flag:\n"
           "     edpm install <packet> --path=<path for packet>\n"
           "  (--path=... is not just where binary will be installed,\n"
           "   all related stuff is placed there)\n\n"

           "<b><blue>copy&paste:</blue></b>\n"
           "  to install missing packets in this directory: \n"
           "     edpm --top-dir=`pwd`\n\n"

           "  to install missing packets to your home directory: \n"
           "     edpm --top-dir=~/.eicrecon\n\n")