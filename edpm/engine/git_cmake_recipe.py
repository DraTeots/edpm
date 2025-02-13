"""
This is a generic recepie for git + cmake project

"""

import os

from edpm.engine.commands import run, workdir
from edpm.engine.env_gen import Set, Append
from edpm.engine.recipe import Recipe


class GitCmakeRecipe(Recipe):
    """Provides data for building and installing Genfit framework
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self, name):
        """Generic init"""

        super(GitCmakeRecipe, self).__init__(name)

        # Set initial values for parent class and self
        self.config['branch'] = 'master'
        self.config['repo_address'] = ''
        self.config['cmake_flags'] = ''
        self.config['cmake_custom_flags'] = ''

    def setup(self, db):
        """Sets all variables like source dirs, build dirs, etc"""

        #
        # use_common_dirs_scheme sets standard package variables:
        # source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
        # build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
        # install_path = {app_path}/root-{version}         # Where the binary installation is
        self.use_common_dirs_scheme()

        #
        # Check we have a repo address
        if not self.config['repo_address']:
            raise ValueError("config 'repo_address' must be set. "
                             "Either in recepie or later with 'edpm config <packet> repo_address=<value>'")

        #
        # Git download link. Clone with shallow copy
        if "git_clone_depth" not in self.config.keys():
            is_main_branch = self.config.get("branch", "") not in ["master", "main"]
            self.config["git_clone_depth"] = "--depth 1" if is_main_branch else ""

        # Add RelWithDebInfo for cmake by default
        cmake_build_type = self.config.get("cmake_build_type", "")
        if not cmake_build_type:
            self.config['cmake_build_type'] = "RelWithDebInfo"

        #print("!!!!!!!!!!!!!!!!!!!!!!", self.config['branch'])
        #print("!!!!!!!!!!!!!!!!!!!!!!", self.config['repo_address'])
        self.clone_command = "git clone {git_clone_depth} -b {branch} {repo_address} {source_path}"\
            .format(**self.config)

        # cmake command:
        # the  -Wno-dev  flag is to ignore the project developers cmake warnings for policy CMP0075
        self.build_cmd = "cmake -Wno-dev " \
                         "-DCMAKE_INSTALL_PREFIX={install_path} -DCMAKE_CXX_STANDARD={cxx_standard} " \
                         "-DCMAKE_BUILD_TYPE={cmake_build_type} " \
                         "{cmake_flags} {cmake_custom_flags} {source_path}" \
                         "&& cmake --build . -- -j {build_threads}" \
                         "&& cmake --build . --target install" \
                         .format(**self.config)

    def step_install(self):
        self.step_clone()
        self.step_build()

    def step_clone(self):
        """Clones JANA from github mirror"""

        # Check the directory exists and not empty
        if os.path.exists(self.source_path) and os.path.isdir(self.source_path) and os.listdir(self.source_path):
            # The directory exists and is not empty. Nothing to do
            return
        else:
            # Create the directory
            run('mkdir -p {}'.format(self.source_path))

        # Execute git clone command
        run(self.clone_command)

    def step_build(self):
        """Builds from the ground"""

        # Create build directory
        run('mkdir -p {}'.format(self.build_path))

        # go to our build directory
        workdir(self.build_path)

        # run scons && scons install
        run(self.build_cmd)

    def step_reinstall(self):
        """Delete everything and start over"""

        # clear sources directories if needed
        run('rm -rf {}'.format(self.app_path))

        # Now run build root
        self.step_install()