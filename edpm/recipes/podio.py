"""
PodIO
https://github.com/AIDASoft/podio.git
"""
import os
import platform

from edpm.engine.env_gen import Set, Append
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

    def gen_env(self, data):
        path = data['install_path']

        yield Set('PODIO_ROOT', path)

        # macOS case
        if platform.system() == 'Darwin':
            if os.path.isdir(os.path.join(path, 'lib64')):
                yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib64'))
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # Linux
        if os.path.isdir(os.path.join(path, 'lib64')):
            yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib64'))
        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'podio'))
