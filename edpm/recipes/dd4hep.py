"""
This file provides information of how to build and configure HepMC framework:
https://github.com/AIDASoft/DD4hep
"""

import os
import platform

from edpm.engine import env_gen
from edpm.engine.commands import run, workdir
from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe



class DD4HEPRecipe(GitCmakeRecipe):
    """Provides data for building and installing HepMC framework
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        """
        Installs Genfit track fitting framework
        """

        # Set initial values for parent class and self
        super(DD4HEPRecipe, self).__init__('dd4hep')

        self.config['branch'] = 'v01-28'
        self.config['repo_address'] = 'https://github.com/AIDASoft/DD4hep.git'
        self.config['cmake_flags'] = ' -DDD4HEP_USE_GEANT4=ON -DDD4HEP_USE_EDM4HEP=ON -DDD4HEP_USE_LCIO=OFF '

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""

        """Generates environments to be set

        This function is a bit more tricky than usual - RawText are going to be used.
        RawText actually allows to:
         1. wright a custom text for sh and csh environment scripts
         2. and run a python command to set the environment

        For bash and csh one wants to run 'source .../thisdd4hep_only.sh[csh]'
        But also, one must be set the environment inside python.
        When building Geant from scratch and there is no thisdd4hep_only.sh[csh] yet
        update_python_environment() - do this

        """

        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        lib_path = os.path.join(install_path, 'lib')        # on some platforms
        include_path = os.path.join(install_path, 'include')        # on some platforms
        cmake_path = os.path.join(install_path, 'cmake')

        # The next is about conda
        # in conda thisdd4hep_only.sh triggers error explaining, that everything is already done in activate
        # so we don't need to put thisdd4hep_only if we acting under conda
        # this is hacky hack
        is_under_conda = 'DD4HEP_INSTALLED_BY_CONDA' in os.environ

        def update_python_environment():
            """Function that will update Geant environment in python build step
            We need this function because we DON'T want to source geant4.sh in python
            """
            env_updates = [
                env_gen.Append('LD_LIBRARY_PATH', lib_path),
                env_gen.Append('CMAKE_PREFIX_PATH', cmake_path),
                env_gen.Append('ROOT_INCLUDE_PATH', include_path),   # So that rootcling could find it
            ]

            if platform.system() == 'Darwin':
                env_updates.append(env_gen.Append('DYLD_LIBRARY_PATH', lib_path))

            for updater in env_updates:
                updater.update_python_env()

        # We just call geant4.sh in different shells
        yield Prepend('PATH', bin_path)  # to make available clhep-config and others

        # We just call thisroot.xx in different shells
        bash_thisdd4hep_path = os.path.join(bin_path, 'thisdd4hep_only.sh')
        bash_text = '\n' \
                    'if [[ -z "$DD4HEP_INSTALLED_BY_CONDA" ]]; then \n' \
                    '   if test -f "{0}"; then \n' \
                    '      source {0}; \n' \
                    '   fi\n' \
                    'fi\n'.format(bash_thisdd4hep_path)


        # in Geant CSH script Geant asks to get a path for geant bin directory
        csh_text = 'echo "WARNING(!) DD4HEP requires bash to setup environment variables'

        yield env_gen.RawText(
            bash_text,
            csh_text,
            update_python_environment
        )

        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        yield Prepend('PATH', bin_path)  # to make available clhep-config and others
        yield Set('DD4HEP_DIR', install_path)


        yield Append('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu18': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu18': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {}
