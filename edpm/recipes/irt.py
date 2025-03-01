"""
Indirect Ray Tracing code for EPIC event reconstruction
https://github.com/eic/irt.git

"""
import os
import platform

from edpm.engine.env_gen import Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class IrtRecipe(ComposedRecipe):
    """
    Installs IRT (Imaging Reconstruction Toolkit) from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/irt.git',
            'branch': 'v1.0.8'
        }
        super().__init__(name='irt', config=config)

    def gen_env(self, data):
        path = data['install_path']

        yield Prepend('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'IRT'))
        yield Prepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        if platform.system() == 'Darwin':
            yield Prepend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

