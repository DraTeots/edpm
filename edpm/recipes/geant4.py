"""
This file provides information of how to build and configure Geant4 framework:
https://github.com/Geant4/geant4


"""
import os
import platform

from distutils.dir_util import mkpath
from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.generators.steps import EnvAppend, EnvPrepend, EnvRawText
from edpm.engine.commands import is_not_empty_dir

class Geant4Recipe(ComposedRecipe):
    """
    Installs Geant4 from Git + CMake with standard EDPM v3 approach.
    Retains advanced flags like:
      - GEANT4_INSTALL_DATA=ON
      - G4 use Qt / Raytracer / X11 / system CLHEP
      - cxx_standard
      - environment that sources geant4.sh/csh
      - optional conda skip
    """

    # OS Dependencies if you want to use `edpm req`.
    os_dependencies = {
        'required': {
            'ubuntu18': "libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev libx11-dev",
            'ubuntu22': "libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev libx11-dev",
            'centos7': (
                "assimp-devel expat-devel libX11-devel libXt-devel libXmu-devel libXrender-devel "
                "libXpm-devel libXft-devel libAfterImage libAfterImage-devel mesa-libGLU-devel "
                "qt5-qtdeclarative-devel qt5-linguist tetgen-devel xerces-c-devel xkeyboard-config "
                "qt5-qtbase-devel"
            ),
            'centos8': (
                "expat-devel libX11-devel libXt-devel libXmu-devel libXrender-devel libXpm-devel "
                "libXft-devel libAfterImage libAfterImage-devel mesa-libGLU-devel qt5-qtdeclarative-devel "
                "qt5-linguist xerces-c-devel xkeyboard-config qt5-qtbase-devel"
            ),
        },
        'optional': {}
    }

    def __init__(self, config):
        # Provide some minimal defaults; user can override in the plan file.
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/Geant4/geant4.git',
            'branch': 'v11.3.0',
            'shallow': True,
            'cxx_standard': 17,
            'cmake_build_type': 'RelWithDebInfo',
            'build_threads': 4,
            # If the user wants to add additional custom flags, they can define:
            #   cmake_flags or cmake_custom_flags
        }
        super().__init__(name='geant4', config=config)

    def preconfigure(self):
        """
        Overridden to merge custom Geant4 cmake flags into self.config['cmake_flags'].
        """
        cxx_std = self.config.get('cxx_standard', 17)
        # If you want to enforce a min version, e.g. 17 or 14:
        # if int(cxx_std) < 14:
        #     raise ValueError("Geant4 requires C++14 or higher...")

        # Construct the standard set of G4 cmake flags
        geant4_flags = [
            "-DGEANT4_INSTALL_DATA=ON",
            f"-DCMAKE_CXX_STANDARD={cxx_std}",
            "-DGEANT4_USE_GDML=ON",
            "-DGEANT4_USE_SYSTEM_CLHEP=ON",
            "-DCLHEP_ROOT_DIR=$CLHEP",  # expects CLHEP env var or user config
            "-DGEANT4_USE_OPENGL_X11=ON",
            "-DGEANT4_USE_RAYTRACER_X11=ON",
            "-DGEANT4_BUILD_MULTITHREADED=ON",
            "-DGEANT4_BUILD_TLS_MODEL=global-dynamic",
            "-DGEANT4_USE_QT=ON",
            f"-DCMAKE_BUILD_TYPE={self.config['cmake_build_type']}",
            f"-DCMAKE_INSTALL_PREFIX={self.config['install_path']}",
            "-Wno-dev",
            # finally we specify the source_path at the end
            self.config.get('source_path', "")
        ]

        # Merge user-provided cmake_flags or cmake_custom_flags
        user_flags = self.config.get('cmake_flags', "")
        user_custom = self.config.get('cmake_custom_flags', "")
        # Combine them all:
        final_flags = " ".join([user_flags, user_custom, " ".join(geant4_flags)]).strip()
        self.config['cmake_flags'] = final_flags

    def fetch(self):
        """
        Use the standard Git fetch logic but skip if source_path is already non-empty.
        """
        source_path = self.config.get('source_path', "")
        if source_path and is_not_empty_dir(source_path):
            # Already cloned or something is there, skip
            return

        # Otherwise, do a shallow clone if requested
        from edpm.engine.commands import run
        shallow_flag = "--depth 1" if self.config.get('shallow', False) else ""
        branch = self.config.get('branch', 'master')
        url = self.config.get('url')
        clone_cmd = f'git clone {shallow_flag} -b {branch} {url} "{source_path}"'
        mkpath(source_path)
        run(clone_cmd)

    def gen_env(self, data):
        """
        Sets environment to source geant4.sh/csh after installation.
        Also skips if 'GEANT_INSTALLED_BY_CONDA' is set.
        """
        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        lib_path = os.path.join(install_path, 'lib')
        lib64_path = os.path.join(install_path, 'lib64')

        # Possibly skip if we detect conda
        is_under_conda = 'GEANT_INSTALLED_BY_CONDA' in os.environ

        # 1) Make sure PATH includes the new bin
        yield EnvPrepend('PATH', bin_path)

        # 2) We'll define a function to do in-process environment updates
        def update_python_environment():
            # We do not want to source geant4.sh in Python,
            # so we manually append the library paths
            if os.path.isdir(lib_path):
                yield EnvAppend('LD_LIBRARY_PATH', lib_path)
                if platform.system() == 'Darwin':
                    yield EnvAppend('DYLD_LIBRARY_PATH', lib_path)
            if os.path.isdir(lib64_path):
                yield EnvAppend('LD_LIBRARY_PATH', lib64_path)
                if platform.system() == 'Darwin':
                    yield EnvAppend('DYLD_LIBRARY_PATH', lib64_path)

        # 3) Prepare the shell scripts
        bash_script = os.path.join(bin_path, 'geant4.sh')
        csh_script = os.path.join(bin_path, 'geant4.csh')

        if not is_under_conda:
            sh_text = f"source {bash_script}"
            csh_text = f"source {csh_script} {bin_path}"
        else:
            # Skip if conda
            sh_text = "# Don't call geant4.sh under conda"
            csh_text = "# Don't call geant4.csh under conda"

        # 4) Combine them into a EnvRawText environment action
        def python_env_updater():
            # This function is called by EDPM to update the Python process environment
            for action in update_python_environment():
                action.update_python_env()

        yield EnvRawText(sh_text, csh_text, python_env_updater)

    def patch(self):
        """If you need to apply patches to G4, do it here."""
        pass

    def post_install(self):
        """Any post-install steps if necessary."""
        pass

