# edpm/engine/recipe_manager.py

import pkgutil
import importlib
from typing import Dict
from edpm.engine.recipe import Recipe
from edpm.engine.composed_recipe import ComposedRecipe   # We'll define it (see below)

def import_all_submodules(modules_dir, package_name):
    for (module_loader, name, ispkg) in pkgutil.iter_modules([modules_dir]):
        importlib.import_module('.' + name, package_name)

def all_subclasses(cls):
    results = set()
    for subclass in cls.__subclasses__():
        results.add(subclass)
        results.update(all_subclasses(subclass))
    return results

class RecipeManager:
    """
    Manages creation of 'baked in' recipes or 'composed' ones.
    """

    def __init__(self):
        self.recipes_by_name = {}
        # (Optional) keep track of known built-in names like "root", "geant4", etc.

    def load_installers(self, modules_dir=None, package_name="edpm.recipes"):
        """
        Import all recipe modules so that baked-in recipe classes are registered.
        For example, RootRecipe might set self.name = "root" internally.
        """
        if modules_dir is None:
            # Automatically determine the package directory
            package = importlib.import_module(package_name)
            modules_dir = package.__path__[0]

        import_all_submodules(modules_dir, package_name)

        # gather all classes that subclass Recipe
        classes = all_subclasses(Recipe)

        # go over classes
        for cls in classes:
            try:
                tmp_instance = cls(config={})  # e.g. RootRecipe()
                if hasattr(tmp_instance, 'name') and tmp_instance.name:
                    # store in a dictionary
                    rname = tmp_instance.name
                    self.recipes_by_name[rname] = cls
            except TypeError:
                pass

    def create_recipe(self, recipe_name, config: Dict[str, any]):
        """
        dep_obj is a planfile.PlanPackage instance.
        config is the merged config dict (global + local).
        Return a `Recipe` object (either baked-in or composed).
        """

        if recipe_name in self.recipes_by_name:
            recipe_cls = self.recipes_by_name[recipe_name]
            recipe = recipe_cls(config)  # instantiate
        else:
            # It's a custom / composed dependency
            # We'll create a ComposedRecipe
            recipe = ComposedRecipe(config=config, name=recipe_name)

        return recipe
