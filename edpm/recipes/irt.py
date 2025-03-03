"""
Indirect Ray Tracing code for EPIC event reconstruction
https://github.com/eic/irt.git

"""
import os
import platform

from edpm.engine.generators.steps import EnvPrepend, CmakePrefixPath
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

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'IRT'))
        yield EnvPrepend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        if platform.system() == 'Darwin':
            yield EnvPrepend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

