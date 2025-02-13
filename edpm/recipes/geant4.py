"""
This file provides information of how to build and configure Geant4 framework:
https://github.com/Geant4/geant4


"""

import os
import platform

from edpm.engine.commands import run, workdir
import edpm.engine.env_gen as env_gen
from edpm.engine.env_gen import Set, Append, Prepend
from edpm.engine.recipe import Recipe


class GeantRecipe(Recipe):
    """Provides data for building and installing Geant4 framework
    source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
    build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
    install_path = {app_path}/root-{version}         # Where the binary installation is
    """

    def __init__(self):
        super(GeantRecipe, self).__init__('geant4')
        self.clone_command = ''             # will be set by self.set_app_path
        self.build_cmd = ''                 # will be set by self.set_app_path
        self.config['branch'] = 'v11.2.1'
        self.config['cmake_build_type'] = 'RelWithDebInfo'


    def setup(self, db):
        """Sets all variables like source dirs, build dirs, etc"""

        #
        # use_common_dirs_scheme sets standard package variables:
        # source_path  = {app_path} / src   / {branch}       # Where the sources for the current version are located
        # build_path   = {app_path} / build / {branch}       # Where sources are built. Kind of temporary dir
        # install_path = {app_path} / geant-{branch}         # Where the binary installation is
        self.use_common_dirs_scheme()

        #
        # Git download link. Clone with shallow copy
        self.clone_command = "git clone --depth 1 -b {branch} https://github.com/Geant4/geant4 {source_path}"\
            .format(**self.config)

        # cmake command:
        # the  -Wno-dev  flag is to ignore the project developers cmake warnings for policy CMP0075
        self.build_cmd = """
            cmake
                -DGEANT4_INSTALL_DATA=ON
                -DCMAKE_CXX_STANDARD={cxx_standard}
                -DGEANT4_USE_GDML=ON
                -DGEANT4_USE_SYSTEM_CLHEP=ON
                -DCLHEP_ROOT_DIR=$CLHEP
                -DGEANT4_USE_OPENGL_X11=ON
                -DGEANT4_USE_RAYTRACER_X11=ON
                -DGEANT4_BUILD_MULTITHREADED=ON 
                -DGEANT4_BUILD_TLS_MODEL=global-dynamic 
                -DGEANT4_USE_QT=ON
                -DCMAKE_BUILD_TYPE={cmake_build_type}
                -DCMAKE_INSTALL_PREFIX={install_path}
                -Wno-dev
                {source_path}
            && cmake --build . -- -j {build_threads}
            && cmake --build . --target install"""\
                         .format(**self.config)
        # remove multiple spaces and \n
        self.build_cmd = " ".join(self.build_cmd.split())

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
        """Builds JANA from the ground"""

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

    @staticmethod
    def gen_env(data):
        """Generates environments to be set

        This function is a bit more tricky than usual - RawText are going to be used.
        RawText actually allows to:
         1. wright a custom text for sh and csh environment scripts
         2. and run a python command to set the environment

        For bash and csh one wants to run 'source .../geant4.sh[csh]'
        But also, one must be set the environment inside python.
        When building Geant from scratch and there is no geant4.sh[csh] yet
        update_python_environment() - do this

        """

        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        lib_path = os.path.join(install_path, 'lib')        # on some platforms
        lib64_path = os.path.join(install_path, 'lib64')    # on some platforms

        # The next is about conda
        # in conda thisroot.sh triggers error explaining, that everything is already done in activate
        # so we don't need to put thisroot if we acting under conda
        # this is hacky hack
        is_under_conda = 'GEANT_INSTALLED_BY_CONDA' in os.environ

        def update_python_environment():
            """Function that will update Geant environment in python build step
            We need this function because we DON'T want to source geant4.sh in python
            """
            env_updates = [
                env_gen.Append('LD_LIBRARY_PATH', lib_path),
                env_gen.Append('LD_LIBRARY_PATH', lib64_path)
            ]

            if platform.system() == 'Darwin':
                env_updates.append(env_gen.Append('DYLD_LIBRARY_PATH', lib_path))
                env_updates.append(env_gen.Append('DYLD_LIBRARY_PATH', lib64_path))

            for updater in env_updates:
                updater.update_python_env()

        # We just call geant4.sh in different shells
        yield Prepend('PATH', bin_path)  # to make available clhep-config and others

        sh_text = "source {}".format(os.path.join(bin_path, 'geant4.sh'))

        # in Geant CSH script Geant asks to get a path for geant bin directory
        csh_text = "source {} {}".format(os.path.join(bin_path, 'geant4.csh'), bin_path)

        sh_text = sh_text if not is_under_conda else "# Don't call geant4.sh under conda"
        csh_text = csh_text if not is_under_conda else "# Don't call geant4.csh under conda"

        yield env_gen.RawText(
            sh_text,
            csh_text,
            update_python_environment
        )

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    # The idea behind is to generate easy to use instructions: 'sudo apt-get install ... ... ... '
    os_dependencies = {
        'required': {
            'ubuntu18': "libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev libx11-dev",
            'ubuntu22': "libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev libx11-dev",
            'centos7': "assimp-devel expat-devel libX11-devel libXt-devel libXmu-devel libXrender-devel libXpm-devel"
                      "libXft-devel libAfterImage libAfterImage-devel mesa-libGLU-devel qt5-qtdeclarative-devel"
                      "qt5-linguist tetgen-devel xerces-c-devel xkeyboard-config qt5-qtbase-devel",
            'centos8': "expat-devel libX11-devel libXt-devel libXmu-devel libXrender-devel libXpm-devel "
                      "libXft-devel libAfterImage libAfterImage-devel mesa-libGLU-devel qt5-qtdeclarative-devel "
                      "qt5-linguist xerces-c-devel xkeyboard-config qt5-qtbase-devel"
        },
        'optional': {}
    }
