# edpm/engine/planfile.py

import os
import sys
from typing import Any, Dict, List, Optional, Union
from ruamel.yaml import YAML
from edpm.engine.env_gen import EnvironmentManipulation, Set, Prepend, Append
from edpm.engine.config import ConfigNamespace

yaml_rt = YAML(typ='rt')  # round-trip mode

def expand_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    for k, v in placeholders.items():
        text = text.replace(f'${k}', v)
    return text

class EnvironmentBlock:
    """
    Holds a list of environment instructions (set/prepend/append).
    """
    def __init__(self, data: List[Any]):
        # data is an array of objects like:  [{set: {...}}, {prepend: {...}}]
        self.data = data or []

    def parse(self, placeholders: Optional[Dict[str, str]] = None) -> List[EnvironmentManipulation]:
        """
        Convert environment instructions into EnvironmentManipulation objects.
        placeholders can be used to expand e.g. "$install_dir"
        """
        from edpm.engine.env_gen import Set, Prepend, Append
        results: List[EnvironmentManipulation] = []

        if placeholders is None:
            placeholders = {}

        for item in self.data:
            if not isinstance(item, dict):
                # skip or raise error
                continue

            # item is like {"prepend": {"PATH": "$install_dir/bin"}}
            # or {"set": {...}}
            for action_key, kv_dict in item.items():
                if not isinstance(kv_dict, dict):
                    continue
                for var_name, raw_val in kv_dict.items():
                    expanded_val = expand_placeholders(str(raw_val), placeholders)
                    if action_key == "set":
                        results.append(Set(var_name, expanded_val))
                    elif action_key == "prepend":
                        results.append(Prepend(var_name, expanded_val))
                    elif action_key == "append":
                        results.append(Append(var_name, expanded_val))
                    else:
                        pass  # unknown action
        return results


class ConfigBlock:
    """
    A small wrapper for storing fields from the plan.
    E.g. "fetch", "make", "branch", "cmake_flags", etc.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def update(self, other: Dict[str, Any]):
        self.data.update(other)

    def keys(self):
        return self.data.keys()

    def __contains__(self, key):
        return key in self.data


class Dependency:
    """
    Represents one dependency from the plan.

    This new version can either be:
    1) A "baked in" name (like "root" or "geant4"), or
    2) A custom dictionary with 'fetch', 'make', environment, etc.

    We store a ConfigBlock for any data: fetch, make, branch, etc.
    We also store an EnvironmentBlock for environment instructions.
    """

    def __init__(self, name: str, config_data: Dict[str, Any], env_data: List[Any], is_baked_in: bool = False):
        self._name = name
        self._is_baked_in = is_baked_in
        # Put all config fields (fetch, make, branch, etc.) in a single config block
        self.config_block = ConfigBlock(config_data)
        self.env_block_obj = EnvironmentBlock(env_data)

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_baked_in(self) -> bool:
        return self._is_baked_in

    def env_block(self) -> EnvironmentBlock:
        return self.env_block_obj


class PlanFile:
    def __init__(self, raw_data: Dict[str, Any]):
        self.data = raw_data
        if "global" not in self.data:
            self.data["global"] = {}
        if "dependencies" not in self.data:
            self.data["dependencies"] = []

        # Ensure there's a config sub-block in global
        if "config" not in self.data["global"]:
            self.data["global"]["config"] = {
                "build_threads": 4,
                "cxx_standard": 17
            }
        # Similarly ensure there's an environment sub-block in global
        if "environment" not in self.data["global"]:
            self.data["global"]["environment"] = []

    @classmethod
    def load(cls, filename: str) -> "PlanFile":
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"Plan file not found: {filename}")
        yaml_rt.preserve_quotes = True
        with open(filename, "r", encoding="utf-8") as f:
            raw_data = yaml_rt.load(f) or {}
        return cls(raw_data)

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            yaml_rt.dump(self.data, f)

    def global_config_block(self) -> ConfigBlock:
        return ConfigBlock(self.data["global"]["config"])

    def get_global_env_actions(self) -> List[EnvironmentManipulation]:
        block = EnvironmentBlock(self.data["global"]["environment"])
        return block.parse()


    def dependencies(self) -> List[Dependency]:
        """
        Parse the 'dependencies' array into a list[Dependency].
        Each item can be a string (baked-in) or a dictionary (custom).
        """
        deps_list = self.data["dependencies"]
        result: List[Dependency] = []

        for item in deps_list:
            if isinstance(item, str):
                # baked-in recipe, e.g. "root" or "geant4"
                d = Dependency(
                    name=item,
                    config_data={},  # no special config
                    env_data=[],
                    is_baked_in=True
                )
                result.append(d)
            elif isinstance(item, dict):
                # e.g. { "my_packet": { fetch:..., make:..., environment: [...], etc. } }
                # or could be multiple keys if user wrote a short form,  but we assume exactly one top-level key: the name
                # Validate dictionary format for named dependencies
                if len(item) != 1:
                    raise ValueError(
                        f"Malformed dependency entry. Each dependency object must have exactly one top-level key.\n"
                        f"Invalid entry: {item}\n"
                        f"Expected format: {{ <dependency-name>: {{ <config-options> }} }}\n"
                        f"Example: {{ 'myapp': {{ 'recipe': 'cmake', 'repo': 'https://...' }} }}"
                    )

                # Extract dependency name and config
                dep_name, dep_config = next(iter(item.items()))

                # Validate config is a dictionary
                if not isinstance(dep_config, dict):
                    raise ValueError(
                        f"Invalid configuration for dependency '{dep_name}'. "
                        f"Expected dictionary of settings, got {type(dep_config)}.\n"
                        f"Full entry: {item}"
                    )

                # environment might exist or not
                env_data = dep_config.get("environment", [])
                # separate out environment from the rest
                tmp = dict(dep_config)  # shallow copy
                tmp.pop("environment", None)

                d = Dependency(
                    name=dep_name,
                    config_data=tmp,
                    env_data=dep_config,
                    is_baked_in=False
                )
                result.append(d)
            else:
                # unknown type
                pass

        return result

    def has_dependency(self, name: str) -> bool:
        return any(d.name == name for d in self.dependencies())

    def find_dependency(self, name: str) -> Optional[Dependency]:
        for d in self.dependencies():
            if d.name == name:
                return d
        return None
