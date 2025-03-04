"""
EDM4Hep
https://github.com/key4hep/EDM4hep
"""

import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class Edm4HepRecipe(ComposedRecipe):
    """
    Installs EDM4hep from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/key4hep/EDM4hep.git',
            'branch': 'v00-99-01'
        }
        super().__init__(name='edm4hep', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'EDM4HEP'))
        yield EnvSet('EDM4HEP_ROOT', path)
