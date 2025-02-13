"""
Indirect Ray Tracing code for EPIC event reconstruction
https://github.com/eic/irt.git

"""

import os

from edpm.engine.env_gen import Prepend, Set, Append
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class IrtRecipe(GitCmakeRecipe):
    """Indirect Ray Tracing code for EPIC event reconstruction"""

    def __init__(self):
        super(IrtRecipe, self).__init__('irt')
        self.config['branch'] = 'v1.0.6'
        self.config['repo_address'] = 'https://github.com/eic/irt.git'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Prepend('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'IRT'))
        yield Prepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {}
