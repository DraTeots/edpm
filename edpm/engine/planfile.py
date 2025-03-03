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

class PlanPackage:
    """
    Represents one dependency from the plan.

    This can be:
      1) A "baked in" name (like "root" or "geant4"), possibly with @version
      2) A custom dictionary with 'fetch', 'make', environment, etc.

    `config` is just a dict, no separate ConfigBlock anymore.
    `env_block_obj` is an EnvironmentBlock for environment instructions if present.
    """

    def __init__(self, name: str, config_data: Dict[str, Any], env_data: List[Any], is_baked_in: bool = False):
        self._name = name
        self._is_baked_in = is_baked_in
        # config is a raw dict of fields (fetch, make, branch, etc.)
        self.config = config_data
        # environment instructions for just this package
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
        self.data = raw_data or {}

        # Ensure 'global' sub-dict
        if "global" not in self.data:
            self.data["global"] = {}

        # Ensure 'packages' is a list
        if "packages" not in self.data or not isinstance(self.data["packages"], list):
            self.data["packages"] = []

        # Ensure there's a 'config' in global
        if "config" not in self.data["global"]:
            self.data["global"]["config"] = {
                "build_threads": 4,
                "cxx_standard": 17
            }

        # Ensure there's an 'environment' in global
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

    def global_config(self) -> Dict[str, Any]:
        """
        Return the raw dict for global config (instead of a ConfigBlock).
        """
        return self.data["global"]["config"]

    def get_global_env_actions(self) -> List[GeneratorStep]:
        block = EnvironmentBlock(self.data["global"]["environment"])
        return block.parse()

    def packages(self) -> List[PlanPackage]:
        """
        Parse the 'packages' array into a list[PlanPackage].
        Each item can be:
          - A string: "root" or "geant4@v11.03"
          - A dict: { "mydep": { fetch:..., environment:..., etc. } }
        """
        pkg_list = self.data["packages"]
        result: List[PlanPackage] = []

        for item in pkg_list:
            if isinstance(item, str):
                # e.g. "root" or "geant4@v11.03"
                pkg_name = item
                version_part = ""
                if '@' in pkg_name:
                    parts = pkg_name.split('@', 1)
                    pkg_name = parts[0]
                    version_part = parts[1]

                config_data = {}
                if version_part:
                    config_data["version"] = version_part

                p = PlanPackage(
                    name=pkg_name,
                    config_data=config_data,
                    env_data=[],
                    is_baked_in=True
                )
                result.append(p)

            elif isinstance(item, dict):
                # e.g. { "mylib": { fetch:..., environment: [...], etc. } }
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
                # shallow copy so we can remove environment key
                tmp_config = dict(dep_config)
                tmp_config.pop("environment", None)

                p = PlanPackage(
                    name=dep_name,
                    config_data=tmp_config,
                    env_data=env_data,
                    is_baked_in=False
                )
                result.append(p)
            else:
                raise ValueError(f"Invalid package entry: {item} (type {type(item)})")

        return result

    def has_package(self, name: str) -> bool:
        """
        True if a package with name 'name' is in the plan.
        """
        return any(p.name == name for p in self.packages())

    def find_package(self, name: str) -> Optional[PlanPackage]:
        for p in self.packages():
            if p.name == name:
                return p
        return None

    def add_package(self, new_entry: Any):
        """
        Append a new package item (string or dict) to self.data["packages"].
        Must remain a list. Then the user can call save() to persist.
        """
        if not isinstance(self.data["packages"], list):
            self.data["packages"] = []

        self.data["packages"].append(new_entry)
