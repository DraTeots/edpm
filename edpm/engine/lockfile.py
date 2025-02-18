# lockfile.py

import os
from typing import Dict, Any
from ruamel.yaml import YAML

yaml_rt = YAML(typ='rt')

class LockfileConfig:
    DEFAULT_FILE_VERSION = 1

    def __init__(self):
        self.file_path: str = ""
        self.data: Dict[str, Any] = {
            "file_version": self.DEFAULT_FILE_VERSION,
            "top_dir": "",
            "dependencies": {}
        }
        self.is_loaded = False

    def load(self, filepath: str):
        if not os.path.isfile(filepath):
            self.file_path = filepath
            return
        with open(filepath, "r", encoding="utf-8") as f:
            raw = yaml_rt.load(f) or {}
        self.data = raw
        self.file_path = filepath
        self.is_loaded = True

    def save(self, filepath: str = ""):
        if filepath:
            self.file_path = filepath
        if not self.file_path:
            raise ValueError("No file path to save lockfile.")
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml_rt.dump(self.data, f)

    @property
    def top_dir(self) -> str:
        return self.data.get("top_dir", "")

    @top_dir.setter
    def top_dir(self, path: str):
        self.data["top_dir"] = path

    def get_dependency(self, name: str) -> Dict[str, Any]:
        return self.data["dependencies"].get(name, {})

    def is_installed(self, name: str) -> bool:
        dep_data = self.get_dependency(name)
        ipath = dep_data.get("install_path", "")
        return bool(ipath and os.path.isdir(ipath))

    def update_dependency(self, name: str, info: Dict[str, Any]):
        if name not in self.data["dependencies"]:
            self.data["dependencies"][name] = {}
        self.data["dependencies"][name].update(info)

    def get_all_dependencies(self):
        return list(self.data["dependencies"].keys())
