"""
PodIO
https://github.com/AIDASoft/podio.git
"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class PodioRecipe(GitCmakeRecipe):
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
        super(PodioRecipe, self).__init__('podio')                        # This name will be used in edpm commands
        self.config['branch'] = 'v00-17-04'                               # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://github.com/AIDASoft/podio.git'    # Repo address
        self.config['cmake_flags'] = '-DBUILD_TESTING=OFF'
        self.config['cxx_standard'] = 17

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Set('PODIO_ROOT', path)

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

        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'podio'))


    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "python3-jinja2 python3-yaml",
            'ubuntu22': "python3-jinja2 python3-yaml",
            'centos7': "",
            'centos8': "",
        },
        'optional': {},
    }