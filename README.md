# edpm

[![PyPI version](https://badge.fury.io/py/edpm.svg)](https://pypi.org/project/edpm/)
[![EDPM Tests](https://github.com/DraTeots/edpm/actions/workflows/test.yaml/badge.svg)](https://github.com/DraTeots/edpm/actions/workflows/test.yaml)

**edpm** stands for **e**asy **d**ependency **p**acket **m**anagement

---

## Overview

**edpm** is a lightweight dependency manager for C++/CMake projects that tries to balance between
simplicity and power. 

**When do you need it?** (tale) You happily live in a common C++ CMake development environment 
until one day your project needs a couple of dependencies to be built with pretty custom configurations.
As usual in scientific software, these dependencies are not on Conan or Conda. Spack doesn't have correct
flags and installs around 15,034 of low-level dependencies for the next 10 hours and... fails
building perl (true story). You then choose to use simple Cmake FetchContent, right? - But your 
dependency management is now tightly coupled with the build system. And you not only struggle
from architecture point, but notice that CMake configuration now takes around 2 hours, as CERN ROOT 
compilation takes 93 minutes and Geant4 is another 27 minutes and sometimes spontaneously 
cmake decides to rebuild them.  
Finally, you managed to manage your dependencies but now need to install your
whole custom stack on cluster machines with old obscure linux, and build container images and 
you want to keep the building in coherent way, making adjustments for systems... 
You probably understand now! We claim that in this scenario `edpm` is more convenient 
than a pile of overgrown barely readable bash scripts.

When Conan is too complex, Spack pulls in too many dependencies, and CMake's FetchContent blurs the
line between dependency acquisition and building, **edpm** offers a focused niche solution.

**Key Features:**

- 📦 **Simple CLI** - Install dependencies with straightforward commands like `edpm install geant4`
- 🔄 **Build Separation** - Clear separation between dependency management and project building
- 📝 **Manifest/Lock Design** - Reproducible builds with plain YAML declaration files
- 🔌 **Environment Integration** - Automatically generates scripts for shell and CMake integration
- 🐍 **Pure Python** - Written in Python with minimal dependencies, available via pip ***on any machine***


**What EDPM is not?**
- Not a general-purpose package manager - it doesn't build dependency tree nor download prebuilt 
  binaries (but can download whatever if you config so)
- Not a replacement for your OS package manager - it won't install system libraries
- Not a build system - it helps to build dependencies and integrate into your CMake project. But doesn't replace CMake
- Not an environment management - not conda, mise, etc. It manages environment scripts but if those needed for integration. 
- Not a version resolver - it trusts you to pick compatible versions of packages
- Not trying to be the next Spack/Conan - it deliberately stays lightweight for a specific use case

Happy building!

---

## Rationale & Philosophy

1. **Separation of Dependency and Build Steps:**
    - Modern CMake approaches like FetchContent tend to mix dependency downloads with the build process, leading to longer configure times and less control.
    - **edpm** separates dependency "fetch/install" from the main build, similar to npm/yarn for JavaScript packages.

2. **Keeping It Simple:**
    - In scientific projects, the full complexity of tools like Spack (which often installs numerous low-level packages) is unnecessary.
    - **edpm** is designed to be more advanced than a bash script, yet far less complex than a full package manager.

3. **Focused, User-Friendly Approach:**
    - **Manifest and Lock Files:** JSON/YAML manifest and lock files ensure everyone uses identical dependency versions.
    - **Environment Generation:** Produces shell scripts and CMake configs to easily set up your environment.
    - **Integration with Existing Installations:** Register pre-installed dependencies to avoid rebuilding what's already available.

---

## Comparison with Other Approaches

- **CMake FetchContent / CPM.cmake:**  
  While FetchContent is convenient for pure CMake projects, it slows down configuration and mixes dependency acquisition with the build.
  **edpm** keeps these concerns separate, with explicit install commands and independent environment scripts.

- **Spack / Conan:**  
  These powerful tools handle complex dependency graphs and version conflicts but install many low-level packages and have steep learning curves.
  **edpm** is designed for scenarios where such complexity is overkill, installing a known set of dependencies with fixed versions.

- **vcpkg & CGet:**  
  vcpkg adds complexity with build profiles (triplets), while CGet (no longer maintained) had the simplicity **edpm** aims for.
  **edpm** borrows CGet's simplicity while adding modern features like environment management and manifest/lock files.

---

## Quick Start

### Installing edpm

Install edpm via pip:

```bash
# System-level installation:
pip install edpm

# Or user-level:
pip install --user edpm
```

### Basic Usage

```bash
# Create a new plan file
edpm init

# Add a package to the plan
edpm add root

# Install the package
edpm install

# Set up your environment
source $(edpm env bash)
```

### Working with Projects

```bash
# Set installation directory
edpm --top-dir=/path/to/install/dir

# Add multiple packages
edpm add root geant4

# Install everything in the plan
edpm install

# View information about installed packages
edpm info

# Generate and use environment scripts
source $(edpm env bash)

# CMake integration (in your CMakeLists.txt)
include("/path/to/install/dir/EDPMToolchain.cmake")
```

### Using Pre-installed Packages

If you already have packages installed that you want to integrate:

```bash
# Reference an existing ROOT installation
edpm add --existing root /path/to/root

# Check that it's recognized
edpm info
```

---

## Plan File Format

**edpm** uses a YAML-based plan file to define packages. Here's a simple example:

```yaml
# Global configuration
global:
  cxx_standard: 17
  build_threads: 8

# Dependencies
packages:
  - root
  - geant4@v11.0.3
  - mylib:
      fetch: git
      url: https://github.com/example/mylib.git
      branch: main
      make: cmake
      cmake_flags: "-DBUILD_TESTING=OFF"
```

For more details, see [Plan File Documentation](https://github.com/eic/edpm/blob/main/spec_plan_file.md).

---

## Configuration

View and modify configuration using the `config` command:

```bash
# Show global configuration
edpm config

# Show configuration for a specific package
edpm config root

# Set global options
edpm config cxx_standard=17 build_threads=8

# Set package-specific options
edpm config root branch=master
```

## Where edpm Data is Stored

EDPM stores data in the platform's standard user data directory:

```
~/.local/share/edpm/env.sh     # Bash environment script
~/.local/share/edpm/env.csh    # CSH environment script
~/.local/share/edpm/plan.yaml  # Default plan file
```

You can control this location by setting the `EDPM_DATA_PATH` environment variable.

---

## Advanced Usage

### Environment Management

Generate and view environment scripts:

```bash
# Generate bash environment
edpm env bash

# Generate csh environment
edpm env csh

# Generate CMake toolchain
edpm env cmake

# Save all environment files
edpm env save
```

### Package Management

```bash
# View package paths
edpm pwd root

# Remove a package
edpm rm root

# Clean build artifacts
edpm clean root

# List system requirements
edpm req ubuntu root geant4
```

---

## Troubleshooting

### Installation Issues

If you encounter certificate problems (common on systems like JLab):

```bash
pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org edpm
```

### Missing Dependencies

If you need to install system dependencies:

```bash
# List required system packages for Ubuntu
edpm req ubuntu eicrecon
sudo apt-get install [packages listed]

# For CentOS/RHEL
edpm req centos eicrecon
sudo yum install [packages listed]
```

---

## Development and Contributing

### Manual or Development Installation

```bash
git clone https://github.com/eic/edpm.git
cd edpm
pip install -e .
```

### Adding a Package Recipe

Each package is represented by a Python recipe file that provides instructions for download, build, and environment setup. See [Adding a Package](docs/add_package.md) for details.

---

## License

EDPM is released under the [LICENSE](LICENSE) (add your license here).