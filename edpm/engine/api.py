# edpm_api.py

import os
import click
import io

from typing import Dict, List
from edpm.engine.manifest import EdpmManifest
from .lockfile import LockfileConfig
from edpm.engine.recipe_manager import RecipeManager
from edpm.engine.output import markup_print as mprint
from edpm.engine.env_gen import EnvironmentManipulation

# optional: from edpm.engine.commands import run, workdir (if needed)

ENV_SH_PATH = "env_sh_path"
ENV_CSH_PATH = "env_csh_path"


class EdpmApi:
    """
    This 'API' object replaces the old DB-based approach.
    It loads a YAML manifest (e.g. package.edpm.yaml)
    and a YAML lockfile (e.g. package-lock.edpm.yaml).

    * manifest: what we WANT to install
    * lockfile: what is currently INSTALLED + top_dir, etc.

    The 'RecipeManager' is used to create + run the actual recipes.
    """

    def __init__(self, manifest_file="package.edpm.yaml", lock_file="package-lock.edpm.yaml"):
        self.manifest: EdpmManifest = None
        self.lock: LockfileConfig = LockfileConfig()
        self.pm = RecipeManager()

        # Paths for environment scripts, if we generate them
        self.env_sh_path = "envedpm.sh"
        self.env_csh_path = "envedpm.csh"

        # 1. Load the manifest
        self.manifest_file = manifest_file
        self.manifest_is_loaded = False
        self.lock_file = lock_file
        self.lock_is_loaded = False

    def load_all(self):
        # 2. Load the lock file
        self.lock.load(self.lock_file)
        self.lock_is_loaded = True
        self.manifest = EdpmManifest.load(self.manifest_file)
        self.pm.load_installers()


    def ensure_lock_exists(self):
        """
        If the lock file path is not set or does not exist, create a new one on disk.
        """
        if not self.lock.file_path:
            # Default location
            self.lock.file_path = "package-lock.edpm.yaml"
        if not os.path.isfile(self.lock.file_path):
            mprint("<green>Creating new lock file at {}</green>", self.lock.file_path)
            self.lock.save()

    @property
    def top_dir(self) -> str:
        return self.lock.top_dir

    @top_dir.setter
    def top_dir(self, path: str):
        """
        The user can supply a top_dir (like --top-dir).
        We store it in the lock file so the recipes know where to install.
        """
        real_path = os.path.abspath(path)
        self.lock.top_dir  = real_path
        self.lock.save()

    def guess_recipe_for(self, pkg_name: str) -> str:
        """
        If 'pkg_name' matches a known recipe from the RecipeManager, return that.
        Otherwise, guess a fallback or return None.
        """
        known = list(self.pm.recipes_by_name.keys())  # e.g. ["manual", "github-cmake-cpp", "root", "geant4", ...]
        # If user typed "root" and we do have a "root" in registry, return "root"
        if pkg_name in known:
            return pkg_name
        # Maybe special-case certain names that map to known recipes
        # e.g., if pkg_name.lower() == "geant4" and "geant4" in known: return "geant4"

        # Otherwise fallback to "manual" or "github-cmake-cpp", or None
        # In real usage, you might prefer a "manual" approach or raise an error
        # if you can't guess. For demonstration:
        if "manual" in known:
            return "manual"

        return None  # meaning we can't guess, the user must specify



    def install_dependency_chain(self, dep_names: List[str], mode="missing", explain=False, deps_only=False):
        """
        Installs each named dependency plus any sub-dependencies.
        Mode can be 'missing', 'single', 'all' (like the old code).
        If explain=True, we only print what would be installed, not actually build.
        If deps_only=True, skip building the main package and only build its dependencies.
        """
        if not dep_names:
            return

        # We build a chain of dependencies from the manifest.
        # (If you want advanced "transitive" dependencies, you'd do it here.
        #  The new EDPM might rely on the order from the manifest, or a graph approach.)
        # For simplicity, we just assume user gave the exact names in the correct order
        # or you have some method to gather them.

        # 1) For each named dep, see if it's installed. If missing => install
        to_install = []
        for dep_name in dep_names:
            # If user wants 'single' mode, or if the lock says it's not installed, we add it
            if mode == "all":
                to_install.append(dep_name)
            elif mode == "single":
                # Only the main package, ignoring whether it's installed or not
                to_install.append(dep_name)
            else:  # 'missing' mode
                if not self.lock.is_installed(dep_name):
                    to_install.append(dep_name)

        # If deps_only = True, we skip installing the actual named dep if it's in to_install
        # This is how your old code separated "dependencies but not the package"
        if deps_only:
            # skip the last one?
            # or skip all named? It's up to your old logic.
            # Possibly we remove the last item from to_install:
            # But it's ambiguous. We'll do a minimal approach:
            for dep_name in dep_names:
                if dep_name in to_install:
                    to_install.remove(dep_name)

        # If there's nothing to install, we exit
        if not to_install:
            mprint("Nothing to install!")
            return

        # If explain mode, just print
        if explain:
            mprint("<b>Dependencies to be installed (explain only):</b>")
            for dn in to_install:
                mprint("  - {}", dn)
            return

        # Actually install each dependency
        for dn in to_install:
            self._install_single_dependency(dn)

        # Save lock
        self.lock.save()

    def _install_single_dependency(self, dep_name: str):
        """
        Creates a recipe instance from the manifest + global config,
        runs it, and records the result in the lock file.
        """
        # 1) Find the dependency in the manifest
        dep_entry = self.manifest.find_dependency(dep_name)
        if not dep_entry:
            mprint("<red>Error:</red> No dependency named '{}' in the manifest.", dep_name)
            return

        # 2) Check if it's already installed
        if self.lock.is_installed(dep_name):
            ipath = self.lock.get_dependency(dep_name).get("install_path", "")
            mprint("<blue>{} is already installed at {}</blue>", dep_name, ipath)
            return

        # 3) Combine global config + top_dir + dep config
        #    EdpmManifest now stores global config in global_config_block.
        global_cfg = dict(self.manifest.global_config_block.data)
        top_dir = self.top_dir
        if not top_dir:
            mprint("<red>No top_dir set. Please use --top-dir or define in lock file.</red>")
            raise click.Abort()

        # Our "app_path" convention: join top_dir + dep_name
        global_cfg["app_path"] = os.path.join(top_dir, dep_name)

        # Merge fields from the dependency's config_block
        dep_cfg = dep_entry.config_block.data  # dict with e.g. branch, repo_address, build_threads, etc.

        # Build final combined config
        combined_config = {**global_cfg, **dep_cfg, "name": dep_entry.name}

        # The recipe name is the same as the dependency's name (or fallback)

        # 4) Create the recipe via RecipeManager using the dep's recipe type + combined_config
        recipe_type = dep_entry.recipe  # e.g. "manual", "github-cmake-cpp", etc.
        recipe = self.pm.recipes_by_name[dep_name]

        # 5) Run the pipeline
        mprint("<magenta>=========================================</magenta>")
        mprint("<green>INSTALLING</green> : <blue>{}</blue>", dep_name)
        mprint("<magenta>=========================================</magenta>\n")

        try:
            recipe.run_full_pipeline()
        except Exception as e:
            mprint("<red>Installation failed for {}:</red> {}", dep_name, e)
            raise click.Abort()

        # 6) Record results in the lock file
        install_path = recipe.config.get("install_path", "")
        self.lock.update_dependency(dep_name, {
            "install_path": install_path,
            "built_with_config": dict(combined_config),
        })
        mprint("<green>{} installed at {}</green>", dep_name, install_path)

    # ------------------------------------------------------------------------
    # Generating shell environment
    # ------------------------------------------------------------------------
    def generate_shell_env(self, shell="bash"):
        """
        Iterate over all installed dependencies, gather environment instructions,
        produce a single shell script text. Then user can redirect to a file.
        """
        lines = []
        lines.append("#!/usr/bin/env bash\n" if shell == "bash" else "#!/usr/bin/env csh\n")
        lines.append("# EDPM environment script\n")

        # For global environment from the manifest
        global_env_actions = self.manifest.get_global_env_actions()
        for act in global_env_actions:
            if shell == "bash":
                lines.append(act.gen_bash() + "\n")
            else:
                lines.append(act.gen_csh() + "\n")

        # For each installed dependency, we create a recipe again, call gen_env() with { install_path: ... } from lock
        for dep_name in sorted(self.lock.get_all_dependencies()):
            dep_data = self.lock.get_dependency(dep_name)
            # If there's no path, skip
            ipath = dep_data.get("install_path", "")
            if not ipath or not os.path.isdir(ipath):
                continue
            # Recreate a minimal recipe object to get environment steps
            # Or you can store the recipe type in the lock as well.
            # For now, we guess from the manifest
            found = [d for d in self.manifest.dependencies if d.name == dep_name]
            if not found:
                continue
            dep_entry = found[0]
            # Build config
            config_data = dict(dep_data.get("built_with_config", {}))
            # Create recipe
            recipe = self.pm.create_recipe(dep_entry.recipe, config_data)
            # installed_data
            installed_data = {"install_path": ipath}
            steps = recipe.gen_env(installed_data)

            lines.append(f"\n# ----- ENV for {dep_name} -----\n")
            for step in steps:
                if shell == "bash":
                    lines.append(step.gen_bash() + "\n")
                else:
                    lines.append(step.gen_csh() + "\n")

        return "".join(lines)

    def save_shell_environment(self, shell="bash", filename=None):
        """
        Writes the environment script to disk.
        Default filenames can be 'scipm_env.sh' or 'scipm_env.csh'.
        """
        if not filename:
            filename = self.env_sh_path if shell == "bash" else self.env_csh_path

        content = self.generate_shell_env(shell=shell)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        mprint("Environment script saved to {}", filename)


def print_packets_info(api):
    """
    Prints a summary of which packages are installed vs. not installed,
    using the new EdpmApi (which holds a manifest + lock file).
    """
    # 1) Gather all dependency names from the manifest
    all_dep_names = [dep.name for dep in api.manifest.dependencies]

    # 2) Determine which are installed by checking the lock
    installed_names = []
    for dep_name in all_dep_names:
        if api.lock.is_installed(dep_name):
            installed_names.append(dep_name)

    # 3) Print installed packages
    if installed_names:
        mprint('\n<b><magenta>INSTALLED PACKAGES:</magenta></b>')
        for dep_name in sorted(installed_names):
            dep_data = api.lock.get_dependency(dep_name)
            install_path = dep_data.get("install_path", "")
            mprint(' <b><blue>{}</blue></b>: {}', dep_name, install_path)
    else:
        mprint("\n<magenta>No packages currently installed.</magenta>")

    # 4) Print not-installed packages
    not_installed_names = [d for d in all_dep_names if d not in installed_names]
    if not_installed_names:
        mprint("\n<b><magenta>NOT INSTALLED:</magenta></b>\n(could be installed by 'edpm install')")
        for dep_name in sorted(not_installed_names):
            mprint(' <b><blue>{}</blue></b>', dep_name)
    else:
        mprint("\nAll manifest packages appear to be installed.")