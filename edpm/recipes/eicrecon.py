"""
This file provides information of how to build and configure EIC Reconstruction (eicrecon) framework:
https://gitlab.com/eic/eicrecon

"""
import os
import platform

from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class EicreconRecipe(ComposedRecipe):
    """
    Installs eicrecon (EIC Reconstruction Framework) from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/eic/eicrecon.git',
            'branch': 'main'
        }
        super().__init__(name='eicrecon', config=config)

    def gen_env(self, data):
        path = data['install_path']
        lib_path = os.path.join(path, 'lib')
        lib64_path = os.path.join(path, 'lib64')

        yield Set('eicrecon_HOME', path)

        yield Prepend('JANA_PLUGIN_PATH', os.path.join(path, 'lib', 'EICrecon', 'plugins'))
        yield Prepend('PATH', os.path.join(path, 'bin'))

        if os.path.isdir(lib64_path):
            yield Prepend('LD_LIBRARY_PATH', lib64_path)
        yield Prepend('LD_LIBRARY_PATH', lib_path)

