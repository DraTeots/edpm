"""
This file provides information of how to build and configure Eigen3 packet:
https://github.com/nathanwbrei/phasm

"""

import os

from edpm.engine.env_gen import Prepend, Set, Append
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class PhasmRecipe(GitCmakeRecipe):
    """Provides data for building and installing Eicgen3 framework"""

    def __init__(self):
        super(PhasmRecipe, self).__init__('phasm')
        self.config['branch'] = 'master'
        self.config['repo_address'] = 'https://github.com/nathanwbrei/phasm'

    def setup(self, db):
        """Sets all variables like source dirs, build dirs, etc"""

        #
        # use_common_dirs_scheme sets standard package variables:
        # source_path  = {app_path} / src   / {branch}       # Where the sources for the current version are located
        # build_path   = {app_path} / build / {branch}       # Where sources are built. Kind of temporary dir
        # install_path = {app_path} / geant-{branch}         # Where the binary installation is
        self.use_common_dirs_scheme()
        print("Sorry Nathan! I haven't put all the deps yet!")
        exit(1)
        super(PhasmRecipe, self).setup()

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Prepend('CMAKE_PREFIX_PATH', os.path.join(path, 'share/eigen3/cmake/'))

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
