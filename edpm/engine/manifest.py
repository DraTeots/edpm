# manifest.py

import os
from typing import Any, Dict, List, Optional

# Instead of PyYAML, use ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from edpm.engine.env_gen import EnvironmentManipulation, Append, Prepend, Set

yaml_rt = YAML(typ='rt')  # rt = round-trip mode

def expand_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    if not text:
        return text
    for k, v in placeholders.items():
        text = text.replace(f'${k}', v)
    return text

class EnvironmentBlock:
    def __init__(self, data: List[Any]):
        # In ruamel.yaml, data might be a CommentedSeq or plain list
        self.data = data or []

    def parse(self, placeholders: Optional[Dict[str, str]] = None) -> List[EnvironmentManipulation]:
        if placeholders is None:
            placeholders = {}
        result = []
        for item in self.data:
            if not isinstance(item, dict):
                continue
            for action_key, kv_dict in item.items():
                if not isinstance(kv_dict, dict):
                    continue
                for var_name, raw_val in kv_dict.items():
                    expanded = expand_placeholders(str(raw_val), placeholders)
                    if action_key == "set":
                        result.append(Set(var_name, expanded))
                    elif action_key == "prepend":
                        result.append(Prepend(var_name, expanded))
                    elif action_key == "append":
                        result.append(Append(var_name, expanded))
                    else:
                        pass
        return result

class ConfigBlock:
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value

    def update(self, other: Dict[str, Any]):
        self.data.update(other)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def keys(self):
        return self.data.keys()

    def __contains__(self, key):
        return key in self.data

class Dependency:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        if "recipe" not in self.data:
            raise ValueError("Dependency must have a 'recipe' field.")
        if "environment" not in self.data:
            self.data["environment"] = []
        if "config" not in self.data:
            self.data["config"] = {}
        if "external-requirements" not in self.data:
            self.data["external-requirements"] = {}

    @property
    def name(self) -> str:
        return self.data.get("name", self.data["recipe"])

    @property
    def recipe(self) -> str:
        return self.data["recipe"]

    @property
    def config_block(self) -> ConfigBlock:
        return ConfigBlock(self.data["config"])

    @property
    def env_block(self) -> EnvironmentBlock:
        return EnvironmentBlock(self.data["environment"])

    @property
    def externals(self) -> Dict[str, List[str]]:
        return self.data["external-requirements"]

    def to_dict(self) -> Dict[str, Any]:
        return self.data

class EdpmManifest:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        if "global" not in self.data:
            self.data["global"] = {}
        if "dependencies" not in self.data:
            self.data["dependencies"] = []
        if "config" not in self.data["global"]:
            self.data["global"]["config"] = {}
        if "environment" not in self.data["global"]:
            self.data["global"]["environment"] = []

    @classmethod
    def load(cls, filename: str) -> "EdpmManifest":
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"Manifest file not found: {filename}")
        with open(filename, "r", encoding="utf-8") as f:
            raw_data = yaml_rt.load(f)  # load with ruamel.yaml
        if not raw_data:
            raw_data = {}
        return cls(raw_data)

    def save(self, filename: str):
        """
        Write self.data back to a YAML file, preserving comments and structure.
        """
        with open(filename, "w", encoding="utf-8") as f:
            yaml_rt.dump(self.data, f)

    @property
    def global_config_block(self) -> ConfigBlock:
        return ConfigBlock(self.data["global"]["config"])

    @property
    def global_env_block(self) -> EnvironmentBlock:
        return EnvironmentBlock(self.data["global"]["environment"])

    @property
    def dependencies(self) -> List[Dependency]:
        deps_list = self.data["dependencies"]
        result = []
        for item in deps_list:
            if isinstance(item, str):
                item = {"recipe": item, "environment": [], "config": {}}
            result.append(Dependency(item))
        return result

    def has_dependency(self, name: str) -> bool:
        return any(d.name == name for d in self.dependencies)

    def find_dependency(self, name: str) -> Optional[Dependency]:
        for d in self.dependencies:
            if d.name == name:
                return d
        return None

    def add_dependency(self, name: str, recipe: str, **kwargs):
        new_dep = {
            "recipe": recipe,
            "name": name,
            "config": {},
            "environment": [],
            "external-requirements": {}
        }
        for k, v in kwargs.items():
            if k == "environment":
                new_dep["environment"] = v
            elif k == "config":
                new_dep["config"] = v
            else:
                new_dep[k] = v
        self.data["dependencies"].append(new_dep)

    def get_global_env_actions(self) -> List[EnvironmentManipulation]:
        return self.global_env_block.parse()

    def gather_requirements(self, manager_key: str) -> List[str]:
        pkgs = []
        for d in self.dependencies:
            reqs = d.externals.get(manager_key, [])
            pkgs.extend(reqs)
        return list(set(pkgs))

    def gather_all_requirements(self) -> Dict[str, List[str]]:
        result = {}
        for dep in self.dependencies:
            for mgr_key, items in dep.externals.items():
                if mgr_key not in result:
                    result[mgr_key] = []
                result[mgr_key].extend(items)
        for mk in result:
            result[mk] = list(set(result[mk]))
        return result
