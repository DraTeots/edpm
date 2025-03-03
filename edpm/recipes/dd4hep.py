"""
This file provides information of how to build and configure HepMC framework:
https://github.com/AIDASoft/DD4hep
"""

import os
import platform

from edpm.engine.generators.steps import EnvSet, EnvAppend, EnvPrepend, EnvRawText
from edpm.engine.composed_recipe import ComposedRecipe


class DD4HepRecipe(ComposedRecipe):
    """
    Installs DD4hep from Git + CMake.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/AIDASoft/DD4hep.git',
            'branch': 'v01-31'
        }
        super().__init__(name='dd4hep', config=config)

    def gen_env(self, data):
        path = data['install_path']
        bin_path = os.path.join(path, 'bin')
        lib_path = os.path.join(path, 'lib')
        include_path = os.path.join(path, 'include')
        cmake_path = os.path.join(path, 'cmake')

        # EnvPrepend PATH for dd4hep executables
        yield EnvPrepend('PATH', bin_path)

        # Typical dynamic library environment
        yield EnvAppend('LD_LIBRARY_PATH', lib_path)
        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', lib_path)

        # CMake detection
        yield EnvAppend('CMAKE_PREFIX_PATH', cmake_path)

        # Root cling might want to find these headers
        yield EnvAppend('ROOT_INCLUDE_PATH', include_path)

        # Optionally source the 'thisdd4hep_only.sh' if it exists
        bash_thisdd4hep_path = os.path.join(bin_path, 'thisdd4hep_only.sh')
        bash_text = (
            f'if [ -f "{bash_thisdd4hep_path}" ] ; then\n'
            f'   source "{bash_thisdd4hep_path}"\n'
            f'fi\n'
        )
        csh_text = (
            f'if ( -f "{bash_thisdd4hep_path}" ) then\n'
            f'    source "{bash_thisdd4hep_path}"\n'
            f'endif\n'
        )
        yield EnvRawText(bash_text, csh_text, None)

        # Also define DD4HEP_DIR
        yield EnvSet('DD4HEP_DIR', path)

