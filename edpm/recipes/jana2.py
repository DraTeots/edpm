"""
This file provides information of how to build and configure JANA2 packet:
https://github.com/JeffersonLab/JANA2

"""

import os

from edpm.engine.commands import run, workdir, env
from edpm.engine.env_gen import Prepend, Set, Append
from edpm.engine.git_cmake_recipe import GitCmakeRecipe
from edpm.engine.recipe import Recipe


class JanaRecipe(GitCmakeRecipe):
    """Provides data for building and installing JANA2 framework

    PacketInstallationInstruction is located in recipe.py and contains the next standard package variables:


    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        super(JanaRecipe, self).__init__('jana2')
        self.config['branch'] = 'master'
        self.config['repo_address'] = 'https://github.com/JeffersonLab/JANA2.git'
        self.config['cmake_flags'] = '-DUSE_ROOT=On -DUSE_PYTHON=Off -DUSE_PODIO=On'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""

        install_path = data['install_path']

        yield Set('JANA_HOME', install_path)
        yield Append('JANA_PLUGIN_PATH', '$JANA_HOME/plugins')
        yield Prepend('PATH', '$JANA_HOME/bin')
        yield Prepend('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))
        yield Prepend('CMAKE_PREFIX_PATH', os.path.join(install_path, 'lib', 'cmake', 'JANA'))

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "libxerces-c-dev curl python3-dev",
            'ubuntu22': "libxerces-c-dev curl python3-dev",
            'centos7': "xerces-c-devel curl",
            'centos8': "xerces-c-devel curl"
        },
        'optional': {},
    }
