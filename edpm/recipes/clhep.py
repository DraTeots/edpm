"""
This file provides information of how to build and configure CLHEP library:
https://gitlab.cern.ch/CLHEP/CLHEP

"""

import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class ClhepRecipe(ComposedRecipe):
    """
    Installs the CLHEP library from GitLab.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://gitlab.cern.ch/CLHEP/CLHEP.git',
            'branch': 'CLHEP_2_4_7_1'
        }
        super().__init__(name='clhep', config=config)

    def gen_env(self, data):
        path = data['install_path']
        lib_path = os.path.join(path, 'lib')
        bin_path = os.path.join(path, 'bin')

        yield Set('CLHEP', path)
        yield Set('CLHEP_BASE_DIR', path)
        yield Set('CLHEP_INCLUDE_DIR', os.path.join(path, 'include'))
        yield Set('CLHEP_LIB_DIR', lib_path)

        yield Prepend('PATH', bin_path)
        yield Prepend('LD_LIBRARY_PATH', lib_path)

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', lib_path)

