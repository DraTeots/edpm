"""
This file provides information of how to build and configure Eigen3 packet:
https://gitlab.com/libeigen/eigen.git
"""

import os

from edpm.engine.env_gen import Prepend, Set, Append
from edpm.engine.composed_recipe import ComposedRecipe


class EigenRecipe(ComposedRecipe):
    """Provides data for building and installing Eicgen3 framework"""

    def __init__(self, config):

        # Default values for the recipe
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'branch': '3.4.0',
            'url': 'https://gitlab.com/libeigen/eigen.git'
        }
        super().__init__(name='eigen3', config=config)


    def gen_env(self, data):
        """Generates environments to be set"""
        path = data['install_path']

        yield Prepend('CMAKE_PREFIX_PATH', os.path.join(path, 'share/eigen3/cmake/'))
