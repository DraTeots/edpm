# edpm

**edpm** stands for **e**asy **d**ependency **p**acket **m**anagement

---

## Overview

**edpm** is a lightweight tool for managing dependencies for C++/CMake (and occasionally Python) projects. Edpm is
designed to be a focused, lightweight helper for dependency management that separates fetching dependencies from the
build process. Its design avoids the pitfalls of CMake’s FetchContent (which mingles dependency acquisition with
building) and the overkill of large managers like Spack that installs numerous low-level packages. By using manifest and
lock files along with generated environment scripts, edpm offers a reproducible, user-friendly solution ideal for
scientific and development projects that need only a fixed, known set of dependencies.

Happy building!

Edpm fetches, builds, and configures dependencies via simple commands (e.g. `edpm install geant4`) while generating:

- A manifest file (in JSON) listing the desired dependencies.
- A lock file that records exactly how packages were installed.
- Environment scripts (for bash, csh, and even a CMake dependency file) so that projects can seamlessly consume
  installed packages.
- **edpm** is written in pure python with minimum dependencies
- it is shipped by pip (python official repo), so can be installed with `pip install edpm` on all major platforms
- CLI (command line interface) - provides users with commands to manipulate packets as easy as `edpm install geant4`

---

## Rationale & Philosophy

1. **Separation of Dependency and Build Steps:**
    - Modern CMake approaches like FetchContent tend to mix dependency downloads with the build process. This can lead
      to complications (e.g. longer configure times, less control over external dependencies) and less reproducible
      builds.
    - Edpm separates the dependency “fetch/install” phase from the project’s main build, similar to how npm/yarn handle
      JavaScript packages. This not only improves reproducibility but also makes it easier to install dependencies in
      environments like Docker images without a full CMake project.

2. **Keeping It Simple:**
    - In many situations, especially in scientific projects, the full complexity of tools like Spack (which often
      installs a gazillion low-level packages) is unnecessary. Spack and similar managers can bring in extra
      dependencies (X11 libraries, Perl, zip, etc.) that complicate the environment.
    - Edpm is designed to be “advanced” compared to a simple bash script yet far less cumbersome than a full package
      manager. It’s tailored for a fixed, known set of dependencies, allowing developers to focus on building their
      software rather than managing a complex dependency graph.

3. **Focused, User-Friendly Approach:**
    - **Manifest and Lock Files:** By keeping a JSON manifest and generating a lock file, edpm guarantees that everyone
      uses the same versions of dependencies. This mirrors best practices seen in npm/yarn and ensures reproducibility.
    - **Environment Generation:** Edpm produces shell scripts (and soon a CMake dependency file) to easily set
      environment variables like `PATH`, `LD_LIBRARY_PATH`, and `CMAKE_PREFIX_PATH`. This decouples dependency
      management from the build system, making it simpler to use edpm-installed libraries in any context.
    - **Integration with Existing Installations:** Users can register pre-installed dependencies (e.g., setting the path
      for CERN.ROOT) so that edpm won’t rebuild what is already available.

---

## Comparison with Other Approaches

- **CMake FetchContent / CPM.cmake:**  
  *Philosophy & Realization:*
    - FetchContent integrates dependency downloads directly into the CMake configuration phase. While convenient for
      pure CMake projects, it can be inflexible and slow down configuration.
    - **edpm** keeps dependency management separate from the build, providing an explicit, one-step “install” command
      and independent environment scripts.

- **Spack / Conan:**  
  *Philosophy & Realization:*
    - These tools are powerful and handle complex dependency graphs, version conflicts, and multiple variants. However,
      they tend to install a large number of low-level packages and require a steep learning curve.
    - **edpm** is designed for scenarios where such complexity is unnecessary. It installs a known set of dependencies
      with fixed, “blessed” versions and avoids the overhead of a full dependency resolver.

- **vcpkg & CGet:**  
  *Philosophy & Realization:*
    - vcpkg offers a manifest-driven, relatively simple approach but introduces build profiles (triplets) that add
      complexity.
    - CGet was very lightweight and easy to use, much like edpm is intended to be, but its lack of active maintenance
      makes it less appealing.
    - **edpm** borrows the simplicity of CGet while adding modern features like environment management and manifest/lock
      files, ensuring reproducibility without unnecessary overhead.

*(Note: XRepo is no longer maintained and is not part of the comparison.)*

---

## Quick Start

### Installing edpm

Install edpm via pip (system-wide or user level):

```bash
# System-level installation:
sudo python -m pip install edpm

# Or user-level (ensure ~/.local/bin is in your PATH):
python -m pip install --user edpm
```

> JLab machines with certificate problems - add these flags to the command above:  
> --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org  
> see [Troubleshooting](#installation-troubleshooting) chapter for details


Install everything else

```bash

# install prerequesties
edpm req centos eicrecon      # get list of OS packets required to build jana and deps
sudo yum install ...          # install whatever 'edpm req' shows

# setup installation dir and existing packets, introspect
edpm --top-dir=<where-to>     # Directory where packets will be installed
edpm                          # To see how edpm is configured
edpm install eicrecon --explain  # To see what is to be installed
edpm set root `$ROOTSYS`      # if you have CERN.ROOT. Or skip this step
edpm set <packet> <path>      # set other existing packets. Or skip this step!!!
edpm config global cxx_standard=17   # It is recommended if compiler supports C++17


# Build and install the rest
edpm install eicrecon            # install eicrecon and dependencies (like genfit, jana and rave)
edpm install g4e              # install Geant-4-Eic and dependencies (Geant4, etc)

# EnvSet environment
source<(edpm env)             # set environment variables
edpm env csh > your.csh       # if you are still on CSH

# If that worked don't read the next...
```

> (!) If you use your version of ROOT, all packages depending on ROOT should be
> installed with the same C++ standard flags as root. So it it was C++11 or C++17, it should be used
> everywhere. To set it in edpm  
> ```edpm config global cxx_standard=17```
>

# Motivation

***TL;DR;*** Major HEP and NP scientific packages are not supported by some major distros and package managers.
Everybody have to reinvent the wheel developing "yet another build-all script" to include
such packages in their software chains and make users' lives easier. And we do. 

What about Spack (Spack that should have saved us)? - Spack works and shines on clusters with supervision of experts.
It failed countless times when the task was to install something working for students.
Spack requires to know Spack and its concepts to debug its deep dependencies failures

***Longer reading***

**edpm** is here as there is no standard convention in HEP and NP of how to distribute and install software packages
with its dependencies. Some packages (like eigen, xerces, etc.) are usually supported by
OS maintainers, while others (Cern ROOT, Geant4, Rave) are usually built by users or
other packet managers and could be located anywhere. We also praise "version hell" (e.g. when GenFit doesn't compile
with CLHEP from ubuntu repo) and lack of software manpower (e.g. to sufficiently and continuously maintain packages
for major distros or even to fix some simple issues on GitHub).

At this points **edpm** tries to unify experience and make it simple to deploy eicrecon for:

- Users on RHEL and CentOS
- Users on Ubutnu (and Windows with WSL)
- Docker and other containers


<br><br>

## Installation

```bash
pip install --upgrade edpm    # system level installation
```

If you have certificate problems (on JLab machines): ([more options on certificates](#jlab-certificate-problems)):

```bash
# System level copy-paste:
sudo python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org -U edpm
# User level copy-paste:
python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --user -U edpm
```

More on this:

* See [INSTALLATION TROUBLESHOOTING](#installation-troubleshooting) If you don't have pip or right python version.
* See [Jlab root certificate problems](#jlab-certificate-problems) and how to solve them
* See [Manual or development installation](#manual-or-development-installation) to use this repo directly, develop edpm
  or don't want to mess with pip at all?

<br><br>

[READ ABOUT MANIFEST](manifest_spec.md)


## Configuration

edpm stores the states in the manifest file. There are certain parameters relevant for
all/most of the packages such as cxx_standard or a number of compilation threads.
Then there are parameters to configure each package installation.

To view and change those configuration:

```
edpm config <packet name> <config name> = <new value> 
```

examples:

```bash
edpm config            # edpm config global
edpm config global     # Show global configs
edpm config root       # Show configs for packet root

edpm config global cxx_standard=14  # EnvSet globally to use C++14 for all new packages  
                                    # (if that is not overwritten by the package config)

edpm config acts cxx_standard=17    # EnvSet cxx standard for root (overwrites global level)
```

Config allows

**Where edpm data is stored:**

There are standard directories for users data for each operating system. edpm use them to store
db.json and generated environment files (edpm doesnt use the files by itself).

For linux it is XDG_DATA_HOME\*:

```
~/.local/share/edpm/env.sh      # sh version
~/.local/share/edpm/env.csh     # csh version
~/.local/share/edpm/db.json     # open it, edit it, love it
```

> \* - XDG is the standard POSIX paths to store applications data, configs, etc.


**```edpm_DATA_PATH```** - You can control where edpm stores data by setting ```edpm_DATA_PATH``` environment variable.

<br><br>

## INSTALLATION TROUBLESHOOTING

***But... there is no pip:***  
Install it!

```
sudo easy_install pip       # system level
easy_install pip --user     # user level
```

For JLab lvl1&2 machines, there is a python installations that have ```pip``` :

```bash
/apps/python/     # All pythons there have pip and etc
/apps/anaconda/   # Moreover, there is anaconda (python with all major math/physics libs) 
``` 

***But there is no 'pip' command?***  
If ```easy_install``` installed something, but ```pip``` command is not found after, do:

1. If ```--user``` flag was used, make sure ```~/.local/bin``` is in your ```$PATH``` variable
2. you can fallback to ```python -m pip``` instead of using ```pip``` command:
    ```bash
    python -m pip install --user --upgrade edpm
    ``` 

***But... there is no easy_install!***  
Install it!

```bash
sudo yum install python-setuptools python-setuptools-devel   # centos and RHEL/CentOS 
sudo apt-get install python-setuptools                       # Ubuntu and Debian
# Gentoo. I should not write this for its users, right?
```

For python3 it is ```easy_install3``` and ```python3-setuptools```

***I dont have sudo privileges!***

Add "--user" flag both for pip and easy_install for this.
[Read SO here](https://stackoverflow.com/questions/15912804/easy-install-or-pip-as-a-limited-user)

### JLab certificate problems

If you get errors like:

```
Retrying (...) after connection broken by 'SSLError(SSLError(1, u'[SSL: CERTIFICATE_VERIFY_FAILED]...
```

The problem is that ```pip``` is trustworthy enough to use secure connection to get packages.
And JLab is helpful enough to put its root level certificates in the middle.

1. The easiest solution is to declare PiPy sites as trusted:
    ```bash
    python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org edpm
    ```
2. Or to permanently add those sites as trusted in pip.config
    ```
    [global]
    trusted-host=
        pypi.python.org
        pypi.org
        files.pythonhosted.org
    ```
   ([The link where to find pip.config on your system](https://pip.pypa.io/en/stable/user_guide/#config-file))
3. You may want to be a hero and kill the dragon. The quest is to take [JLab certs](https://cc.jlab.org/JLabCAs).
   Then [Convert them to pem](https://stackoverflow.com/questions/991758/how-to-get-pem-file-from-key-and-crt-files).
   Then [add certs to pip](https://stackoverflow.com/questions/25981703/pip-install-fails-with-connection-error-ssl-certificate-verify-failed-certi).
   Then **check it really works** on JLab machines. And bring the dragon's head back (i.e. please, add the exact
   instruction to this file)

<br><br>

### Manual or development installation:

***TL;DR;*** Get edpm, install requirements, ready:

```bash
git clone https://gitlab.com/eic/edpm.git
pip install -r edpm/requirements.txt

# OR clone and add edpm/bin to your PATH
export PATH=`pwd`/edpm/bin:$PATH
```

**requirments**:

```Click``` and ```appdirs``` are the only requirements. If you have pip do:

```bash
pip install --upgrade click appdirs
```

> If for some reason you don't have pip, you don't know python well enough
> and don't want to mess with it, pips, shmips and doh...
> Just download and add to ```PYTHONPATH```:
[this 'click' folder](https://pypi.org/project/click/)
> and some folder with [appdirs.py](https://github.com/ActiveState/appdirs/blob/master/appdirs.py)


<br>

## Adding a package

Each packet is represented by a single python file - a recipe which has instructions
of how to get and build the package. Usually it provides:

- download/clone command
- build command
- setup of environment variables
- system dependencies (which can be installed by OS packet managers: yum, apt)

For simplicity (at this point) all recipes are located in a folder inside this repo:
[edpm/recipes](edpm/recipes).

### Adding Git-CMake package

The most of packages served now by edpm use git to get source code and cmake to build
the package. As git + cmake became a 'standard' there is a basic recipe class which makes
adding new git+cmake packets straight forward.

As a dive-in example of adding packets,
lets look on how to add such packet using Genfit as a copy-paste example.

[edpm/recipes/genfit.py](edpm/recipes/genfit.py)

**1. Set packet name and where to clone from**

One should change 3 lines:

```python
class GenfitRecipe(GitCmakeRecipe):
    def __init__(self):
        """Installs Genfit track fitting framework"""

        # This name is used in edpm commands like 'edpm install genfit'
        super(GenfitRecipe, self).__init__('genfit')

        # The branch or tag to be cloned (-b flag)
        self.config['branch'] = 'master'

        # Repo address
        self.config['repo_address'] = 'https://github.com/GenFit/GenFit'   
```

Basically that is enough to build the package and one can test:

```bash
edpm install yourpacket
```

**2. Set environment variables**

This is a done in `gen_env` function. By using this function edpm generates environments for
csh/tcsh, bash and python*. So 3 commands to be used in this function:

* `Set(name, value)` - equals `export name=value` in bash
* `Append(name, value)` - equals `export name=$name:value` in bash
* `Prepend(name, value)` - equals `export name=value:$name` in bash

```python
@staticmethod
def gen_env(data):
    path = data['install_path']  # data => installation information 

    yield Set('GENFIT_HOME', path)

    # add bin to PATH
    yield Prepend('PATH', os.path.join(path, 'bin'))

    # add lib to LD_LIBRARY_PATH
    yield Append('LD_LIBRARY_PATH', os.path.join(path, 'lib'))
```

One can test gen_env with:

```bash
edpm env
```

> \* - if other python packages use edpm programmatically to build something


**3. System requirments**

If packet has some dependencies that can be installed by OS packet managers such as apt, one can
add them to os_dependencies array.

```python
os_dependencies = {
    'required': {
        'ubuntu': "libboost-dev libeigen3-dev",
        'centos': "boost-devel eigen3-devel"
    },
    'optional': {
        'ubuntu': "",
        'centos': ""
    },
}
```

> (!) don't remove any sections from the map, leave them blank

To test it one can run:

```python
edpm
req
ubuntu
edpm
req
centos
```

### Adding a custom package

Compared to the previous example, several more functions should be added:

- `setup` - configures the package
- `step_clone`, `step_build`, `step_install` - execute commands to perform the step

**1. Setup**

Setup should provide all values, that are going to be used later in 'step_xxx' functions.
Usually it is just 3 things:

```python
def setup(self):
    #
    # use_common_dirs_scheme() sets standard package variables:
    # source_path  = {app_path}/src/{branch}          # Where the sources for the current version are located
    # build_path   = {app_path}/build/{branch}        # Where sources are built. Kind of temporary dir
    # install_path = {app_path}/root-{branch}         # Where the binary installation is
    self.use_common_dirs_scheme()

    # Git download link. Clone with shallow copy
    self.clone_command = "git clone --depth 1 -b {branch} {repo_address} {source_path}".format(**self.config)

    # make command:
    self.build_command = './configure && make -j{build_threads} install'.format(**self.config)

```

**2. Step functions**

3 docker alike functions that helps to execute stuff:

* `run(command)` - executes the console command
* `workdir(dir)` - changes the working directory
* `env(name, value)` - sets an environment variable

```python
run(self.clone_command)  # Execute git clone command
workdir(self.source_path)  # Go to our build directory
run('./bootstrap')  # This command required to run by rave once...
env('RAVEPATH', self.install_path)
```   
