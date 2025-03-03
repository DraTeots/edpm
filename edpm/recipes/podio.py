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
            'branch': 'v01-02'
        }
        super().__init__(name='podio', config=config)

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        yield EnvSet('PODIO_ROOT', path)

        # macOS case
        if platform.system() == 'Darwin':
            if os.path.isdir(os.path.join(path, 'lib64')):
                yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib64'))
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # Linux
        if os.path.isdir(os.path.join(path, 'lib64')):
            yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib64'))
        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'podio'))
