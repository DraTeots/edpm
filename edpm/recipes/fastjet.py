"""
This file provides information of how to build and configure Fast Jet:
http://fastjet.fr

"""

import os
import sysconfig

from edpm import PacketStateDatabase
from edpm.engine.db import INSTALL_PATH
from edpm.engine.env_gen import Set, Prepend
from edpm.engine.recipe import Recipe
from edpm.engine.commands import run, env, workdir


class FastJet(Recipe):
    """Provides data for building and installing Rave vertex reconstruction package

    (PacketInstallationInstruction is located in recipe.py)
    """

    def __init__(self):
        # Call parent constructor to fill version, app_path ... and others
        # (!) it is called AFTER we override self.version
        super(FastJet, self).__init__('fastjet')

        self.clone_command = ""
        self.unpack_command = ""         # This command is to untar downloaded array
        self.build_command = ""
        self.make_exec_command = ""
        self.config['branch'] = 'fastjet-3.4.2'
        self.config['repo_address'] = 'http://fastjet.fr/repo/{branch}.tar.gz'
        self.config['python_exec'] = self.find_python()

    @staticmethod
    def find_python():
        """Searches default python which is first found in PATH"""

        from subprocess import check_output
        out = check_output(["which", "python3"]).decode('ascii').strip()

        if not out:
            out = check_output(["which", "python2"]).decode('ascii').strip()

        if not out:
            out = check_output(["which", "python"]).decode('ascii').strip()
        return out

    def setup(self, db):
        """Sets all variables like source dirs, build dirs, etc"""
        if db:
            assert isinstance(db, PacketStateDatabase)

        #
        # use_common_dirs_scheme() sets standard package variables:
        # source_path  = {app_path}/src/{branch}          # Where the sources for the current version are located
        # build_path   = {app_path}/build/{branch}        # Where sources are built. Kind of temporary dir
        # install_path = {app_path}/root-{branch}         # Where the binary installation is
        self.use_common_dirs_scheme()


        self.config['build_flags'] = ""

        # Apply configs
        self.config['repo_address'] = self.config['repo_address'].format(**self.config)
        self.clone_command = "wget {repo_address} -O {branch}.tar.gz".format(**self.config)
        self.unpack_command = 'tar zxvf {branch}.tar.gz && mv {branch}/* {source_path}'.format(**self.config)
        self.build_command = 'pwd && ./configure --prefix={install_path} {build_flags} &&' \
                             ' make -j {build_threads} &&' \
                             ' make install' \
            .format(**self.config)



    def step_install(self):
        self.step_clone()
        self.step_build()

    def step_clone(self):
        """Clones RAVE from github mirror"""

        # Check the directory exists and not empty
        if self.source_dir_is_not_empty():
            # The directory exists and is not empty. Nothing to do
            return
        else:
            # Create the directory
            run('mkdir -p {}'.format(self.source_path))

        workdir(self.source_path)  # Go to our build directory

        run(self.clone_command)         # Execute download command
        run(self.unpack_command)        # Execute unzip command

    def step_build(self):
        # go to our build directory
        workdir(self.source_path)

        # To fix error such as tput: No value for $TERM and no -T specified
        env('TERM', 'xterm')

        # run cmake && make && install
        run(self.build_command)


    @staticmethod
    def gen_env(data):
        install_path = data['install_path']
        yield Prepend('PATH', os.path.join(install_path, 'bin'))
        yield Prepend('LD_LIBRARY_PATH', os.path.join(install_path, 'lib'))
        yield Set('FASTJET_ROOT', install_path)

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {},
        'optional': {},
    }
