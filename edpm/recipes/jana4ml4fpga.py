"""
https://github.com/JeffersonLab/JANA4ML4FPGA


"""

import os

from edpm.engine.env_gen import Set, Prepend
from edpm.engine.recipe import Recipe
from edpm.engine.commands import run, env, workdir


class Jana4ml4fpgaRecipe(Recipe):
    """Provides data for building and installing JANA framework

    PackageInstallationContext is located in recipe.py and contains the next standard package variables:

    version      = 'v{}-{:02}-{:02}'                 # Stringified version. Used to create directories and so on
    glb_app_path = Context.work_dir                  # The directory where all other packets are installed
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        """
        """
        super(Jana4ml4fpgaRecipe, self).__init__('jana4ml4fpga')
        self.config['repo_address'] = 'https://github.com/JeffersonLab/JANA4ML4FPGA'
        self.required_deps = ['root', 'jana2']
        self.config['branch'] = 'main'

    def setup(self, db):
        """Sets all variables like source dirs, build dirs, etc"""

        # Git download link. Clone with shallow copy
        self.config['source_path'] = "{app_path}/jana4ml4fpga-{branch}".format(**self.config)

        # The directory for cmake build
        self.config['build_path'] = "{app_path}/jana4ml4fpga-{branch}/cmake-build-debug".format(**self.config)

        self.config['install_path'] = "{app_path}/jana4ml4fpga-{branch}".format(**self.config)

        self.config['clone_command'] = "git clone -b {branch} {repo_address} {source_path}" \
            .format(**self.config)

        # cmake command:
        # the  -Wno-dev  flag is to ignore the project developers cmake warnings for policy CMP0075
        self.config['build_cmd'] = "cmake -DCMAKE_INSTALL_PREFIX={install_path} -DCMAKE_CXX_STANDARD={cxx_standard} {source_path}" \
                                   "&& cmake --build . -- -j {build_threads}" \
                                   "&& cmake --build . --target install" \
            .format(**self.config)

    def step_install(self):
        self.step_clone()
        self.step_build()

    def step_clone(self):
        """Clones JANA from github mirror"""

        # Check the directory exists and not empty
        if self.source_dir_is_not_empty():
            return  # The directory exists and is not empty. Nothing to do

        run('mkdir -p {source_path}'.format(**self.config))   # Create the directory
        run(self.config['clone_command'])                               # Execute git clone command

    def step_build(self):
        """Builds JANA from the ground"""

        # Create build directory
        run('mkdir -p {}'.format(self.config['build_path']))

        # go to our build directory
        workdir(self.config['build_path'])

        # run scons && scons install
        run(self.config['build_cmd'])

    def step_reinstall(self):
        """Delete everything and start over"""

        # clear sources directories if needed
        run('rm -rf {}'.format(self.app_path))

        # Now run build root
        self.step_install()

    @staticmethod
    def gen_env(data):
        """Generates environments to be set"""
        install_path = data['install_path']
        yield Set('jana4ml4fpga_HOME', install_path)
        yield Prepend('JANA_PLUGIN_PATH', os.path.join(install_path, 'plugins'))
        yield Prepend('PATH', os.path.join(install_path, 'bin'))

        lib_path = os.path.join(install_path, 'lib')  # on some platforms
        lib64_path = os.path.join(install_path, 'lib64')  # on some platforms

        if os.path.isdir(lib64_path):
            yield Prepend('LD_LIBRARY_PATH', lib64_path)
        else:
            yield Prepend('LD_LIBRARY_PATH', lib_path)

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
            'ubuntu18': "libspdlog-dev",
            'ubuntu22': "libspdlog-dev",
            'centos7': "spdlog-devel",
            'centos8': "spdlog-devel"
    }

    # Flags that can me made in cmake
    cmake_deps_flag_names = {
        "root": "ROOT_DIR",             # Cern root installation
        "jana": 'JANA_DIR',             # JANA2 installation directory
        'genfit': 'GENFIT_DIR',         # Genfit2  installation directory
        'eic-smear': 'EIC_SMEAR_DIR',   # EIC-smear smearing packet
        'hepmc': 'HEPMC_DIR'
    }

