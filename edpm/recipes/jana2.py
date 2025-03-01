"""
This file provides information of how to build and configure JANA2 packet:
https://github.com/JeffersonLab/JANA2

"""
import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class Jana2Recipe(ComposedRecipe):
    """
    Installs JANA2 from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/JeffersonLab/JANA2.git',
            'branch': 'v2.4.0'
        }
        super().__init__(name='jana2', config=config)

    def gen_env(self, data):
        path = data['install_path']

        yield Set('JANA_HOME', path)
        yield Append('JANA_PLUGIN_PATH', os.path.join(path, 'plugins'))
        yield Prepend('PATH', os.path.join(path, 'bin'))
        yield Prepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'JANA'))

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))
