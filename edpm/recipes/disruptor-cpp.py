"""
JLab version of disruptor-cpp library
https://github.com/JeffersonLab/Disruptor-cpp
"""

import os
import platform

from edpm.engine.generators.steps import EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class EvioRecipe(ComposedRecipe):
    """
    Installs the JLab version of disruptor-cpp library
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/JeffersonLab/Disruptor-cpp.git',
            'branch': 'master'
        }
        super().__init__(name='disruptor-cpp', config=config)

    def preconfigure(self):
        # We need to do it in preconfigure when install_path is known
        self.config["cmake_flags"]=f"-DINSTALL_DIR={self.config['install_path']}"
        super().preconfigure()

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