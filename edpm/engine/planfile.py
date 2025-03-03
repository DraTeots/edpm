# edpm/engine/planfile.py

import os
from typing import Any, Dict, List, Optional
from ruamel.yaml import YAML
from edpm.engine.generators.steps import GeneratorStep

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

    def parse(self, placeholders: Optional[Dict[str, str]] = None) -> List[GeneratorStep]:
        """
        Convert environment instructions into GeneratorStep objects.
        placeholders can be used to expand e.g. "$install_dir"
        """
        from edpm.engine.generators.steps import EnvSet, EnvPrepend, EnvAppend
        results: List[GeneratorStep] = []

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
                        results.append(EnvSet(var_name, expanded_val))
                    elif action_key == "prepend":
                        results.append(EnvPrepend(var_name, expanded_val))
                    elif action_key == "append":
                        results.append(EnvAppend(var_name, expanded_val))
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


class PlanPackage:
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
        if "packages" not in self.data:
            self.data["packages"] = []

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

    def get_global_env_actions(self) -> List[GeneratorStep]:
        block = EnvironmentBlock(self.data["global"]["environment"])
        return block.parse()


    def packages(self) -> List[PlanPackage]:
        """
        Parse the 'packages' array into a list[PlanPackage].
        Each item can be:
          1) A string (baked-in), possibly with @version. e.g. "geant4@v11.03"
          2) A dictionary of form { "mydep": { fetch:..., make:..., environment: [...], etc. }}
        """
        packages = self.data["packages"] if self.data["packages"] else []
        result: List[PlanPackage] = []

        for item in packages:
            if isinstance(item, str):
                # e.g. "root" or "geant4@v11.03"
                pkg_name = item
                version_part = ""

                # If we have "root@v6.32.0", parse out the version
                if '@' in pkg_name:
                    parts = pkg_name.split('@', 1)
                    pkg_name = parts[0]
                    version_part = parts[1]

                # Store version in config_data if present
                config_data = {}
                if version_part:
                    config_data["version"] = version_part

                d = PlanPackage(
                    name=pkg_name,
                    config_data=config_data,
                    env_data=[],
                    is_baked_in=True
                )
                result.append(d)

            elif isinstance(item, dict):
                # e.g. { "my_packet": {...} }
                if len(item) != 1:
                    raise ValueError(
                        f"Malformed dependency entry. Must have exactly one top-level key.\n"
                        f"Invalid entry: {item}"
                    )

                dep_name, dep_config = next(iter(item.items()))
                if not isinstance(dep_config, dict):
                    raise ValueError(
                        f"Invalid config for dependency '{dep_name}'. Must be a dictionary.\n"
                        f"Got: {type(dep_config)}"
                    )

                env_data = dep_config.get("environment", [])
                tmp = dict(dep_config)  # shallow copy
                tmp.pop("environment", None)

                d = PlanPackage(
                    name=dep_name,
                    config_data=tmp,
                    env_data=env_data,
                    is_baked_in=False
                )
                result.append(d)

            else:
                # Unknown type
                raise ValueError(f"Invalid package entry type: {type(item)}. Entry: {item}")

        return result


    def has_package(self, name: str) -> bool:
        return any(d.name == name for d in self.packages())

    def find_package(self, name: str) -> Optional[PlanPackage]:
        for d in self.packages():
            if d.name == name:
                return d
        return None
