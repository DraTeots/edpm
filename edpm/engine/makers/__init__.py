# edpm/engine/components.py

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any
from edpm.engine.commands import run, workdir

# -------------------------------------
# M A K E R   I N T E R F A C E
# -------------------------------------

class IMaker(ABC):
    """
    Base interface for "makers" that handle the build+install steps
    (cmake, autotools, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def preconfigure(self):
        """
        This method can do any final arrangement of config data
        before build/install. E.g. composing final build_cmd, etc.
        """
        pass

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def install(self):
        pass


class CmakeMaker(IMaker):
    """
    Example maker that uses CMake to build and install.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Provide some default build_type
        self.config.setdefault("cmake_build_type", "RelWithDebInfo")
        # We might prefer a subdir approach:
        # e.g., source_path = {app_path}/src/{branch}
        # build_path = {app_path}/build/{branch}
        # install_path = {app_path}/{app_name}-{branch}
        # We'll do that in preconfigure or below:

    def preconfigure(self):
        """Set configure and build CMD-s"""
        
        defaults = {
            "cxx_standard": 20,
            "build_threads": 4,
            "cmake_flags": "",
            "cmake_user_flags": ""
        }
        cfg_with_defs = {**defaults, **self.config}

        self.config["configure_cmd"] = (
            "cmake -B {build_path} "
            "-DCMAKE_INSTALL_PREFIX={install_path} "
            "-DCMAKE_CXX_STANDARD={cxx_standard} "
            "-DCMAKE_BUILD_TYPE={cmake_build_type} "
            "{cmake_flags} "
            "{cmake_user_flags} "
            "{source_path} "
        ).format(**cfg_with_defs)


        self.config["build_cmd"] = "cmake --build {build_path} --parallel {build_threads}".format(**cfg_with_defs)
        self.config["install_cmd"] = "cmake --build {build_path} --target install".format(**cfg_with_defs)
        from pprint import pprint
        print("------- cmake-maker preconfigure result: ---------")
        pprint(self.config)
        print("--------------------------------------------------")

    def build(self):

        # Check we have preconfigured everything:
        if not self.config.get("configure_cmd", ""):
            raise ValueError("[CmakeMaker] build_cmd is empty. Did you call preconfigure?")

        # Create the build_path if it doesn't exist yet
        run(f'mkdir -p "{self.config["build_path"]}"')

        # We need an environment to configure/build:
        env_file_bash = self.config["env_file_bash"]
        if not os.path.isfile(env_file_bash):
            raise FileNotFoundError(f"[CmakeMaker] Env file does not exist: {env_file_bash}")

        run(self.config['configure_cmd'], env_file=env_file_bash)
        run(self.config['build_cmd'], env_file=env_file_bash)

    def install(self):
        """Install the packet"""
        install_cmd = self.config.get("install_cmd", "")
        run(install_cmd, env_file=self.config["env_file_bash"])

    def use_common_dirs_scheme(self):
        """Function sets a common directory scheme."""
        if 'app_path' in self.config:
            # where we download the source or clone git
            if not 'fetch_path' in self.config:
                self.config["fetch_path"] = "{app_path}/src".format(**self.config)

            # The directory with source files for the current version
            if not "source_path" in self.config:
                self.config["source_path"] = "{app_path}/src".format(**self.config)

            # The directory for cmake build
            if not "build_path" in self.config:
                self.config["build_path"] = "{app_path}/build".format(**self.config)

            # The directory, where binary is installed
            if not "install_path" in self.config:
                self.config["install_path"] = "{app_path}/{app_name}-install".format(**self.config)


class AutotoolsMaker(IMaker):
    """
    Example maker that uses the Autotools flow:
      ./configure && make && make install
    """

    def preconfigure(self):
        # Possibly combine or default flags
        self.config.setdefault("configure_flags", "")
        self.config.setdefault("build_threads", 4)

    def build(self):
        app_path = self.config.get("app_path", "")
        source_path = self.config.get("source_path", os.path.join(app_path, "src"))
        configure_flags = self.config["configure_flags"]
        build_threads = self.config["build_threads"]

        env_file_bash = self.config["env_file_bash"]
        if not os.path.isfile(env_file_bash):
            raise FileNotFoundError(f"[CmakeMaker] Env file does not exist: {env_file_bash}")

        workdir(source_path)

        run(f'./configure {configure_flags}', env_file=env_file_bash)
        # build
        run(f'make -j {build_threads}', env_file=env_file_bash)

    def install(self):
        # Typically just "make install"
        app_path = self.config.get("app_path", "")
        source_path = self.config.get("source_path", os.path.join(app_path, "src"))
        run('make install', env_file="env.sh")


def make_maker(config: Dict[str, Any]) -> IMaker:
    """
    Factory that picks the maker based on config['make'] or returns None if no build step.
    """
    val = config.get("make", None)
    if not val:
        return None  # no build step at all

    if val == "cmake":
        return CmakeMaker(config)
    elif val in ("autotools", "automake"):
        return AutotoolsMaker(config)
    else:
        # Could handle more or raise an error for unknown
        raise ValueError(f"[make_maker] Unknown build system: '{val}'.")