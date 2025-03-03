"""
Nuclear Physics Detectors library
https://eicweb.phy.anl.gov/EIC/NPDet.git
"""
import os
import platform

from edpm.engine.generators.steps import EnvPrepend
from edpm.engine.composed_recipe import ComposedRecipe


class NpDetRecipe(ComposedRecipe):
    """
    Installs npdet from Git + CMake (for NP detectors).
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://eicweb.phy.anl.gov/EIC/NPDet.git',
            'branch': 'v1.4.1'
        }
        super().__init__(name='npdet', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        yield EnvPrepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield EnvPrepend('PATH', os.path.join(path, 'bin'))

        if platform.system() == 'Darwin':
            yield EnvPrepend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

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