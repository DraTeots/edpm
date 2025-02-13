"""
manifest.py

This module provides classes and functions for handling the EDPM YAML manifest:
  - edpm.dependencies.yaml

It includes:
  - Loading the YAML data
  - Parsing global config and global environment
  - Parsing dependencies (including environment and external requirements)
  - Utility methods to gather external requirements by package manager key

All environment-manipulation code (Set, Prepend, Append, etc.) is also included
here to avoid scattering the logic across multiple files.
"""

import os
import yaml
from typing import Any, Dict, List, Optional

from edpm.engine.env_gen import EnvironmentManipulation, Append, Prepend, Set


############################
# Manifest Classes
############################

def expand_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    """
    Expands placeholders like $install_dir or $location in a string.
    If text = "$install_dir/bin" and placeholders["install_dir"] = "/opt/foo",
    then the result is "/opt/foo/bin".
    """
    if not text:
        return text

    for k, v in placeholders.items():
        text = text.replace(f'${k}', v)
    return text


def parse_environment_block(
        env_block: List[Any],
        placeholders: Optional[Dict[str, str]] = None
) -> List[EnvironmentManipulation]:
    """
    Converts a YAML environment list into a list of EnvironmentManipulation objects.

    Example env_block:
      [
        { prepend: { PATH: "$install_dir/bin", LD_LIBRARY_PATH: "$install_dir/lib" }},
        { set: { MY_VAR: "some_value" }},
        { append: { PYTHONPATH: "/custom/python" }}
      ]

    placeholders can be something like:
      { "install_dir": "/opt/app", "location": "/opt/manual" }

    Returns a list of Set/Prepend/Append objects.
    """
    if placeholders is None:
        placeholders = {}

    result = []

    for item in env_block:
        # Each item is expected to be a dict with exactly one key: set, prepend, or append
        if not isinstance(item, dict):
            continue

        for action_key, data_dict in item.items():
            # data_dict is, e.g., { PATH: "$install_dir/bin", LD_LIBRARY_PATH: "$install_dir/lib" }
            if not isinstance(data_dict, dict):
                continue

            # For each VAR => VALUE in data_dict, create the right environment object
            for var_name, raw_value in data_dict.items():
                expanded_value = expand_placeholders(str(raw_value), placeholders)

                if action_key == "set":
                    result.append(Set(var_name, expanded_value))
                elif action_key == "prepend":
                    result.append(Prepend(var_name, expanded_value))
                elif action_key == "append":
                    result.append(Append(var_name, expanded_value))
                else:
                    # Unrecognized action, skip or raise an error
                    pass

    return result


class DependencyEntry:
    """
    Represents a single item in the 'dependencies' list.
    It aggregates:
      - recipe name
      - user-specified overrides (e.g., repo_address, branch, location, etc.)
      - environment instructions
      - external-requirements
    """

    def __init__(self, data: Dict[str, Any]):
        """
        data is the raw dict from the YAML describing this dependency.
        """
        # Required fields
        self.recipe: str = data.get("recipe", "")
        if not self.recipe:
            raise ValueError("Each dependency dictionary must have 'recipe' key.")

        # If the user provided a specific name, use it; otherwise fall back to 'recipe'
        self.name: str = data.get("name", self.recipe)

        # Common fields that might appear in many recipes:
        self.location: str = data.get("location", "")
        self.repo_address: str = data.get("repo_address", "")
        self.branch: str = data.get("branch", "")
        self.cmake_flags: str = data.get("cmake_flags", "")
        self.build_threads: Any = data.get("build_threads", None)  # might be an int or str
        self.cxx_standard: Any = data.get("cxx_standard", None)

        # Additional user-specified fields for specialized recipes (pip-install, etc.)
        # We'll just store them in a generic dictionary for retrieval:
        self._raw_data = data

        # Environment block
        self.environment_data = data.get("environment", [])

        # External requirements
        self.external_requirements = data.get("external-requirements", {})
        # e.g. { 'apt': ['libx11-dev', 'libssl-dev'], 'pip': ['numpy>=1.21', 'pyyaml'] }

    def get_env_actions(
            self,
            placeholders: Optional[Dict[str, str]] = None
    ) -> List[EnvironmentManipulation]:
        """
        Parse this dependency's environment block into environment manipulation objects.
        placeholders typically includes { 'install_dir': '...', 'location': '...' }.
        """
        return parse_environment_block(self.environment_data, placeholders or {})

    def get_externals_for(self, manager_key: str) -> List[str]:
        """
        Returns the list of requirements for a given manager, e.g. 'apt', 'dnf', 'pip'.
        """
        if manager_key not in self.external_requirements:
            return []
        reqs = self.external_requirements[manager_key]
        # Typically a list of strings
        return reqs if isinstance(reqs, list) else []

    def get_all_externals(self) -> Dict[str, List[str]]:
        """
        Returns the entire external-requirements dictionary
        (manager -> list of packages).
        """
        return self.external_requirements

    def get_raw_field(self, key: str, default=None):
        """
        Access any arbitrary user field from the YAML, e.g. 'package_name' or 'version'
        for pip-install.
        """
        return self._raw_data.get(key, default)


class EdpmManifest:
    """
    Represents the entire edpm.dependencies.yaml structure:
      - global config
      - array of dependency entries
    """

    def __init__(self, data: Dict[str, Any]):
        # Parse the top-level 'global' object
        self.global_config: Dict[str, Any] = data.get("global", {})
        # E.g. { cxx_standard: 17, build_threads: 8, environment: [...] }

        # Pull out environment instructions from global
        self._global_env_data = self.global_config.get("environment", [])

        # cxx_standard and build_threads are typical fields
        self.cxx_standard: Any = self.global_config.get("cxx_standard")
        self.build_threads: Any = self.global_config.get("build_threads")

        # Parse the 'dependencies' array
        deps_data = data.get("dependencies", [])
        self.dependencies: List[DependencyEntry] = []
        for entry in deps_data:
            if isinstance(entry, str):
                # If the user wrote just "geant4" or something,
                # we interpret it as { recipe: "geant4" }
                entry = {"recipe": entry}
            if not isinstance(entry, dict):
                continue
            dep = DependencyEntry(entry)
            self.dependencies.append(dep)

    @classmethod
    def load(cls, filename: str) -> "EdpmManifest":
        """
        Loads the manifest from a YAML file and returns an EdpmManifest instance.
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"Manifest file not found: {filename}")

        with open(filename, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}

        return cls(raw_data)

    def get_global_env_actions(self) -> List[EnvironmentManipulation]:
        """
        Parse the global environment instructions from 'global.environment'
        into a list of environment manipulation objects.
        """
        # No placeholders at the "global" level typically,
        # unless you define something like $some_global_dir.
        return parse_environment_block(self._global_env_data, {})

    def gather_requirements(self, manager_key: str) -> List[str]:
        """
        Collects all external requirements for a given manager key
        (e.g. 'apt', 'pip', 'conda', 'dnf') across all dependencies.
        """
        all_pkgs = []
        for dep in self.dependencies:
            these_pkgs = dep.get_externals_for(manager_key)
            all_pkgs.extend(these_pkgs)
        return list(set(all_pkgs))  # unique

    def gather_all_requirements(self) -> Dict[str, List[str]]:
        """
        Gathers the union of all external-requirements from all dependencies,
        returning a dict: manager_key -> list of packages
        """
        result_map = {}
        for dep in self.dependencies:
            for manager, pkgs in dep.get_all_externals().items():
                if manager not in result_map:
                    result_map[manager] = []
                result_map[manager].extend(pkgs)

        # Deduplicate each list
        for k in result_map:
            result_map[k] = list(set(result_map[k]))
        return result_map
