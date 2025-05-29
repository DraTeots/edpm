"""
This file provides information of how to build and configure ACTS framework:
https://gitlab.cern.ch/acts/acts-core
"""

import os

from edpm.engine.generators.steps import EnvSet, EnvAppend, CmakePrefixPath
from edpm.engine.composed_recipe import ComposedRecipe


class ActsRecipe(ComposedRecipe):
    """
    Installs the ACTS (A Common Tracking Software) library from GitHub.
    """
    def __init__(self, config):
        # Default config for a Git + CMake build
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/acts-project/acts.git',
            'branch': 'v41.0.0',
            'cmake_flags': '-DACTS_BUILD_PLUGIN_TGEO=ON -DACTS_BUILD_PLUGIN_DD4HEP=ON -DACTS_BUILD_PLUGIN_JSON=ON -DACTS_BUILD_PLUGIN_ACTSVG=OFF'
        }
        super().__init__(name='acts', config=config)


    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        path = data['install_path']

        yield EnvSet('ACTS_DIR', path)

        # it could be lib or lib64. There are bugs on different platforms (RHEL&centos and WSL included)
        # https://stackoverflow.com/questions/46847939/config-site-for-vendor-libs-on-centos-x86-64
        # https: // bugzilla.redhat.com / show_bug.cgi?id = 1510073

        import platform
        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))

        # share/cmake/Acts
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'Acts'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'nlohmann_json'))
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'ActsDD4hep'))
