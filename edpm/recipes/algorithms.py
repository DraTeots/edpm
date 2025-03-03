"""
Algorithms library:
https://github.com/eic/algorithms

"""
import os
import platform

from edpm.engine.generators.steps import EnvAppend
from edpm.engine.composed_recipe import ComposedRecipe


class AlgorithmsRecipe(ComposedRecipe):
    """
    Installs a hypothetical EIC 'algorithms' project from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/algorithms.git',
            'branch': 'v1.0.0'
        }
        super().__init__(name='algorithms', config=config)

    def gen_env(self, data):
        path = data['install_path']

        # On macOS, add to DYLD_LIBRARY_PATH
        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # On Linux or others, LD_LIBRARY_PATH
        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

