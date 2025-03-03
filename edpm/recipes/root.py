"""
This file provides information of how to build and configure CERN.ROOT:
https://github.com/root-project/root

"""

import os
import platform
from distutils.dir_util import mkpath
from subprocess import check_output

from edpm.engine.composed_recipe import ComposedRecipe
from edpm.engine.generators.steps import EnvSet, EnvPrepend, EnvRawText
from edpm.engine.commands import is_not_empty_dir

ROOTSYS = "ROOTSYS"

class RootRecipe(ComposedRecipe):
    """
    Installs CERN ROOT from Git + CMake, retaining advanced logic:
    - Minimum cxx_standard=14
    - Python detection
    - root7=ON, gdml=ON, etc.
    - 'thisroot.sh' environment script
    - Optional conda skip
    """

    # OS dependencies (optional). You can leave this out if you don't use `edpm req`.
    os_dependencies = {
        'required': {
            'ubuntu18': "dpkg-dev binutils libx11-dev libxpm-dev libxft-dev libxext-dev liblzma-dev",
            'ubuntu22': "dpkg-dev binutils libx11-dev libxpm-dev libxft-dev libxext-dev liblzma-dev",
            'centos7':  "gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel",
            'centos8':  "gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel"
        },
        'optional': {
            'ubuntu18': "gfortran libssl-dev libpcre3-dev "
                        "xlibmesa-glu-dev libglew-dev libftgl-dev "
                        "libmysqlclient-dev libfftw3-dev libcfitsio-dev "
                        "graphviz-dev libavahi-compat-libdnssd-dev "
                        "libldap2-dev python3-dev libxml2-dev libkrb5-dev "
                        "libgsl0-dev",
            'ubuntu22': "gfortran libssl-dev libpcre3-dev "
                        "xlibmesa-glu-dev libglew-dev libftgl-dev "
                        "libmysqlclient-dev libfftw3-dev libcfitsio-dev "
                        "graphviz-dev libavahi-compat-libdnssd-dev "
                        "libldap2-dev python3-dev libxml2-dev libkrb5-dev "
                        "libgsl0-dev",
            'centos7':  "gcc-gfortran openssl-devel pcre-devel "
                        "mesa-libGL-devel mesa-libGLU-devel glew-devel ftgl-devel mysql-devel "
                        "fftw-devel cfitsio-devel graphviz-devel "
                        "avahi-compat-libdns_sd-devel libldap-dev python-devel "
                        "libxml2-devel gsl-static",
            'centos8':  "gcc-gfortran openssl-devel pcre-devel "
                        "mesa-libGL-devel mesa-libGLU-devel ftgl-devel mysql-devel "
                        "fftw-devel cfitsio-devel graphviz "
                        "openldap-devel python3-devel "
                        "libxml2-devel gsl-devel"
        },
    }

    def __init__(self, config):
        # Provide minimal defaults. Many can be overridden from plan.
        self.default_config = {
            'fetch': 'git',
            'make': 'cmake',
            'url': 'https://github.com/root-project/root.git',  # main GitHub
            'branch': 'v6-34-04',
            'shallow': True,  # means use `--depth 1`
            'cxx_standard': '17',
            'cmake_build_type': 'RelWithDebInfo',
            # If user doesn't override, we'll set them in preconfigure().
            'cmake_flags': "",
            'build_threads': 4,
        }
        super().__init__(name='root', config=config)

    def preconfigure(self):
        """
        Overriding preconfigure step to:
        1. Enforce cxx_standard >= 14
        2. Find Python
        3. Build up specialized cmake flags for ROOT
        """
        # 1) Check cxx_standard
        cxx_std = int(self.config.get('cxx_standard', 17))
        if cxx_std < 14:
            raise ValueError(
                "ERROR: cxx_standard must be >= 14 to build ROOT.\n"
                "Please set it in plan or via 'edpm config global cxx_standard=14'."
            )

        # 2) Find python
        python_path = self._find_python()
        python_flag = ""
        if python_path:
            python_flag = f"-DPYTHON_EXECUTABLE={python_path}"
        # 3) Combine your advanced flags
        # You can add more or disable modules as needed
        root_flags = [
            "-Wno-dev",
            f"-DCMAKE_CXX_STANDARD={cxx_std}",
            f"-DCMAKE_BUILD_TYPE={self.config['cmake_build_type']}",
            "-Droot7=ON",
            "-Dgdml=ON",
            "-Dxrootd=OFF",
            "-Dmysql=OFF",
            "-Dpythia6=OFF",
            "-Dpythia6_nolink=OFF",
            "-Dpythia8=OFF",
            "-Dhttp=ON",
        ]
        if python_flag:
            root_flags.append(python_flag)

        # Merge any user-provided custom flags
        user_flags = self.config.get('cmake_custom_flags', "")
        if user_flags:
            root_flags.append(user_flags)

        # Convert to a single string, appended to the standard 'cmake_flags'
        joined_flags = " ".join(root_flags)
        # The ComposedRecipe’s CmakeMaker typically looks at `config['cmake_flags']`.
        self.config['cmake_flags'] = f"{self.config['cmake_flags']} {joined_flags}"

    def _find_python(self):
        """
        Attempt to find a 'python3', fallback to python2, python.
        """
        candidates = ["python3", "python2", "python"]
        for prog in candidates:
            try:
                path = check_output(["which", prog]).decode().strip()
                if path:
                    return path
            except Exception:
                pass
        return None

    def fetch(self):
        """
        Overrides default fetch to implement a shallow git clone, if requested,
        and avoid re-downloading if source_path is nonempty.
        """
        source_path = self.config.get('source_path', "")
        if source_path and is_not_empty_dir(source_path):
            # Already cloned or existing
            return

        # Build the clone command ourselves to use `--depth 1` if shallow
        shallow_flag = ""
        if self.config.get('shallow', False):
            shallow_flag = "--depth 1"

        branch = self.config.get('branch', 'master')
        url = self.config.get('url')
        clone_cmd = f'git clone {shallow_flag} -b {branch} {url} "{source_path}"'

        # Make sure source dir exists
        mkpath(source_path)
        # Actually run the clone
        from edpm.engine.commands import run
        run(clone_cmd)

    def patch(self):
        """
        If you have any patch steps, place them here.
        Otherwise, skip.
        """
        pass

    def post_install(self):
        """
        Any post-install steps after 'cmake --build . --target install'.
        Typically none, but you can add if needed.
        """
        pass

    def gen_env(self, data):
        """
        Replicates environment logic from old recipe (including conda skip).
        """
        install_path = data['install_path']
        bin_path = os.path.join(install_path, 'bin')
        lib_path = os.path.join(install_path, 'lib')
        cmake_path = os.path.join(install_path, 'cmake')
        yield EnvPrepend('CMAKE_PREFIX_PATH', cmake_path)

        # We'll skip calling 'thisroot' if conda is found
        is_under_conda = os.environ.get('ROOT_INSTALLED_BY_CONDA', False)

        def update_python_environment():
            """
            This function is called in-process for Python environment updates.
            We set environment variables like PATH, LD_LIBRARY_PATH, etc.
            """
            # You can replicate old logic
            yield EnvSet('ROOTSYS', install_path)
            yield EnvPrepend('PATH', bin_path)
            yield EnvPrepend('LD_LIBRARY_PATH', lib_path)
            if platform.system() == 'Darwin':
                yield EnvPrepend('DYLD_LIBRARY_PATH', lib_path)
            # Put the .so python modules into PYTHONPATH
            yield EnvPrepend('PYTHONPATH', lib_path)
            # Possibly also add a jupyter path
            jup_path = os.path.join(install_path, 'etc', 'notebook')
            yield EnvPrepend('JUPYTER_PATH', jup_path)
            # EnvPrepend overall prefix
            yield EnvPrepend('CMAKE_PREFIX_PATH', install_path)

        # Build the scripts to source
        bash_thisroot = os.path.join(bin_path, 'thisroot.sh')
        csh_thisroot = os.path.join(bin_path, 'thisroot.csh')

        # If user is not under conda, we source them
        if not is_under_conda:
            bash_text = (
                f'\nif [ -f "{bash_thisroot}" ]; then\n'
                f'   source "{bash_thisroot}"\n'
                f'fi\n'
            )
            csh_text = (
                f'\nif ( -f "{csh_thisroot}" ) then\n'
                f'   source "{csh_thisroot}"\n'
                f'endif\n'
            )
        else:
            # Under conda? skip
            bash_text = "# Skipping thisroot.sh under conda"
            csh_text = "# Skipping thisroot.csh under conda"

        # Provide the Python in-process environment update function
        def python_env_updater():
            for action in update_python_environment():
                action.update_python_env()

        yield EnvRawText(bash_text, csh_text, python_env_updater)


# Optional utility function from old code if you want it:
def root_find():
    """
    Looks for CERN ROOT by checking $ROOTSYS.
    Returns a list with one element if found, or empty if not found.
    """
    if ROOTSYS not in os.environ:
        print("<red>ROOTSYS</red> not found in the environment")
        return []
    root_sys_path = os.environ[ROOTSYS]
    if not os.path.isdir(root_sys_path):
        print("WARNING: ROOTSYS points to nonexistent directory:", root_sys_path)
        return []
    return [root_sys_path]

