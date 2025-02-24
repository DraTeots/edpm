from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.config import ConfigNamespace

class GitCmakeRecipe(ComposedRecipe):
    """
    A refactored Git+CMake recipe that uses the new EDPM pipeline:
      fetch -> patch -> build -> install -> post_install,
    plus a gen_env() returning environment actions.

    This version references self.config[...] everywhere, so the user
    clearly sees all settings (like repo_address, branch, etc.) in config.
    """

    def __init__(self, name: str, config: ConfigNamespace = None):
        super().__init__(name, config)

        # Provide some defaults if they aren't set in the plan file
        self.config['fetch'] = 'git'
        self.config['make'] =  'cmake'

    def preconfigure(self):
        super().preconfigure()

