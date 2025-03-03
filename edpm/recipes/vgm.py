"""
This file provides information of how to build and configure VMC framework:
Geometry conversion tool, providing conversion between Geant4 and ROOT TGeo geometry models.

https://github.com/vmc-project/vgm


"""
import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend
from edpm.engine.composed_recipe import ComposedRecipe


class VgmRecipe(ComposedRecipe):
    """
    Installs VGM (a geometry conversion tool for Geant4/ROOT).
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/vmc-project/vgm.git',
            'branch': 'v5-3-1'
        }
        super().__init__(name='vgm', config=config)

    def gen_env(self, data):
        path = data['install_path']

        yield EnvSet('VGM_DIR', path)

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib64'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib64'))
