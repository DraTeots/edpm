"""
Algorithms library:
https://github.com/eic/algorithms

"""

import os

import platform
from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class AlgorithmsRecipe(GitCmakeRecipe):

    def __init__(self):

        # Set initial values for parent class and self
        super(AlgorithmsRecipe, self).__init__('algorithms')                 # This name will be used in edpm commands
        self.config['branch'] = 'algorithms-integration'                     # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://github.com/eic/algorithms'    # Repo address
        self.config['cmake_flags'] = ' '
        self.config['cxx_standard'] = 17

    def setup(self, db):
        # Call GitCmakeRecipe `default` setup function
        super(AlgorithmsRecipe, self).setup(db)

        # cmake command:
        # the  -Wno-dev  flag is to ignore the project developers cmake warnings for policy CMP0075
        self.build_cmd = "cmake -Wno-dev " \
                         "-DCMAKE_INSTALL_PREFIX={install_path} -DCMAKE_CXX_STANDARD={cxx_standard} " \
                         "{cmake_flags} {cmake_custom_flags} {source_path}/external/algorithms" \
                         "&& cmake --build . -- -j {build_threads}" \
                         "&& cmake --build . --target install" \
                         .format(**self.config)

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        install_path = data['install_path']

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(install_path, 'lib'))

        yield Append('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))


    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "libmsgsl-dev",
            'ubuntu22': "libmsgsl-dev",
            'centos7': "guidelines-support-library",
            'centos8': "guidelines-support-library",
        },
    }
