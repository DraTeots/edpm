# edpm/engine/lockfile.py

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
            "packages": {}
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

    def get_installed_package(self, name: str) -> Dict[str, Any]:
        return self.data["packages"].get(name, {})

    def is_installed(self, name: str) -> bool:
        dep_data = self.get_installed_package(name)
        ipath = dep_data.get("install_path", "")
        return bool(ipath and os.path.isdir(ipath))

    def update_package(self, name: str, info: Dict[str, Any]):
        if name not in self.data["packages"]:
            self.data["packages"][name] = {}
        self.data["packages"][name].update(info)

    def get_installed_packages(self):
        return list(self.data["packages"].keys())

    def remove_package(self, name: str):
        """
        Removes a package from the lock file.
        Note: This method silently ignores attempts to remove non-existent packages.
        """
        if name in self.data["packages"]:
            del self.data["packages"][name]