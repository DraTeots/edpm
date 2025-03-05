# edpm/engine/api.py

import os
import sys
from typing import List

from edpm.engine.lockfile import LockfileConfig
from edpm.engine.output import markup_print as mprint
from edpm.engine.recipe_manager import RecipeManager
from edpm.engine.planfile import PlanFile

# We rely on the new Generators, but do NOT define environment
# or cmake generation methods here. Just references:
from edpm.engine.generators.environment_generator import EnvironmentGenerator
from edpm.engine.generators.cmake_generator import CmakeGenerator


class EdpmApi:
    """
    Main EDPM API class.
    Handles loading the plan file, the lock file, and orchestrates installs.
    """

    def __init__(self, plan_file="plan.edpm.yaml", lock_file="plan-lock.edpm.yaml"):
        self.plan_file = plan_file
        self.lock_file = lock_file

        self.lock: LockfileConfig = LockfileConfig()
        self.recipe_manager = RecipeManager()
        self.plan: PlanFile = None

    def load_all(self):
        """
        Load both the lock file and the plan file into memory,
        and initialize the recipe manager.
        """
        self.lock.load(self.lock_file)
        self.plan = PlanFile.load(self.plan_file)
        self.recipe_manager.load_installers()

    def ensure_lock_exists(self):
        """
        If the lock file does not exist or is empty, create it.
        """
        if not os.path.isfile(self.lock_file):
            mprint("<green>Creating new lock file at {}</green>", self.lock_file)
            self.lock.file_path = self.lock_file
            self.lock.save()

    @property
    def top_dir(self) -> str:
        """Return the top-level directory where packages will be installed, from lock file."""
        return self.lock.top_dir

    @top_dir.setter
    def top_dir(self, path: str):
        real_path = os.path.abspath(path)
        self.lock.top_dir = real_path
        self.lock.save()

    def guess_recipe_for(self, pkg_name: str) -> str:
        """
        If the user didn't explicitly set a recipe, guess from known recipes
        or default to 'manual'.
        """
        known = list(self.recipe_manager.recipes_by_name.keys())
        if pkg_name in known:
            return pkg_name
        return "manual"

    def install_dependency_chain(self,
                                 dep_names: List[str],
                                 mode="missing",
                                 explain=False,
                                 force=False):
        """
        Installs all dependencies in 'dep_names' if they are not yet installed,
        respecting the chosen mode:
          - mode="missing": only install if not installed
          - mode="all" or force=True: reinstall anyway
        """
        to_install = [
            dep_name
            for dep_name in dep_names
            if force or not self.lock.is_installed(dep_name)
        ]

        if explain:
            if not to_install:
                mprint("Nothing to install!")
            else:
                mprint("<b>Dependencies to be installed (explain only):</b>")
                for dn in to_install:
                    mprint("  - {}", dn)
            return

        for dn in to_install:
            self._install_single_dependency(dn, force)

    def _install_single_dependency(self, dep_name: str, force: bool):
        """
        Core routine to install a single dependency.
        """
        dep_obj = self.plan.find_package(dep_name)
        if not dep_obj:
            mprint("<red>Error:</red> No dependency named '{}' in the plan.", dep_name)
            return

        top_dir = self.top_dir
        if not top_dir:
            mprint("<red>No top_dir set. Please use --top-dir or define it in the lock file.</red>")
            sys.exit(1)

        # If already installed and not forcing, skip
        if self.lock.is_installed(dep_name) and not force:
            ipath = self.lock.get_installed_package(dep_name).get("install_path", "")
            if os.path.isdir(ipath) and ipath:
                mprint("<blue>{} is already installed at {}</blue>", dep_name, ipath)
                return

        # Merge global + local config
        global_cfg = dict(self.plan.global_config())
        local_cfg = dict(dep_obj.config)
        combined_config = {**global_cfg, **local_cfg}

        # we need to generate env_bash_file with what we have now
        env_gen = self.create_environment_generator()
        bash_in, bash_out = self.get_env_paths("bash")
        env_gen.save_environment_with_infile("bash", bash_in, bash_out)

        # save it to packet lock file info
        combined_config["env_file_bash"] = bash_out
        combined_config["app_path"] = os.path.join(top_dir, dep_name)

        # Check if this is an "existing" package
        if "existing" in combined_config:
            existing_path = combined_config["existing"]
            mprint("<magenta>=========================================</magenta>")
            mprint("<green>REFERENCING EXISTING PACKAGE</green> : <blue>{}</blue>", dep_name)
            mprint("<magenta>=========================================</magenta>\n")
            mprint("<blue>Existing installation at: {}</blue>", existing_path)

            # Update lock file for existing package
            self.lock.update_package(dep_name, {
                "install_path": existing_path,
                "built_with_config": dict(combined_config),
                "owned": False  # Mark as not owned by EDPM
            })
            self.lock.save()

            mprint("<green>{} referenced at {}</green>", dep_name, existing_path)
            return

        # Normal installation for non-existing packages
        mprint("<magenta>=========================================</magenta>")
        mprint("<green>INSTALLING</green> : <blue>{}</blue>", dep_name)
        mprint("<magenta>=========================================</magenta>\n")

        # Create the recipe, run the pipeline
        try:
            recipe = self.recipe_manager.create_recipe(dep_obj.name, combined_config)
            recipe.preconfigure()
            recipe.run_full_pipeline()
        except Exception as e:
            mprint("<red>Installation failed for {}:</red> {}", dep_name, e)
            raise

        final_install = recipe.config.get("install_path", "")
        if not final_install:
            final_install = os.path.join(combined_config["app_path"], "install")
            recipe.config["install_path"] = final_install

        # Update lock file
        self.lock.update_package(dep_name, {
            "install_path": final_install,
            "built_with_config": dict(combined_config),
            "owned": True
        })
        self.lock.save()

        mprint("<green>{} installed at {}</green>", dep_name, final_install)

    #
    # Provide the new generator creation
    #
    def create_environment_generator(self) -> EnvironmentGenerator:
        if not self.plan or not self.lock:
            self.load_all()
        return EnvironmentGenerator(self.plan, self.lock, self.recipe_manager)

    def create_cmake_generator(self) -> CmakeGenerator:
        if not self.plan or not self.lock:
            self.load_all()
        return CmakeGenerator(self.plan, self.lock, self.recipe_manager)

    def _resolve_output_path(self, config_key: str, default_filename: str) -> str:
        """
        Resolve output path based on spec priority:
        1. Explicitly set in config
        2. top_dir if exists
        3. Current working directory
        """
        # Get explicit config value
        explicit_path = self.plan.global_config().get(config_key)

        if explicit_path:
            return os.path.abspath(explicit_path)

        # Try top_dir if configured
        if self.top_dir:
            return os.path.join(self.top_dir, default_filename)

        # Fallback to current directory
        return os.path.join(os.getcwd(), default_filename)

    def get_env_paths(self, shell_type: str) -> tuple:
        """Get (input_path, output_path) for environment files"""
        in_key = f"env_{shell_type}_in"
        out_key = f"env_{shell_type}_out"
        default_out = f"env.{'sh' if shell_type == 'bash' else 'csh'}"

        in_path = self.plan.global_config().get(in_key)
        out_path = self._resolve_output_path(out_key, default_out)
        return in_path, out_path

    def get_cmake_toolchain_paths(self) -> tuple:
        """Get (input_path, output_path) for CMake toolchain"""
        in_path = self.plan.global_config().get("cmake_toolchain_in")
        out_path = self._resolve_output_path("cmake_toolchain_out", "EDPMToolchain.cmake")
        return in_path, out_path

    def get_cmake_presets_paths(self) -> tuple:
        """Get (input_path, output_path) for CMake presets"""
        in_path = self.plan.global_config().get("cmake_presets_in")
        out_path = self._resolve_output_path("cmake_presets_out", "CMakePresets.json")
        return in_path, out_path

    def save_generator_scripts(self):
        # Get all paths through the API
        bash_in, bash_out = self.get_env_paths("bash")
        csh_in, csh_out = self.get_env_paths("csh")
        toolchain_in, toolchain_out = self.get_cmake_toolchain_paths()
        presets_in, presets_out = self.get_cmake_presets_paths()
    
        # Environment files
        env_gen = self.create_environment_generator()
        env_gen.save_environment_with_infile("bash", bash_in, bash_out)
        mprint(f"<green>[Saved]</green> bash environment: {bash_out}")
        env_gen.save_environment_with_infile("csh", csh_in, csh_out)
        mprint(f"<green>[Saved]</green> csh  environment: {csh_out}")
    
        # CMake files
        cm_gen = self.create_cmake_generator()
        cm_gen.save_toolchain_with_infile(toolchain_in, toolchain_out)
        mprint(f"<green>[Saved]</green> CMake toolchain: {toolchain_out}")
        cm_gen.save_presets_with_infile(presets_in, presets_out)
        mprint(f"<green>[Saved]</green> CMake presets  : {presets_out}")


def print_packets_info(api: "EdpmApi"):
    """
    Helper function to print installed vs. not-installed packages info.
    """
    all_deps = [d.name for d in api.plan.packages()]
    installed_names = []
    not_installed_names = []
    for dep_name in all_deps:
        if api.lock.is_installed(dep_name):
            installed_names.append(dep_name)
        else:
            not_installed_names.append(dep_name)

    if installed_names:
        mprint('\n<b><magenta>INSTALLED PACKAGES:</magenta></b>')
        for dep_name in sorted(installed_names):
            dep_data = api.lock.get_installed_package(dep_name)
            install_path = dep_data.get("install_path", "")
            mprint(' <b><blue>{}</blue></b>: {}', dep_name, install_path)
    else:
        mprint("\n<magenta>No packages currently installed.</magenta>")

    if not_installed_names:
        mprint("\n<b><magenta>NOT INSTALLED:</magenta></b>\n(could be installed by 'edpm install')")
        for dep_name in sorted(not_installed_names):
            mprint(' <b><blue>{}</blue></b>', dep_name)
    else:
        mprint("\nAll plan packages appear to be installed.")

    _, bash_out = api.get_env_paths("bash")
    _, csh_out = api.get_env_paths("csh")
    _, toolchain_out = api.get_cmake_toolchain_paths()
    _, presets_out = api.get_cmake_presets_paths()

    mprint(f"<b><blue>bash env</blue></b>        : {bash_out}")
    mprint(f"<b><blue>csh  env</blue></b>        : {csh_out}")
    mprint(f"<b><blue>CMake toolchain</blue></b> : {toolchain_out}")
    mprint(f"<b><blue>CMake presets  </blue></b> : {presets_out}")