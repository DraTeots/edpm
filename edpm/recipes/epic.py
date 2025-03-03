"""
EPIC DD4Hep geometry repository
"""
import os

from edpm.engine.generators.steps import EnvSet, EnvPrepend
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

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        yield EnvPrepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield EnvPrepend('PATH', os.path.join(path, 'bin'))

        yield EnvSet('DETECTOR_PATH', os.path.join(path, 'share', 'epic'))
        yield EnvSet('BEAMLINE', 'epic')
        yield EnvSet('BEAMLINE_PATH', os.path.join(path, 'share', 'epic'))
        yield EnvSet('BEAMLINE_CONFIG', 'epic')

