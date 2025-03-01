"""
This file provides information of how to build and configure HepMC framework:
https://gitlab.cern.ch/hepmc/HepMC3
"""
import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class HepMC3Recipe(ComposedRecipe):
    """
    Installs HepMC3 from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://gitlab.cern.ch/hepmc/HepMC3.git',
            'branch': 'v3.3.0'
        }
        super().__init__(name='hepmc3', config=config)

    def gen_env(self, data):
        path = data['install_path']
        bin_path = os.path.join(path, 'bin')

        yield Prepend('PATH', bin_path)
        yield Set('HEPMC3_DIR', path)
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'share', 'HepMC3', 'cmake'))

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))
        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
