"""
Catch2 unit testing framework
https://github.com/fmtlib/fmt.git
"""

import os
import platform

from edpm.engine.generators.steps import EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class FmtRecipe(ComposedRecipe):
    """ Installs the fmt C++ string formatting library from GitHub. """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            # This can be adjusted if you prefer a stable branch like 'v3.3.2'
            'url': 'https://github.com/fmtlib/fmt.git',
            'branch': 'v11.2.0'
        }
        super().__init__(name='fmt', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'fmt'))
