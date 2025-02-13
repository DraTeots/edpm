"""
This file provides information of how to build and configure HepMC framework:
https://gitlab.cern.ch/hepmc/HepMC3
"""

import os

from edpm.engine.commands import run, workdir, env
from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class HepMC3Recipe(GitCmakeRecipe):
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
        super(HepMC3Recipe, self).__init__('hepmc3')

        self.config['branch'] = '3.2.6'
        self.config['repo_address'] = 'https://gitlab.cern.ch/hepmc/HepMC3.git'
        self.config['cmake_flags'] = ' -DHEPMC3_ENABLE_ROOTIO=OFF -DHEPMC3_ENABLE_PYTHON=OFF -DHEPMC3_BUILD_EXAMPLES=OFF HEPMC3_CXX_STANDARD=17'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""

        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        yield Prepend('PATH', bin_path)  # to make available clhep-config and others
        yield Set('HEPMC3_DIR', install_path)


        yield Append('CMAKE_PREFIX_PATH', os.path.join(install_path, 'share', 'HepMC3', 'cmake'))

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {},
        'optional': {},
    }