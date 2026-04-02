"""
PodIO
https://github.com/AIDASoft/podio.git
"""
import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class PodioRecipe(ComposedRecipe):
    """
    Installs Podio from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/AIDASoft/podio.git',
            'branch': 'v01-03'
        }
        super().__init__(name='podio', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'podio'))

        # This is important for ROOT to find dictionaries
        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
