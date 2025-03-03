from typing import Optional
from edpm.engine.recipe import Recipe
from edpm.engine.config import ConfigNamespace
from edpm.engine.recipe_components import make_fetcher, make_maker

class ComposedRecipe(Recipe):


    """
    A flexible "composed" recipe that delegates:
     - fetch step to a 'fetcher' (git/tarball/filesystem)
     - build step to a 'maker' (cmake/autotools/custom)
    """
    def __init__(self, config: Optional[ConfigNamespace], name: str=""):

        super().__init__(config)

        self.fetcher = None
        self.maker = None

        config["app_name"] = self.name = name

        # Create fetcher on-demand if it's not already set
        self.fetcher = make_fetcher(config) # Attempt to create fetcher using factory function
        self.maker = make_maker(config) # Attempt to create maker using factory function
        self.use_common_dirs_scheme()


    def preconfigure(self):
        """
        Pre-configures fetcher and maker components for the recipe.

        This method is responsible for ensuring that both a fetcher and a maker
        are available for the recipe before proceeding with the build and install process.
        It uses factory functions `make_fetcher` and `make_maker` (assumed to be defined elsewhere)
        to create these components based on the recipe's configuration.

        Explicit errors are raised if, after attempting to create them, either the fetcher or the maker is still missing.
        This helps to catch configuration problems early in the recipe execution.
        """

        if not self.fetcher: # Check again if fetcher is still missing after creation attempt
            raise RuntimeError(f"Failed to initialize fetcher for recipe '{self.name}'. "
                               "Please check recipe definition and configuration. "
                               "Ensure a valid fetcher type and configuration are provided.")

        # Call preconfigure method of the fetcher if it exists.
        # This allows fetcher to perform its own preconfiguration steps based on the recipe's config.
        if hasattr(self.fetcher, 'preconfigure'):
            self.fetcher.preconfigure()

        if not self.maker: # Check again if maker is still missing after creation attempt
            raise RuntimeError(f"Failed to initialize maker for recipe '{self.name}'. "
                               "Please check recipe definition and configuration. "
                               "Ensure a valid maker type and configuration are provided.")

        # Call preconfigure method of the maker if it exists.
        # This allows maker to perform its own preconfiguration steps based on recipe's config.
        if hasattr(self.maker, 'preconfigure'):
            self.maker.preconfigure()

    def fetch(self):

        if self.fetcher:
            self.fetcher.fetch()

    def patch(self):
        # optional no-op
        pass

    def build(self):
        # Create maker on-demand

        if self.maker:
            self.maker.build()

    def install(self):
        if self.maker:
            self.maker.install()

    def post_install(self):
        pass

    def use_common_dirs_scheme(self):
        """Function sets common directory scheme. It is the same for many packets:
        """

        super().use_common_dirs_scheme()

        if self.fetcher and hasattr(self.fetcher, "use_common_dirs_scheme"):
            self.fetcher.use_common_dirs_scheme()

        if self.maker and hasattr(self.maker, "use_common_dirs_scheme"):
            self.maker.use_common_dirs_scheme()
