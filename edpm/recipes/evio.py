"""
Evio v6 JLab input output library
https://github.com/JeffersonLab/evio
"""

import os
import platform

from edpm.engine.generators.steps import EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class EvioRecipe(ComposedRecipe):
    """
    Installs the evio library
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/JeffersonLab/evio',
            'branch': 'v6.0.0'
        }
        super().__init__(name='evio', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake'))

    require = {
        "apt": ["liblz4-dev"]

    }