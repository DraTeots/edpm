"""
This file provides information of how to build and configure Fast Jet:
http://fastjet.fr

"""
import os

import platform
from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.generators.steps import EnvSet, EnvPrepend, EnvAppend

class FastJetRecipe(ComposedRecipe):
    """
    Installs FastJet from a tarball using Autotools-like configure & make.
    Default is FastJet 3.4.3 from fastjet.fr.
    """

    def __init__(self, config):
        # Fill in default_config with the tarball URL and use 'autotools' build
        self.default_config = {
            'fetch': 'tarball',
            'make': 'autotools',
            'url': 'https://fastjet.fr/repo/fastjet-3.4.3.tar.gz',
            # If you need custom configure flags, e.g. debug or special options:
            # 'configure_flags': '--enable-allfeatures',
            # You can also set default 'build_threads': 8 if you want
        }
        super().__init__(name='fastjet', config=config)

    @staticmethod
    def gen_env(data):
        """
        Sets environment variables so that other software can discover FastJet.
        Mirrors the original environment logic from the older v2 recipe.
        """
        install_path = data['install_path']
        yield EnvPrepend('PATH', os.path.join(install_path, 'bin'))
        yield EnvPrepend('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))
        yield EnvSet('FASTJET_ROOT', install_path)

        if platform.system() == 'Darwin':
            yield EnvAppend('DYLD_LIBRARY_PATH', os.path.join(install_path, 'lib'))

