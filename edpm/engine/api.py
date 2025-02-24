# edpm/engine/api.py

import os
import sys
from typing import List

from edpm.engine.lockfile import LockfileConfig
from edpm.engine.output import markup_print as mprint
from edpm.engine.recipe_manager import RecipeManager
from edpm.engine.planfile import PlanFile


def print_packets_info(api: "EdpmApi"):
    """
    Helper function to print installed vs. not-installed packages info.
    """
    all_deps = [d.name for d in api.plan.dependencies()]
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
            dep_data = api.lock.get_dependency(dep_name)
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


class EdpmApi:
    """
    Main EDPM API class.
    Handles loading the plan file, the lock file, and orchestrates installs.
    """

    def __init__(self, plan_file="plan.edpm.yaml", lock_file="plan-lock.edpm.yaml"):
        self.plan_file = plan_file
        self.lock_file = lock_file

        self.lock: LockfileConfig = LockfileConfig()
        self.pm = RecipeManager()
        self.plan: PlanFile = None

    def load_all(self):
        """
        Load both the lock file and the plan file into memory,
        and initialize the recipe manager.
        """
        self.lock.load(self.lock_file)
        self.plan = PlanFile.load(self.plan_file)
        self.pm.load_installers()

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
        """
        Return the top-level directory where packages will be installed,
        as recorded in the lock file.
        """
        return self.lock.top_dir

    @top_dir.setter
    def top_dir(self, path: str):
        """
        Update (or set) the top_dir in the lock file.
        """
        real_path = os.path.abspath(path)
        self.lock.top_dir = real_path
        self.lock.save()

    def guess_recipe_for(self, pkg_name: str) -> str:
        """
        If the user did not specify a specific approach, guess one from known names.
        (Kept for backward compatibility or custom usage.)
        """
        known = list(self.pm.recipes_by_name.keys())
        if pkg_name in known:
            return pkg_name
        # Fallback to "manual" if truly unknown
        return "manual"

    def install_dependency_chain(self,
                                 dep_names: List[str],
                                 mode="missing",
                                 explain=False,
                                 deps_only=False):
        """
        Installs all dependencies in 'dep_names' if they are not yet installed,
        respecting the chosen mode:
          - 'missing': only install if not installed
          - 'all'/'force': reinstall anyway
          - 'single': install exactly those requested, ignoring chain
        """
        to_install = []
        for dep_name in dep_names:
            if mode == "missing":
                if not self.lock.is_installed(dep_name):
                    to_install.append(dep_name)
            elif mode in ("all", "force", "single"):
                to_install.append(dep_name)

        if explain:
            if not to_install:
                mprint("Nothing to install!")
            else:
                mprint("<b>Dependencies to be installed (explain only):</b>")
                for dn in to_install:
                    mprint("  - {}", dn)
            return

        for dn in to_install:
            self._install_single_dependency(dn)

    def _install_single_dependency(self, dep_name: str):
        """
        Core routine to install a single dependency.
        Grabs config from the PlanFile, merges with global config,
        calls the relevant recipe steps, and updates the lock file on success.
        """
        # 1) Find the dependency in the plan
        dep_obj = self.plan.find_dependency(dep_name)
        if not dep_obj:
            mprint("<red>Error:</red> No dependency named '{}' in the plan.", dep_name)
            return

        # Check if it is already installed
        if self.lock.is_installed(dep_name):
            ipath = self.lock.get_dependency(dep_name).get("install_path", "")
            if os.path.isdir(ipath) and ipath:
                mprint("<blue>{} is already installed at {}</blue>", dep_name, ipath)
                return

        # Merge global config + local config
        global_cfg = dict(self.plan.global_config_block().data)
        local_cfg = dict(dep_obj.config_block.data)
        combined_config = {**global_cfg, **local_cfg}

        # Ensure we have environment file set, or it is going to be fiasco during install
        if "env_file_bash" not in combined_config:
            bash_env, _ = self.get_env_script_paths()
            combined_config["env_file_bash"] = bash_env

        # Ensure we have a top_dir
        top_dir = self.top_dir
        if not top_dir:
            mprint("<red>No top_dir set. Please use --top-dir or define in lock file.</red>")
            sys.exit(1)

        # e.g. /some/top_dir/MyLib
        combined_config["app_path"] = os.path.join(top_dir, dep_name)

        mprint("<magenta>=========================================</magenta>")
        mprint("<green>INSTALLING</green> : <blue>{}</blue>", dep_name)
        mprint("<magenta>=========================================</magenta>\n")

        # Create and run the recipe
        try:
            # Instead of dep_entry.recipe, we pass dep_obj to let PM decide
            recipe = self.pm.create_recipe(dep_obj.name, combined_config)

            # Now when 'app_path' is set, we can preconfigure the recipe
            recipe.preconfigure()

            # Run installation!
            recipe.run_full_pipeline()
        except Exception as e:
            mprint("<red>Installation failed for {}:</red> {}", dep_name, e)
            raise

        # 6) Resolve the final install_path
        #    In a real scenario, the "maker" might set it in recipe.config["install_path"].
        #    If not present, use a default.
        final_install = recipe.config.get("install_path", "")
        if not final_install:
            # fallback: e.g. app_path/install
            final_install = os.path.join(combined_config["app_path"], "install")
            recipe.config["install_path"] = final_install

        # 7) Update the lock file
        self.lock.update_dependency(dep_name, {
            "install_path": final_install,
            "built_with_config": dict(combined_config),
        })
        self.lock.save()

        mprint("<green>{} installed at {}</green>", dep_name, final_install)

    def get_env_script_paths(self) -> (str, str):
        """
        Determine the paths to env.sh and env.csh based on:
          1) The plan's directory
          2) The global config overrides (env_file_bash, env_file_csh)
          3) If the user sets an absolute path in the config, use it directly.
             Otherwise, join it with the plan's directory.

        Returns (bash_path, csh_path).
        """
        plan_dir = os.path.dirname(os.path.abspath(self.plan_file))

        global_cfg = dict(self.plan.global_config_block().data)
        bash_cfg_value = global_cfg.get("env_file_bash", "env.sh")
        csh_cfg_value  = global_cfg.get("env_file_csh", "env.csh")

        if os.path.isabs(bash_cfg_value):
            bash_path = bash_cfg_value
        else:
            bash_path = os.path.join(plan_dir, bash_cfg_value)

        if os.path.isabs(csh_cfg_value):
            csh_path = csh_cfg_value
        else:
            csh_path = os.path.join(plan_dir, csh_cfg_value)

        return bash_path, csh_path

    def generate_shell_env(self, shell="bash") -> str:
        """
        Build a textual environment script (bash or csh) by combining:
          - global environment
          - each installed package environment
        """
        lines = []
        if shell == "bash":
            lines.append("#!/usr/bin/env bash\n")
        else:
            lines.append("#!/usr/bin/env csh\n")

        lines.append("# EDPM environment script\n\n")

        # 1) Global environment actions
        global_env_actions = self.plan.get_global_env_actions()
        for act in global_env_actions:
            if shell == "bash":
                lines.append(act.gen_bash() + "\n")
            else:
                lines.append(act.gen_csh() + "\n")

        # 2) For each installed dependency, gather environment actions
        all_deps = self.lock.get_all_dependencies()
        for dep_name in sorted(all_deps):
            dep_data = self.lock.get_dependency(dep_name)
            ipath = dep_data.get("install_path", "")
            if not ipath or not os.path.isdir(ipath):
                continue

            dep_obj = self.plan.find_dependency(dep_name)
            if not dep_obj:
                continue

            lines.append(f"\n# ----- ENV for {dep_name} -----\n")
            placeholders = {
                "install_dir": ipath,
                "location": ipath,  # for compatibility with old "manual" usage
            }
            for act in dep_obj.env_block().parse(placeholders):
                if shell == "bash":
                    lines.append(act.gen_bash() + "\n")
                else:
                    lines.append(act.gen_csh() + "\n")

        return "".join(lines)

    def save_shell_environment(self, shell="bash", filename=None):
        """
        Generate and save the environment script for 'shell' (bash or csh).
        If filename is None, we derive it from:
          - global config (env_file_bash / env_file_csh)
          - else use defaults: env.sh / env.csh
          - stored in the same folder as plan.edpm.yaml
        """
        if filename is None:
            bash_path, csh_path = self.get_env_script_paths()
            if shell == "bash":
                filename = bash_path
            else:
                filename = csh_path

        content = self.generate_shell_env(shell=shell)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        mprint("Environment script saved to {}", filename)
