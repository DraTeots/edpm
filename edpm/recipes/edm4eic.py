"""
EIC Event data model extension
https://github.com/eic/edm4eic.git
"""
import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class Edm4EicRecipe(ComposedRecipe):
    """
    Installs EDM4EIC from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/edm4eic.git',
            'branch': 'v8.2.0'
        }
        super().__init__(name='edm4eic', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        # This is important for ROOT to find dictionaries
        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'EDM4EIC'))


