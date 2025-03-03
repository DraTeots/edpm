"""
https://github.com/JeffersonLab/JANA4ML4FPGA


"""
import os

from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.generators.steps import EnvSet, EnvPrepend
from edpm.engine.commands import is_not_empty_dir
from distutils.dir_util import mkpath

class Jana4ml4fpgaRecipe(ComposedRecipe):
    """
    Installs the JANA4ML4FPGA project from Git + CMake.

    Original repo: https://github.com/JeffersonLab/JANA4ML4FPGA
    """

    # OS dependencies (if you want to use `edpm req`):
    os_dependencies = {
        'required': {
            'ubuntu18': "libspdlog-dev",
            'ubuntu22': "libspdlog-dev",
            'centos7':  "spdlog-devel",
            'centos8':  "spdlog-devel"
        },
        'optional': {}
    }

    # Possibly define cmake_deps_flag_names if you use them in your build, e.g. mapping 'root' -> 'ROOT_DIR'
    cmake_deps_flag_names = {
        "root": "ROOT_DIR",
        "jana": "JANA_DIR",
        "genfit": "GENFIT_DIR",
        "eic-smear": "EIC_SMEAR_DIR",
        "hepmc": "HEPMC_DIR"
    }

    def __init__(self, config):
        # Provide minimal defaults; user can override in plan
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/JeffersonLab/JANA4ML4FPGA.git',
            'branch': 'main',
            'cxx_standard': 17,
            'cmake_build_type': 'RelWithDebInfo',
            'build_threads': 4,
            # 'cmake_flags': '',     # user can override or set in plan
        }
        super().__init__(name='jana4ml4fpga', config=config)

    def preconfigure(self):
        """
        Combine user-provided cmake flags with defaults for Jana4ml4fpga.
        """
        cxx_std = self.config.get('cxx_standard', 17)
        # We can override the 'source_path' and 'build_threads' as needed
        source_path = self.config.get('source_path', "")
        cmake_build_type = self.config.get('cmake_build_type', 'RelWithDebInfo')
        build_threads = self.config.get('build_threads', 4)

        # Merge user cmake_flags or cmake_custom_flags
        user_flags = self.config.get('cmake_flags', "")
        custom_flags = self.config.get('cmake_custom_flags', "")

        # Construct final cmake invocation
        # The typical pattern is:
        #   cmake -DCMAKE_INSTALL_PREFIX=... -DCMAKE_CXX_STANDARD=... <source> && cmake --build . ...
        # We'll store them in 'cmake_flags' for ComposedRecipe to use
        line = [
            f"-DCMAKE_CXX_STANDARD={cxx_std}",
            f"-DCMAKE_BUILD_TYPE={cmake_build_type}",
            f"-DCMAKE_INSTALL_PREFIX={self.config.get('install_path','')}",
            source_path  # last argument to cmake is the source path
        ]
        merged_flags = " ".join([user_flags, custom_flags, " ".join(line)]).strip()
        self.config['cmake_flags'] = merged_flags
        self.config['build_threads'] = build_threads

    def fetch(self):
        """
        Shallow Git clone if requested; skip if source_path is non-empty.
        """
        source_path = self.config.get('source_path', "")
        if source_path and is_not_empty_dir(source_path):
            return  # Already exists

        from edpm.engine.commands import run
        shallow_flag = ""
        if self.config.get('shallow', False):
            shallow_flag = "--depth 1"
        branch = self.config.get('branch', 'main')
        url = self.config.get('url')
        clone_cmd = f'git clone {shallow_flag} -b {branch} {url} "{source_path}"'
        mkpath(source_path)
        run(clone_cmd)

    @staticmethod
    def gen_env(data):
        """
        Sets environment variables for JANA4ML4FPGA,
        including PATH, JANA_PLUGIN_PATH, and library paths.
        """
        install_path = data['install_path']
        yield EnvSet('jana4ml4fpga_HOME', install_path)
        yield EnvPrepend('JANA_PLUGIN_PATH', os.path.join(install_path, 'plugins'))
        yield EnvPrepend('PATH', os.path.join(install_path, 'bin'))

        lib_path = os.path.join(install_path, 'lib')
        lib64_path = os.path.join(install_path, 'lib64')
        if os.path.isdir(lib64_path):
            yield EnvPrepend('LD_LIBRARY_PATH', lib64_path)
        else:
            yield EnvPrepend('LD_LIBRARY_PATH', lib_path)

    def patch(self):
        """
        If any patch steps are needed, place them here.
        """
        pass

    def post_install(self):
        """
        Any post-install steps if needed.
        """
        pass


