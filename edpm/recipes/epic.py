"""
EPIC DD4Hep geometry repository
"""

import os

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.git_cmake_recipe import GitCmakeRecipe


class EpicRecipe(GitCmakeRecipe):


    def __init__(self):

        # Set initial values for parent class and self
        super(EpicRecipe, self).__init__('epic')    # This name will be used in edpm commands
        self.required_deps = ['clhep', 'eigen3', 'root', 'hepmc3', 'podio', 'edm4hep', 'edm4eic', 'geant4','dd4hep', 'acts', 'actsdd4hep', 'actssvg']
        self.config['branch'] = '23.08.0'                             # The branch or tag to be cloned (-b flag)
        self.config['repo_address'] = 'https://github.com/eic/epic'

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
        yield Set('DETECTOR_PATH', os.path.join(path, 'share', 'epic'))
        yield Set('BEAMLINE', 'epic')
        yield Set('BEAMLINE_PATH', os.path.join(path, 'share', 'epic'))
        yield Set('BEAMLINE_CONFIG', 'epic')

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu': 'libfmt-dev'
        },
        'optional': {},
    }
