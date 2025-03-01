"""
EPIC DD4Hep geometry repository
"""
import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class EpicRecipe(ComposedRecipe):
    """
    Installs the ePIC detector software from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/epic.git',
            'branch': '25.02.0'
        }
        super().__init__(name='epic', config=config)

    def gen_env(self, data):
        path = data['install_path']

        yield Prepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield Prepend('PATH', os.path.join(path, 'bin'))

        yield Set('DETECTOR_PATH', os.path.join(path, 'share', 'epic'))
        yield Set('BEAMLINE', 'epic')
        yield Set('BEAMLINE_PATH', os.path.join(path, 'share', 'epic'))
        yield Set('BEAMLINE_CONFIG', 'epic')

