"""
Acts dd4hep project
https://github.com/acts-project/actsvg.git
"""
import os
import platform

from edpm.engine.env_gen import Append, Set, Prepend
from edpm.engine.composed_recipe import ComposedRecipe


class ActsSvgRecipe(ComposedRecipe):
    """
    Installs the ActsSVG plugin (hypothetical project) for ACTS-based SVG outputs.
    """
    def __init__(self, config):
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/acts-project/acts-svg.git',
            'branch': 'v0.4.50'
        }
        super().__init__(name='actssvg', config=config)

    def gen_env(self, data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield Append('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        # Example usage: cmake config location might be named differently:
        yield Append('CMAKE_PREFIX_PATH', os.path.join(path, 'lib', 'cmake', 'actsvg-0.1'))

