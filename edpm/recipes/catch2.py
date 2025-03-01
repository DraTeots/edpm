"""
Catch2 unit testing framework
https://github.com/catchorg/Catch2
"""

import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class Catch2Recipe(ComposedRecipe):
    """
    Installs the Catch2 C++ unit testing framework from GitHub.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            # This can be adjusted if you prefer a stable branch like 'v3.3.2'
            'url': 'https://github.com/catchorg/Catch2.git',
            'branch': 'v3.8.0'
        }
        super().__init__(name='catch2', config=config)

    def gen_env(self, data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'Catch2'))
