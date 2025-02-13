"""
This file provides information of how to build and configure ACTS framework:
https://gitlab.cern.ch/acts/acts-core
"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class ActsRecipe(GitCmakeRecipe):
    """Provides data for building and installing Genfit framework
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        """
        Installs Genfit track fitting framework
        """

        # Set initial values for parent class and self
        super(ActsRecipe, self).__init__('acts')                        # This name will be used in edpm commands
        self.config['branch'] = 'v31.2.0'                               # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://github.com/acts-project/acts'    # Repo address
        self.config['cmake_flags'] = '-DACTS_BUILD_PLUGIN_TGEO=ON -DACTS_BUILD_PLUGIN_DD4HEP=ON -DACTS_BUILD_PLUGIN_JSON=ON -DACTS_BUILD_PLUGIN_ACTSVG=OFF'
        self.config['cxx_standard'] = 17

    def setup(self, db):
        # ACTS require C++14 (at least). We  check that it is set
        if int(self.config['cxx_standard']) < 17:
            message = "ERROR. cxx_standard must be 17 or above to build ACTS.\n"\
                      "To set cxx_standard globally:\n"\
                      "   edpm config global cxx_standard=17\n"\
                      "To set cxx_standard for acts:\n"\
                      "   edpm config acts cxx_standard=17\n"\
                      "(!) Make sure cmake is regenerated after. (rm <top_dir>/acts and run edpm install acts again)\n"
            raise ValueError(message)

        print(self.config['branch'])
        # Call GitCmakeRecipe `default` setup function
        super(ActsRecipe, self).setup(db)

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Set('ACTS_DIR', path)

        # it could be lib or lib64. There are bugs on different platforms (RHEL&centos and WSL included)
        # https://stackoverflow.com/questions/46847939/config-site-for-vendor-libs-on-centos-x86-64
        # https: // bugzilla.redhat.com / show_bug.cgi?id = 1510073

        import platform
        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # share/cmake/Acts
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'Acts'))
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'nlohmann_json'))
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'ActsDD4hep'))


    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "libboost-dev libboost-filesystem-dev libboost-program-options-dev libboost-test-dev nlohmann-json3-dev",
            'ubuntu22': "libboost-dev libboost-filesystem-dev libboost-program-options-dev libboost-test-dev nlohmann-json3-dev",
            'centos7': "boost-devel",
            'centos8': "boost-devel",
        },
    }