# edpm

[![PyPI version](https://badge.fury.io/py/edpm.svg)](https://pypi.org/project/edpm/)
[![GitHub Actions Status](https://github.com/eic/edpm/workflows/Tests/badge.svg)](https://github.com/eic/edpm/actions)

**edpm** stands for **e**asy **d**ependency **p**acket **m**anagement

---

## Overview

**edpm** is a lightweight dependency manager for C++/CMake projects that strikes the perfect balance between simplicity and power. When Spack is too complex, Conan pulls in too many dependencies, and CMake's FetchContent blurs the line between dependency acquisition and building, **edpm** offers a focused solution.

By using manifest and lock files, **edpm** separates the dependency acquisition process from your build, giving you reproducible builds without the overhead. It's ideal for scientific and research projects that need a fixed set of dependencies with minimal fuss.

**Key Features:**

- 📦 **Simple CLI** - Install dependencies with straightforward commands like `edpm install geant4`
- 🔄 **Build Separation** - Clear separation between dependency management and project building
- 📝 **Manifest/Lock Design** - Reproducible builds with plain YAML declaration files
- 🔌 **Environment Integration** - Automatically generates scripts for shell and CMake integration
- 🐍 **Pure Python** - Written in Python with minimal dependencies, available via pip

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