"""
Nuclear Physics Detectors library
https://eicweb.phy.anl.gov/EIC/NPDet.git
"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class NpDetRecipe(GitCmakeRecipe):
    """Provides data for building and installing NPDet librarty
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        """
        Installs Genfit track fitting framework
        """

        # Set initial values for parent class and self
        super(NpDetRecipe, self).__init__('npdet')    # This name will be used in edpm commands
        self.required_deps = ['eigen3', 'hepmc3', 'root', 'geant4', 'dd4hep']
        self.config['branch'] = 'master'                             # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://eicweb.phy.anl.gov/EIC/NPDet.git'

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        # it could be lib or lib64. There are bugs on different platforms (RHEL&centos and WSL included)
        # https://stackoverflow.com/questions/46847939/config-site-for-vendor-libs-on-centos-x86-64
        # https: // bugzilla.redhat.com / show_bug.cgi?id = 1510073

        # yield Prepend('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake'))
        yield Prepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield Prepend('PATH', os.path.join(path, 'bin'))

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "libspdlog-dev libocct-foundation-dev occt-misc libocct-draw-dev libocct-data-exchange-dev libfmt-dev libtbb-dev",
            'ubuntu22': "libspdlog-dev libocct-foundation-dev occt-misc libocct-draw-dev libocct-data-exchange-dev libfmt-dev libtbb-dev",
        },
        'optional': {},
    }