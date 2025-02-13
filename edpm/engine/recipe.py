# recipe.py

import os
from typing import List, Optional
from edpm.engine.config import ConfigNamespace  # or use a dict if you prefer
from edpm.engine.commands import run, workdir
from edpm.engine.env_gen import Set, Prepend, Append

class Recipe:
    """
    Base class for EDPM recipes.
    A 'Recipe' knows how to download/fetch, build, install, and possibly patch a package.

    Typical usage:
      - config: A ConfigNamespace containing relevant fields (branch, repo_address, etc.).
      - The user calls fetch(), build(), install(), post_install() in order.
      - Optionally override environment or define required_deps, optional_deps.

    Attributes:
      name: short name of the recipe (e.g. 'geant4', 'fastjet')
      config: ConfigNamespace with fields like:
        - app_path, source_path, build_path, install_path
        - branch, repo_address, cmake_flags, etc.
      required_deps, optional_deps: lists of other recipes that this one depends on (for chaining).
    """

    def __init__(self, name: str, config: Optional[ConfigNamespace] = None):
        self.name = name

        # If none provided, create an empty config
        self.config = config if config else ConfigNamespace()
        # Guarantee these core fields exist (can be overwritten by user or manifest):
        if "app_name" not in self.config:
            self.config["app_name"] = self.name
        if "app_path" not in self.config:
            self.config["app_path"] = ""

        # Dependencies
        self.required_deps: List[str] = []
        self.optional_deps: List[str] = []

    ############################
    # Lifecycle / Steps
    ############################

    def fetch(self):
        """Download or clone the source. Subclasses override if needed."""
        pass

    def patch(self):
        """Apply patches if needed."""
        pass

    def build(self):
        """Build or compile the source. Subclasses override if needed."""
        pass

    def install(self):
        """Install the final artifacts. Subclasses override if needed."""
        pass

    def post_install(self):
        """Any final steps after install. e.g. fix perms, do some logging, etc."""
        pass

    def run_full_pipeline(self):
        """A convenience method to run fetch->patch->build->install->post_install in order."""
        self.fetch()
        self.patch()
        self.build()
        self.install()
        self.post_install()

    ############################
    # Helpers
    ############################

    def use_common_dirs_scheme(self):
        """
        Fill config with standard directory structure:
          app_path/src/{branch}  -> source_path
          app_path/build/{branch} -> build_path
          app_path/{app_name}-{branch} -> install_path
        """
        # short references
        app_path = self.config["app_path"]
        branch = self.config.get("branch", "master")
        app_name = self.config["app_name"]

        self.config["download_path"] = f"{app_path}/src"
        self.config["source_path"] = f"{app_path}/src/{branch}"
        self.config["build_path"] = f"{app_path}/build/{branch}"
        self.config["install_path"] = f"{app_path}/{app_name}-{branch}"

    def source_dir_is_not_empty(self):
        src = self.config.get("source_path", "")
        return os.path.isdir(src) and os.listdir(src)

    def app_path(self) -> str:
        return self.config.get("app_path", "")

    def source_path(self) -> str:
        return self.config.get("source_path", "")

    def build_path(self) -> str:
        return self.config.get("build_path", "")

    def install_path(self) -> str:
        return self.config.get("install_path", "")

    def gen_env(self, installed_data: dict) -> List:
        """
        Generate environment steps (Set, Prepend, Append) for shell scripts or in-process.
        Subclasses can override to define how environment variables are set after installation.

        'installed_data' might be something like:
          {
            "install_path": "/opt/something",
            ...
          }
        The default base recipe does nothing.
        """
        return []


class GitCmakeRecipe(Recipe):
    """
    A generic "Git + CMake" recipe.
    By default:
      - fetch() => clone from repo_address at given branch
      - build() => run cmake & build
      - install() => `make install`
      - gen_env() => sets PATH, LD_LIBRARY_PATH, etc. if desired
    """

    def __init__(self, name: str, config: Optional[ConfigNamespace] = None):
        super().__init__(name, config)
        # Provide some defaults if not set:
        if "branch" not in self.config:
            self.config["branch"] = "master"
        if "repo_address" not in self.config:
            self.config["repo_address"] = ""
        if "cmake_flags" not in self.config:
            self.config["cmake_flags"] = ""
        if "cmake_build_type" not in self.config:
            self.config["cmake_build_type"] = "RelWithDebInfo"
        if "build_threads" not in self.config:
            self.config["build_threads"] = 4
        if "cxx_standard" not in self.config:
            self.config["cxx_standard"] = 17

    def fetch(self):
        self.use_common_dirs_scheme()

        repo = self.config["repo_address"]
        if not repo:
            raise ValueError(f"{self.name} recipe: 'repo_address' is not specified")

        branch = self.config["branch"]
        clone_depth = self.config.get("git_clone_depth", "")
        if not clone_depth:
            # shallow if the branch is not 'master' or 'main'
            if branch not in ["master", "main"]:
                clone_depth = "--depth 1"
                self.config["git_clone_depth"] = clone_depth

        src = self.config["source_path"]
        if os.path.exists(src) and os.path.isdir(src) and os.listdir(src):
            # Already cloned, skip
            return
        else:
            run(f'mkdir -p "{src}"')  # ensure directory
            # run actual clone
            run(f'git clone {clone_depth} -b {branch} {repo} "{src}"')

    def build(self):
        src = self.config["source_path"]
        bld = self.config["build_path"]
        run(f'mkdir -p "{bld}"')
        workdir(bld)

        cxx_standard = self.config["cxx_standard"]
        build_type = self.config["cmake_build_type"]
        cmake_flags = self.config["cmake_flags"]
        install_dir = self.config["install_path"]
        threads = self.config["build_threads"]

        cmake_cmd = (
            f'cmake -Wno-dev '
            f'-DCMAKE_CXX_STANDARD={cxx_standard} '
            f'-DCMAKE_BUILD_TYPE={build_type} '
            f'-DCMAKE_INSTALL_PREFIX="{install_dir}" '
            f'{cmake_flags} "{src}"'
        )
        run(cmake_cmd)
        run(f'cmake --build . -- -j {threads}')

    def install(self):
        bld = self.config["build_path"]
        workdir(bld)
        run('cmake --build . --target install')

    def gen_env(self, installed_data: dict):
        """
        Suppose we want to set PATH, LD_LIBRARY_PATH.
        installed_data should contain "install_path": <where it ended up>
        """
        ipath = installed_data.get("install_path", "")
        if not ipath:
            return []
        bin_dir = os.path.join(ipath, "bin")
        lib_dir = os.path.join(ipath, "lib")

        return [
            Prepend("PATH", bin_dir),
            Prepend("LD_LIBRARY_PATH", lib_dir),
        ]


class ManualRecipe(Recipe):
    """
    For pre-installed / external packages. No fetch/build.
    Just sets environment (like 'root', 'python', etc.).
    """

    def __init__(self, name: str, config: Optional[ConfigNamespace] = None):
        super().__init__(name, config)

    def run_full_pipeline(self):
        """
        We skip fetch/build/install for a pre-installed package.
        """
        pass

    def gen_env(self, installed_data: dict):
        """
        For an external package, we expect the user has 'location' in config.
        We'll set environment from that.
        """
        loc = self.config.get("location", "")
        if not loc:
            return []
        return [
            Prepend("PATH", os.path.join(loc, "bin")),
            Prepend("LD_LIBRARY_PATH", os.path.join(loc, "lib")),
        ]


class TarballRecipe(Recipe):
    """
    Example: a tarball-based recipe (like your FastJet example).
    We define fetch() as: wget the tarball, extract it,
    build() as: run ./configure + make, etc.
    """

    def fetch(self):
        self.use_common_dirs_scheme()
        branch = self.config.get("branch", "v1.0.0")
        repo_addr = self.config.get("repo_address", "")
        if not repo_addr:
            raise ValueError("TarballRecipe requires 'repo_address' to be set")
        src = self.config["source_path"]
        run(f'mkdir -p "{src}"')
        workdir(src)

        # e.g. wget ...
        run(f'wget {repo_addr.format(branch=branch)} -O {branch}.tar.gz')
        run(f'tar zxvf {branch}.tar.gz --strip-components=1')

    def build(self):
        src = self.config["source_path"]
        workdir(src)
        threads = self.config.get("build_threads", 4)
        inst = self.config["install_path"]
        run(f'./configure --prefix="{inst}"')
        run(f'make -j {threads}')

    def install(self):
        src = self.config["source_path"]
        workdir(src)
        run(f'make install')

    def gen_env(self, installed_data: dict):
        path = installed_data.get("install_path", "")
        return [
            Prepend("PATH", os.path.join(path, "bin")),
            Prepend("LD_LIBRARY_PATH", os.path.join(path, "lib")),
        ]
