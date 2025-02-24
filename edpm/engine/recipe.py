# edpm/engine/recipe.py

import os
from typing import Optional, List
from edpm.engine.config import ConfigNamespace

class Recipe:
    """
    Base class for all recipes.

    Recipes in EDPM define how to build, install, and manage a specific software package.
    This class provides a common structure and defines the lifecycle stages
    for all recipes, whether they are baked-in (simple recipes that inherit this class and override methods)
    or composed (selecting components like fetcher and maker in ComposedRecipe).

    """

    default_config = {}     # inherited classes can add values here before calling super().__init__(...).
    # This simplifies __init__() for inherited classes

    def __init__(self, config: Optional[ConfigNamespace]):

        # Smart copy of default configs into the config
        if self.default_config:
            local_config = self.default_config.copy()
            local_config.update(config)     # If user provided some fields, they should overwrite defaults
            config.update(local_config)     # This copies back whatever we have with config

        self.config = config if config else ConfigNamespace()
        # Next variables are set by ancestors


    def preconfigure(self):
        """This function is used to format and fill variables, when app_path is known download command
        This method is called before any other recipe steps (fetch, build, install, etc.).
        """
        pass

        def preconfigure(self):
            """
            Prepare configuration variables after app_path is known but before fetching.
            Used to format path templates and set up derived configuration values.
            """
        pass

    def fetch(self):
        """Download or clone the package sources to fetch_path"""
        pass

    def patch(self):
        """Apply any patches or source modifications to source_path"""
        pass

    def build(self):
        """Configure and compile the package in build_path"""
        pass

    def install(self):
        """Install the built package to install_path"""
        pass

    def post_install(self):
        """Perform post-installation tasks and verification"""
        pass

    def run_full_pipeline(self):
        """
        Execute the complete installation pipeline:
        1. fetch() -> 2. patch() -> 3. build() -> 4. install() -> 5. post_install()
        """
        self.fetch()
        self.patch()
        self.build()
        self.install()
        self.post_install()

    def use_common_dirs_scheme(self):
        """Function sets common directory scheme. It is the same for many packets:
        """
        if 'app_path' in self.config.keys():
            # where we download the source or clone git
            if "fetch_path" not in self.config.keys():
                self.config["fetch_path"] = "{app_path}/src".format(**self.config)

            # The directory with source files for current version
            if "source_path" not in self.config.keys():
                self.config["source_path"] = "{app_path}/src".format(**self.config)

            # The directory for cmake build
            if "build_path" not in self.config.keys():
                self.config["build_path"] = "{app_path}/build".format(**self.config)

            # The directory, where binary is installed
            if "install_path" not in self.config.keys():
                self.config["install_path"] = "{app_path}/{app_name}-install".format(**self.config)
