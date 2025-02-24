# edpm/engine/components.py

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any
from edpm.engine.commands import run, workdir


# -------------------------------------
# F E T C H E R   I N T E R F A C E
# -------------------------------------

class IFetcher(ABC):
    """
    Base interface for "fetchers" that handle retrieving source code, etc.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Store the config dict for further usage in fetch steps.
        """
        self.config = config

    def preconfigure(self):
        """
        This function can be used to add or refine config entries
        needed before the actual fetch step. Default: do nothing.
        """
        pass

    @abstractmethod
    def fetch(self):
        """
        Actually perform the fetch/cloning/copying step
        (e.g. git clone, tarball download+extract, etc.).
        """
        pass


class GitFetcher(IFetcher):
    """
    A fetcher that uses `git clone`.
    """

    def preconfigure(self):
        """
        Set up config['clone_command'] if not already provided.
        For example, set shallow clone if branch != (master|main).
        """
        # If user doesn't specify 'git_clone_depth', pick default
        if "git_clone_depth" not in self.config:
            is_main_branch = self.config.get("branch", "") not in ["master", "main"]
            self.config["git_clone_depth"] = "--depth 1" if is_main_branch else ""

        # For convenience, build a 'clone_command' string
        self.config["clone_command"] = (
            "git clone {git_clone_depth} -b {branch} {url} {source_path}"
            .format(**self.config)
        )

    def fetch(self):
        repo_url = self.config.get("url", "")
        source_path = self.config.get("source_path", "")
        clone_command = self.config.get("clone_command", "")

        if not repo_url:
            raise ValueError(
                "[GitFetcher] 'url' is missing in config. Current config: {}".format(self.config)
            )

        # If already cloned or source_path is not empty, skip
        if os.path.exists(source_path) and os.path.isdir(source_path) and os.listdir(source_path):
            # The directory exists and is not empty. Do nothing.
            return

        # Ensure the parent directories exist
        run('mkdir -p "{}"'.format(source_path))

        # Execute the clone
        run(clone_command)


class TarballFetcher(IFetcher):
    """
    A fetcher that downloads a tarball from a URL, extracts it,
    and places contents in `source_path`.
    """

    def preconfigure(self):
        # Optionally refine or default something, e.g. local temp name
        if "tar_temp_name" not in self.config:
            self.config["tar_temp_name"] = "/tmp/temp.tar.gz"

    def fetch(self):
        file_url = self.config.get("file_url", "")
        app_path = self.config.get("app_path", "")
        source_path = os.path.join(app_path, "src")  # or use source_path from config

        if not file_url:
            raise ValueError("[TarballFetcher] 'file_url' not specified in config.")

        # Create the source_path
        run('mkdir -p "{}"'.format(source_path))

        download_cmd = f"wget {file_url} -O {self.config['tar_temp_name']}"
        run(download_cmd)

        extract_cmd = f"tar zxvf {self.config['tar_temp_name']} -C {source_path} --strip-components=1"
        run(extract_cmd)


class FileSystemFetcher(IFetcher):
    """
    A fetcher that simply uses a local directory as 'source_path'.
    Optionally can copy it, or do nothing if the user wants to build in-place.
    """

    def fetch(self):
        # The user might store it in config["path"]
        # or config["source_path"]. Decide which to rely on:
        path = self.config.get("path", "")
        source_path = self.config.get("source_path", "")

        if not path:
            raise ValueError("[FileSystemFetcher] No 'path' provided in config.")
        if not os.path.isdir(path):
            raise ValueError(f"[FileSystemFetcher] Provided 'path' is not a directory: {path}")

        # A typical usage: just copy or do nothing. We'll do a naive copy example:
        # If user actually wants an in-place usage, they can skip copying.
        # For demonstration, let's copy to source_path if different:
        if source_path and source_path != path:
            run(f'mkdir -p "{source_path}"')
            # A naive copy with rsync (example):
            copy_cmd = f'rsync -a "{path}/" "{source_path}/"'
            run(copy_cmd)
        else:
            # If user sets them the same, we do nothing.
            pass


def make_fetcher(config: Dict[str, Any]) -> IFetcher:
    """
    Factory that picks the fetcher based on config['fetch'] or tries to autodetect
    from 'fetch' value if it is a URL or local path.
    """
    fetch_val = config.get("fetch", "")
    if not fetch_val:
        # No fetch step
        return None

    # If user explicitly says "git", "tarball", or "filesystem"
    if fetch_val in ("git", "tarball", "filesystem"):
        if fetch_val == "git":
            return GitFetcher(config)
        elif fetch_val == "tarball":
            return TarballFetcher(config)
        else:
            return FileSystemFetcher(config)

    # Otherwise, do an autodetect:
    if fetch_val.endswith(".git"):
        return GitFetcher(config)
    elif fetch_val.endswith(".tar.gz"):
        return TarballFetcher(config)
    else:
        # assume local filesystem
        return FileSystemFetcher(config)


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
        """
        Example: set up a 'build_cmd' or combine flags
        """
        cxx_std = self.config.get("cxx_standard", 17)
        build_threads = self.config.get("build_threads", 4)
        cmake_flags = self.config.get("cmake_flags", "")
        cmake_user_flags = self.config.get("cmake_user_flags", "")
        # Compose a single line. This is up to your usage style:
        self.config["build_cmd"] = (
            f"cmake -DCMAKE_INSTALL_PREFIX={self.config['install_path']} "
            f"-DCMAKE_CXX_STANDARD={cxx_std} "
            f"-DCMAKE_BUILD_TYPE={self.config['cmake_build_type']} "
            f"{cmake_flags} {cmake_user_flags}"
            f"{self.config['source_path']} "
            f"&& cmake --build . -- -j {build_threads} "
            f"&& cmake --build . --target install"
        )

    def build(self):
        build_path = self.config["build_path"]
        run(f'mkdir -p "{build_path}"')
        # We run the build_cmd in that directory
        build_cmd = self.config.get("build_cmd", "")
        if not build_cmd:
            raise ValueError("[CmakeMaker] build_cmd is empty. Did you call preconfigure?")
        run(build_cmd, env_file="env.sh")  # example: we might source env.sh

    def install(self):
        # Actually, we already do `make install` in build_cmd above.
        # But if you want a separate step, do it here.
        pass

    def use_common_dirs_scheme(self):
        """Function sets common directory scheme."""
        if 'app_path' in self.config.keys():
            # where we download the source or clone git
            self.config["fetch_path"] = "{app_path}/src".format(**self.config)

            # The directory with source files for current version
            self.config["source_path"] = "{app_path}/src".format(**self.config)

            # The directory for cmake build
            self.config["build_path"] = "{app_path}/build".format(**self.config)

            # The directory, where binary is installed
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

        conf_cmd = f'./configure {configure_flags}'
        workdir(source_path)
        run(conf_cmd, env_file="env.sh")
        # build
        run(f'make -j {build_threads}', env_file="env.sh")

    def install(self):
        # Typically just "make install"
        app_path = self.config.get("app_path", "")
        source_path = self.config.get("source_path", os.path.join(app_path, "src"))
        run('make install', env_file="env.sh", cwd=source_path)


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
