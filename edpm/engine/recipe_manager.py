import importlib
import pkgutil
import edpm.recipes
from edpm.engine.git_cmake_recipe import GitCmakeRecipe

from edpm.engine.recipe import Recipe


def import_all_submodules(modules_dir, package_name):
    # >oO debug   for (module_loader, name, ispkg) in pkgutil.iter_modules([modules_dir]):
    # >oO debug       print("module_loader {}, name {}, ispkg {}".format(module_loader, name, ispkg))

    # parent_module =  imp.find_module('packets', path)
    for (module_loader, name, ispkg) in pkgutil.iter_modules([modules_dir]):
        importlib.import_module('.' + name, package_name)
        # module = importlib.import_module('.' + name, package_name)
        # >oO debug   print(module)


class InstallationRequest(object):
    """ This class is assumed to reflect a user requests for a packet installation"""

    def __init__(self, recipe, mode, config, just_explain=False, deps_only=4):
        assert isinstance(recipe, Recipe)

        self.name = recipe.name   # Packet name
        self.recipe = recipe
        self.mode = mode
        self.just_explain = just_explain
        self.config_overrides = config
        self.deps_only = deps_only

    def update_installer_config(self):
        self.recipe.config.update(self.config_overrides)

    def __repr__(self):
        return "InstallationRequest '{}'".format(self.name)


class RecipeManager(object):

    class Config(object):
        dir = ""

    def __init__(self):
        # But now we just import and create them manually
        self.recipes_by_name = {}
        self.env_generators = {}

        # The next are collection of requirements for different operating systems
        # The type is map to have requirements by packets, i.e.:
        #     self.centos_required_packets['eicrecon'] - list for eicrecon
        self.os_deps_by_name = {}

    def load_installers(self, modules_dir="", package_name=""):

        if not modules_dir:
            modules_dir = edpm.recipes.__path__[0]
        if not package_name:
            package_name = edpm.recipes.__name__

        # We need to import submodules at least once to get __submodules__() function work later
        import_all_submodules(modules_dir, package_name)

        # Create all subclasses of Recipe and GitCmakeRecipe and add here
        classes = [cls for cls in Recipe.__subclasses__() + GitCmakeRecipe.__subclasses__() if cls != GitCmakeRecipe]

        for cls in classes:
            if cls == GitCmakeRecipe:
                continue
            installer = cls()

            # Add installer 'by name'
            self.recipes_by_name[installer.name] = installer

            # Add environment generator to env_generators map
            if hasattr(installer, 'gen_env'):
                self.env_generators[installer.name] = installer.gen_env

            # Add list of dependencies
            self.add_os_deps(installer)

    def add_os_deps(self, installer):
        """Adds os dependencies to global os_dependencies_by_name map"""

        # First, we add default structure with empty deps
        result = {'required': {'ubuntu': '', 'centos': ''},
                  'optional': {'ubuntu': '', 'centos': ''}}

        # Then we check if installer defines its dependencies
        if hasattr(installer, 'os_dependencies'):
            result.update(installer.os_dependencies)

        # Set the result by installer name
        self.os_deps_by_name[installer.name] = result

    def get_installation_chain_names(self, main_recepie_name, deps_only=False):
        """
        Returns name of the package + dependencies edpm can install
        so it is like: ['CLHEP', 'root', ..., 'eicrecon'] for installer_name=eicrecon
        it is single: ['CLHEP'] for installer_name='CLHEP'

        :param deps_only: get only names of dependencies not packet name included
        :param main_recepie_name: name of packet like 'eicrecon'
        :return: list with dependencies names and installer name itself
        """

        deps = self.recipes_by_name[main_recepie_name].required_deps

        if deps_only:
            return deps

        # If we install just a single packet desired_names a single name
        return deps + [main_recepie_name] if deps else [main_recepie_name]

    def gen_shell_env_text(self, name_data, shell='bash'):
        """Generates a text that sets environment for a given shell """

        output = ""     # a string holding the result

        # Go through provided name-path pairs:
        for name, data in name_data.items():

            # if some packet has no data, or there is no environ generator for it, we skip it
            if not data or name not in self.env_generators.keys():
                continue

            env_gen = self.env_generators[name]

            output += "\n"
            output += "# =============================\n"
            output += "# {}\n".format(name)
            output += "# =============================\n"

            # env_gen(data) provides environment manipulation instructions based on the given data
            steps = env_gen(data)
            if not steps:
                continue
            for step in env_gen(data):
                output += step.gen_csh() if shell == 'csh' else step.gen_bash()   # bash or csh?
                output += '\n'
        return output

    def gen_bash_env_text(self, name_data):
        """Generates a text that sets environment for bash shell """
        return self.gen_shell_env_text(name_data, shell='bash')

    def gen_csh_env_text(self, name_data):
        """Generates a text that sets environment for csh/tcsh shell """
        return self.gen_shell_env_text(name_data, shell='csh')

    def update_python_env(self, name_data):
        """Updates python environment according to (name,paths) pairs"""

        # Go through provided name-path pairs:
        for name, data in name_data.items():

            # If we have a generator for this program and installation data
            if data and name in self.env_generators.keys():
                env_gens = self.env_generators[name]
                for env_gen in env_gens(data):          # Go through 'environment generators' look engine/env_gen.py
                    env_gen.update_python_env()         # Do environment update
