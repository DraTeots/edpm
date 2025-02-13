"""
This file provides information of how to build and configure CLHEP library:
https://gitlab.cern.ch/CLHEP/CLHEP

"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class ClhepRecipe(GitCmakeRecipe):
    """Provides data for building and installing CLHEP framework
    """

    def __init__(self):
        # Set initial values for parent class and self
        super(ClhepRecipe, self).__init__('clhep')
        self.clone_command = ''             # will be set by self.set_app_path
        self.build_cmd = ''                 # will be set by self.set_app_path
        self.config['branch'] = 'CLHEP_2_4_6_4'
        self.config['repo_address'] = 'https://gitlab.cern.ch/CLHEP/CLHEP.git'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""

        path = data['install_path']
        lib_path = os.path.join(path, 'lib')
        include_path = os.path.join(path, 'include')
        bin_path = os.path.join(path, 'bin')

        yield Set('CLHEP', path)
        yield Set('CLHEP_BASE_DIR', path)                  # Some system look for CLHEP this way
        yield Set('CLHEP_INCLUDE_DIR', include_path)  # or /usr/include/CLHEP/
        yield Set('CLHEP_LIB_DIR', lib_path)

        yield Prepend('PATH', bin_path)  # to make available clhep-config and others
        yield Prepend('LD_LIBRARY_PATH', lib_path)

        # set DYLD_LIBRARY_PATH for mac
        import platform
        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', lib_path)

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "cmake",
            'ubuntu22': "cmake",
            'centos7': "cmake",
            'centos8': "cmake"
        },
        'optional': {},
    }
