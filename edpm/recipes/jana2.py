"""
This file provides information of how to build and configure JANA2 packet:
https://github.com/JeffersonLab/JANA2

"""
import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend, EnvPrepend
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

        yield EnvSet('JANA_HOME', path)
        yield EnvAppend('JANA_PLUGIN_PATH', os.path.join(path, 'plugins'))
        yield EnvPrepend('PATH', os.path.join(path, 'bin'))
        yield EnvPrepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield EnvAppend('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'JANA'))

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))
