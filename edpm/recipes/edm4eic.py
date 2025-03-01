"""
EIC Event data model extension
https://github.com/eic/edm4eic.git
"""
import os
import platform

from edpm.engine.env_gen import Set, Append
from edpm.engine.composed_recipe import ComposedRecipe


class Edm4EicRecipe(ComposedRecipe):
    """
    Installs EDM4EIC from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/edm4eic.git',
            'branch': 'v8.0.0'
        }
        super().__init__(name='edm4eic', config=config)

    def gen_env(self, data):
        path = data['install_path']

        yield Set('EICD_ROOT', path)

        if platform.system() == 'Darwin':
            # Some projects might install in lib or lib64
            if os.path.isdir(os.path.join(path, 'lib64')):
                yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib64'))
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # On Linux, we add both lib and lib64 if they exist
        if os.path.isdir(os.path.join(path, 'lib64')):
            yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib64'))
        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'EDM4EIC'))
