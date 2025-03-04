"""
Geant4 recipe for EDPMv3
https://github.com/Geant4/geant4
"""
from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.generators.steps import EnvPrepend, EnvRawText
from edpm.engine.commands import is_not_empty_dir
import os
import platform

class Geant4Recipe(ComposedRecipe):
    """
    Installs Geant4 from Git with standard CMake build approach.
    """

    # OS Dependencies definition
    os_dependencies = {
        'required': {
            'ubuntu': "libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev libx11-dev",
            'centos': (
                "expat-devel libX11-devel libXt-devel libXmu-devel libXrender-devel "
                "libXpm-devel libXft-devel mesa-libGLU-devel qt5-qtbase-devel "
                "qt5-qtdeclarative-devel xerces-c-devel"
            ),
        },
        'optional': {}
    }

    def __init__(self, config):
        # Default configuration
        defaults = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/Geant4/geant4.git',
            'branch': 'v11.3.0',
            'shallow': True,
            'cxx_standard': 17,
            'cmake_build_type': 'RelWithDebInfo',
            'build_threads': 4,
            'cmake_flags': {
                'GEANT4_INSTALL_DATA': 'ON',
                'GEANT4_USE_GDML': 'ON',
                'GEANT4_USE_SYSTEM_CLHEP': 'ON',
                'CLHEP_ROOT_DIR': '$CLHEP',
                'GEANT4_USE_OPENGL_X11': 'ON',
                'GEANT4_USE_RAYTRACER_X11': 'ON',
                'GEANT4_BUILD_MULTITHREADED': 'ON',
                'GEANT4_BUILD_TLS_MODEL': 'global-dynamic',
                'GEANT4_USE_QT': 'ON',
                'Wno-dev': None  # Flag with no value
            }
        }
        super().__init__(name='geant4', config=config, defaults=defaults)

    def fetch(self):
        """Skip fetch if source directory is not empty"""
        source_path = self.config.get('source_path', "")
        if source_path and is_not_empty_dir(source_path):
            return
        super().fetch()

    @staticmethod
    def gen_env(data):
        """Setup environment to use Geant4"""
        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')

        # Add bin to PATH
        yield EnvPrepend('PATH', bin_path)

        # Source geant4 scripts unless under conda
        is_under_conda = 'GEANT_INSTALLED_BY_CONDA' in os.environ
        if not is_under_conda:
            bash_script = os.path.join(bin_path, 'geant4.sh')
            csh_script = os.path.join(bin_path, 'geant4.csh')

            sh_text = f"source {bash_script}"
            csh_text = f"source {csh_script} {bin_path}"

            # Function to update Python environment
            def python_env_updater():
                lib_path = os.path.join(install_path, 'lib')
                lib64_path = os.path.join(install_path, 'lib64')

                # Add library paths
                if os.path.isdir(lib_path):
                    os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
                    if platform.system() == 'Darwin':
                        os.environ['DYLD_LIBRARY_PATH'] = f"{lib_path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"

                if os.path.isdir(lib64_path):
                    os.environ['LD_LIBRARY_PATH'] = f"{lib64_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
                    if platform.system() == 'Darwin':
                        os.environ['DYLD_LIBRARY_PATH'] = f"{lib64_path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"

            yield EnvRawText(sh_text, csh_text, python_env_updater)