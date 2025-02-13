"""
This file provides information of how to build and configure CERN.ROOT:
https://github.com/root-project/root

"""

import os
from distutils.dir_util import mkpath

from edpm.engine import env_gen
from edpm.engine.db import BUILT_WITH_CONFIG
from edpm.engine.recipe import Recipe
from edpm.engine.commands import run, env, workdir, is_not_empty_dir

ROOTSYS = "ROOTSYS"


class RootRecipe(Recipe):
    """Provides data for building and installing root

    PackageInstallationContext is located in engine/recipe.py

    """

    class DefaultConfigFields(object):
        pass

    def __init__(self):
        """
        """

        # Fill the common path pattern
        super(RootRecipe, self).__init__("root")
        self.config['branch'] = 'v6-30-04'
        self.config['cmake_custom_flags'] = ''
        self.config['cmake_build_type'] = 'RelWithDebInfo'
        self.config['cxx_standard'] = '17'

    def find_python(self):
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

        # Ensure that we are using C++14 or higher
        if int(self.config['cxx_standard']) < 14:
            message = "ERROR. cxx_standard must be 14 or above to build root7.\n" \
                      "To set cxx_standard globally:\n" \
                      "   edpm config global cxx_standard=14\n" \
                      "To set cxx_standard for acts:\n" \
                      "   edpm config root7 cxx_standard=14\n" \
                      "(!) Make sure cmake is regenerated after. (rm <top_dir>/acts and run edpm install acts again)\n"
            raise ValueError(message)
        #
        # Compile with python3, then whatever python is...
        python_path = self.find_python()
        self.config["python_flag"] = ' -DPYTHON_EXECUTABLE={} '.format(python_path) if python_path else ''
        # >oO debug: print("Configuring ROOT with '{}' python flag".format(self.config["python_flag"]))

        #
        # use_common_dirs_scheme sets standard package variables:
        # version      = 'v{}-{:02}-{:02}'                 # Stringified version. Used to create directories and so on
        # source_path  = {app_path}/src/{version}          # Where the sources for the current version are located
        # build_path   = {app_path}/build/{version}        # Where sources are built. Kind of temporary dir
        # install_path = {app_path}/root-{version}         # Where the binary installation is
        self.use_common_dirs_scheme()

        #
        # Root download link. We will use github root mirror:
        # The tags have names like: v6-14-04
        # http://github.com/root-project/root.git
        # clone with shallow copy
        self.clone_command = "git clone --depth 1 -b {branch} https://github.com/root-project/root.git {source_path}" \
            .format(**self.config)

        # Make sure custom flags are in there
        if "cmake_custom_flags" not in self.config:
            self.config["cmake_custom_flags"] = ''

        #
        # ROOT packets to disable in our build (go with -D{name}=ON flag)
        # the  -Wno-dev  flag is to ignore the project developers cmake warnings for policy CMP0075
        self.build_cmd = "cmake -Wno-dev -DCMAKE_INSTALL_PREFIX={install_path} " \
                         " -DCMAKE_CXX_STANDARD={cxx_standard}" \
                         " -DCMAKE_BUILD_TYPE={cmake_build_type}"\
                         " -Dhttp=ON" \
                         " -Droot7=ON" \
                         " -Dgdml=ON" \
                         " -Dxrootd=OFF" \
                         " -Dmysql=OFF" \
                         " -Dpythia6=OFF" \
                         " -Dpythia6_nolink=OFF" \
                         " -Dpythia8=OFF" \
                         " {python_flag}" \
                         " {cmake_custom_flags}" \
                         " {source_path}" \
                         "&& cmake --build . -- -j {build_threads}" \
                         "&& cmake --build . --target install" \
            .format(**self.config)  # make global options like '-j8'. Skip now

    def step_install(self):
        self.step_clone_root()
        self.step_build_root()

    def step_clone_root(self):
        """Clones root from github mirror"""

        # Check the directory exists and not empty
        if is_not_empty_dir(self.source_path):
            return  # The directory exists and is not empty. Assume it cloned

        mkpath(self.source_path)  # Create the directory and any missing ancestor directories if not there
        run(self.clone_command)  # Execute git clone command

    def step_build_root(self):
        """Builds root from the ground"""

        # Create build directory
        run('mkdir -p {}'.format(self.build_path))

        env('ROOTSYS', self.install_path)

        # go to our build directory
        workdir(self.build_path)

        # run cmake && make && install
        run(self.build_cmd)

    def step_rebuild_root(self):
        """Clear root build directory"""

        # clear sources directories if needed
        run('rm -rf {}'.format(self.source_path))
        run('rm -rf {}'.format(self.build_path))

        # Now run build root
        self.step_build_root()

    @staticmethod
    def gen_env(data):
        install_path = data['install_path']
        yield env_gen.Prepend('CMAKE_PREFIX_PATH', os.path.join(install_path, 'cmake/'))

        isinstance(data, dict)

        # The next is about conda
        # in conda thisroot.sh triggers error explaining, that everything is already done in activate
        # so we don't need to put thisroot if we acting under conda
        # this is hacky hack
        is_under_conda = 'ROOT_INSTALLED_BY_CONDA' in os.environ

        # In any case we need python environment to build stuff with root under edpm
        def update_python_environment():
            """Function that will update ROOT environment in python
            We need this function because we DON'T want source thisroot in python
            """

            root_bin = os.path.join(install_path, 'bin')
            root_lib = os.path.join(install_path, 'lib')
            root_jup = os.path.join(install_path, 'etc', 'notebook')

            env_updates = [
                env_gen.Set('ROOTSYS', install_path),
                env_gen.Prepend('PATH', root_bin),
                env_gen.Prepend('LD_LIBRARY_PATH', root_lib),
                env_gen.Prepend('DYLD_LIBRARY_PATH', root_lib),
                env_gen.Prepend('PYTHONPATH', root_lib),
                env_gen.Prepend('CMAKE_PREFIX_PATH', install_path),
                env_gen.Prepend('JUPYTER_PATH', root_jup),
            ]

            for updater in env_updates:
                updater.update_python_env()

        # We just call thisroot.xx in different shells
        bash_thisroot_path = os.path.join(install_path, 'bin', 'thisroot.sh')
        bash_text = '\n' \
                    'if [[ -z "$ROOT_INSTALLED_BY_CONDA" ]]; then \n' \
                    '   if test -f "{0}"; then \n' \
                    '      source {0}; \n' \
                    '   fi\n' \
                    'fi\n'.format(bash_thisroot_path)

        csh_thisroot_path = os.path.join(install_path, 'bin', 'thisroot.csh')
        csh_text = "\n" \
                   "if (! $?ROOT_INSTALLED_BY_CONDA) then\n" \
                   "   if ( -f {0} ) then\n"\
                   "      source {0}\n"\
                   "   endif\n" \
                   "endif\n"\
                   .format(csh_thisroot_path)

        bash_text = bash_text if not is_under_conda else "# Don't call thisroot.sh under conda"
        csh_text = csh_text if not is_under_conda else "# Don't call thisroot.csh under conda"
        # Do we need this because of conda?

        # RawText requires text for bash, csh and a function for python
        raw = env_gen.RawText(bash_text, csh_text, update_python_environment)
        yield raw

    #
    # OS dependencies are a map of software packets installed by os maintainers
    # The map should be in form:
    # os_dependencies = { 'required': {'ubuntu': "space separated packet names", 'centos': "..."},
    #                     'optional': {'ubuntu': "space separated packet names", 'centos': "..."}
    #                   }
    os_dependencies = {
        'required': {
            'ubuntu18': "dpkg-dev binutils libx11-dev libxpm-dev libxft-dev libxext-dev liblzma-dev",
            'ubuntu22': "dpkg-dev binutils libx11-dev libxpm-dev libxft-dev libxext-dev liblzma-dev",
            'centos7': "gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel",
            'centos8': "gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel"
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

            'centos7': "gcc-gfortran openssl-devel pcre-devel "
                      "mesa-libGL-devel mesa-libGLU-devel glew-devel ftgl-devel mysql-devel "
                      "fftw-devel cfitsio-devel graphviz-devel "
                      "avahi-compat-libdns_sd-devel libldap-dev python-devel "
                      "libxml2-devel gsl-static",
            'centos8': "gcc-gfortran openssl-devel pcre-devel "
                      "mesa-libGL-devel mesa-libGLU-devel ftgl-devel mysql-devel "
                      "fftw-devel cfitsio-devel graphviz "
                      "openldap-devel python3-devel "
                      "libxml2-devel gsl-devel"
        },
    }




def root_find():
    """Looks for CERN ROOT package
    :return [str] - empty list if not found or a list with 1 element - ROOTSYS path

    The only way to find ROOT is by checking for ROOTSYS package,
    The function family xxx_find() return list in general
    so this function returns either empty list or a list with 1 element - root path
    """

    # The only way to find a CERN ROOT is by
    result = []

    # Check ROOTSYS environment variable
    if ROOTSYS not in os.environ:
        print("<red>ROOTSYS</red> not found in the environment")
        return result

    # Now check ROOTSYS exists in the system
    root_sys_path = os.environ[ROOTSYS]
    if not os.path.isdir(root_sys_path):
        print("WARNING", " ROOTSYS points to nonexistent directory of a file")
        return result

    # Looks like root exists, return the path
    return [root_sys_path]
