Below is a **user-friendly** introduction to **EDPM Generators**: what they are, how they help you **use** the packages that EDPM has installed, and what commands are available to generate the integration files (shell scripts, CMake scripts, etc.).

---

## EDPM Generators: The Basics

When you install a package with EDPM (e.g. `edpm install root` or `edpm install geant4`), EDPM fetches the source code, builds it, and records the results (the “install path”) in its **Lockfile**. At that point, your system *has* the software installed—but you still need an easy way for your own projects or shells to *find* it.

That’s where **EDPM Generators** come in:
- They **collect all** the environment variables or paths from each installed package,
- Then **generate “integration” files** so that you (or your build system) can effortlessly use them.

---

## Types of Integration Files EDPM Can Generate

### 1. Shell Environment Scripts

- **`env.sh`** (Bash) or **`env.csh`** (C Shell)
- Each script sets the typical environment variables:
- `PATH` (so you can run program executables),
- `LD_LIBRARY_PATH` or `DYLD_LIBRARY_PATH` (so libraries are found at runtime),
- `CMAKE_PREFIX_PATH` (so CMake can locate the installed package),
- and any custom variables like `ROOTSYS`, `GEANT4_DIR`, etc.
- You can simply `source env.sh` (or `source env.csh`) in your terminal, and then your shell “knows” about all EDPM-installed packages.

### 2. CMake Integration

EDPM can also produce **two** special files for **CMake**:

1. **Toolchain/Config file (e.g. `EDPMToolchain.cmake`)**
- A standard `.cmake` file with lines like `set(ROOT_DIR "/path/to/root")`, or `list(INSERT CMAKE_PREFIX_PATH 0 "/my/other/lib")`.
- You can `include(EDPMToolchain.cmake)` in your `CMakeLists.txt` to automatically pick up all dependencies installed by EDPM.

2. **CMake Presets File (`CMakePresets.json`)**
- A modern feature in CMake (3.21+) that stores configuration options in a JSON file.
- You can then do:
```bash
cmake --preset=edpm
cmake --build --preset=edpm
```
and automatically get all EDPM-provided paths or flags.

---

## Using the EDPM “env” Command

EDPM provides the **`edpm env`** command with subcommands that let you **print** or **save** these files. The subcommands might look like this:

1. **`edpm env bash`**
- Prints the **Bash** environment script (what would go into `env.sh`).

2. **`edpm env csh`**
- Prints the **C Shell** environment script (like `env.csh`).

3. **`edpm env cmake`**
- Prints the **CMake** “toolchain” file. It contains `set()` or `list()` commands that CMake can consume.

4. **`edpm env cmake-prof`**
- Prints the **CMake Presets** JSON.

5. **`edpm env save`**
- **Saves** all of the above files to disk, so you can reference or include them. For example, it might save:
- `env.sh` and `env.csh` (in the same directory as your plan?),
- `EDPMToolchain.cmake`,
- `CMakePresets.json`
- After that, you can do `source env.sh` in your shell or `include(EDPMToolchain.cmake)` in your CMake project.

---

## Why Generators Matter

- **Unified Environment Setup**: Rather than manually updating your `PATH` and library paths for each installed package, you rely on EDPM to do it for you.
- **Easy CMake Integration**: If your project is a CMake-based build, you can simply point CMake to the EDPM-generated config or presets, and everything is found automatically.
- **Reproducibility**: Because EDPM references the exact install paths from its **Lockfile**, your environment scripts and toolchain files reflect the precise versions and locations of each installed package.

---

## Typical Workflow

1. **Install Packages**
```bash
edpm install root
edpm install geant4
edpm install dd4hep
# etc.
```
EDPM fetches each library, compiles it, and records `install_path` in its lock file.

2. **Generate Integration Files**
- Option A: **Print** them to stdout:
```bash
edpm env bash         # prints env.sh
edpm env cmake        # prints EDPMToolchain.cmake
```
- Option B: **Save** them all at once:
```bash
edpm env save
```
This writes `env.sh`, `env.csh`, `EDPMToolchain.cmake`, and `CMakePresets.json` to disk.

3. **Use** the Files
- If you prefer **shell usage**:
```bash
source env.sh
# Now PATH and LD_LIBRARY_PATH point to the new software
```
- If you prefer **CMake usage**:
```cmake
# CMakeLists.txt
include("/path/to/EDPMToolchain.cmake")

# or use CMake presets
# cd yourProject
# cmake --preset=edpm
```
- That’s it! Your compiler and runtime linker know where to find the installed packages.

---

## Conclusion

- **Generators** are **“integration tools”** in EDPM that produce environment scripts and CMake integration files.
- **`edpm env`** subcommands either **print** or **save** these files, ensuring your system or build sees all installed libraries.
- With **one** simple command (`edpm env save`), you can set up a fully configured environment for scientific/HPC libraries (like ROOT, Geant4, dd4hep, etc.) and easily integrate them into your own CMake or shell-based workflow.

That’s the **essence** of how EDPM manages your installed packages and how it helps you seamlessly consume them via environment variables and/or CMake.