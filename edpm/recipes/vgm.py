"""
This file provides information of how to build and configure VMC framework:
Geometry conversion tool, providing conversion between Geant4 and ROOT TGeo geometry models.

https://github.com/vmc-project/vgm


"""

import os

from edpm.engine.commands import run, workdir
from edpm.engine.env_gen import Set, Append
from edpm.engine.git_cmake_recipe import GitCmakeRecipe
from edpm.engine.recipe import Recipe


class VgmRecipe(GitCmakeRecipe):
    """Provides data for building and installing Geant4 framework
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        """
        Installs Genfit track fitting framework
        """

        # Set initial values for parent class and self
        super(VgmRecipe, self).__init__('vgm')
        self.config['branch'] = 'v4-5'
        self.config['cmake_flags'] = '-DWITH_EXAMPLES=0'
        self.config['repo_address'] = 'https://github.com/vmc-project/vgm'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""

        install_path = data['install_path']
        yield Set('VGM_DIR', install_path)

        import platform
        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(install_path, 'lib'))
            yield Append('DYLD_LIBRARY_PATH', os.path.join(install_path, 'lib64'))

        yield Append('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))
        yield Append('LD_LIBRARY_PATH', os.path.join(install_path, 'lib64'))

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu': "",
            'centos': ""
        },
        'optional': {
            'ubuntu': "",
            'centos': ""
        },
    }
