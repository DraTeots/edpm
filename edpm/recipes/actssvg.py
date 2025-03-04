"""
Acts dd4hep project
https://github.com/acts-project/actsvg.git
"""
import os
import platform

from edpm.engine.generators.steps import EnvAppend, CmakePrefixPath
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

    @staticmethod
    def gen_env(data):
        path = data['install_path']

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(path, 'lib'))

        yield EnvAppend('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
        # Example usage: cmake config location might be named differently:
        yield CmakePrefixPath(os.path.join(path, 'lib', 'cmake', 'actsvg-0.1'))

