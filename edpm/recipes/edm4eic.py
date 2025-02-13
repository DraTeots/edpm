"""
EIC Event data model extension
https://github.com/eic/edm4eic.git
"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class Edm4EicRecipe(GitCmakeRecipe):
    """"""

    def __init__(self):
        """
        Installs Eic Data framework
        """

        # Set initial values for parent class and self
        super(Edm4EicRecipe, self).__init__('edm4eic')                        # This name will be used in edpm commands
        self.config['branch'] = 'v3.0.1'                                # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://github.com/eic/edm4eic.git'    # Repo address
        self.config['cmake_flags'] = '-DBUILD_DATA_MODEL=ON'
        self.config['cxx_standard'] = 17

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Set('EICD_ROOT', path)

        # it could be lib or lib64. There are bugs on different platforms (RHEL&centos and WSL included)
        # https://stackoverflow.com/questions/46847939/config-site-for-vendor-libs-on-centos-x86-64
        # https: // bugzilla.redhat.com / show_bug.cgi?id = 1510073

        import platform
        if platform.system() == 'Darwin':
            if os.path.isdir(os.path.join(path, 'lib64')):
                yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib64'))
            else:
                yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        if os.path.isdir(os.path.join(path, 'lib64')):
            yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib64'))
        else:
            yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'EDM4EIC'))


    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "",
            'ubuntu22': "",
            'centos7': "",
            'centos8': "",
        },
        'optional': {},
    }