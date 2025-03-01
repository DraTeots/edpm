
# edpm

**edpm** (Easy Dependency Package Manager) is a lightweight tool for managing external dependencies in C++/CMake (and occasionally Python) projects. 
Unlike heavy package managers (e.g., Spack) or mixed approaches (like CMake’s FetchContent), 
edpm cleanly separates dependency fetching/building from your main build process—keeping things reproducible and straightforward.

## Key Features
- **Manifest & Lock File**: edpm uses a YAML-based plan (“manifest”) and a lock file to ensure predictable, repeatable installs.
- **Minimal Overhead**: Installs a known set of scientific/engineering packages without building an entire OS worth of sub-libraries.
- **Environment Scripts**: Automatically generates shell scripts (bash/csh) so your tools can locate installed packages via `PATH`, `LD_LIBRARY_PATH`, and `CMAKE_PREFIX_PATH`.
- **Extensible Recipes**: Supports Git + CMake, tarballs, local filesystems, and specialized recipes (e.g., Geant4, ROOT).

## Quick Start
1. **Install edpm**:
   ```bash
   pip install --upgrade edpm
   ```
2. **Initialize & Install**:
   ```bash
   # Create or edit your plan (plan.edpm.yaml) then install
   edpm add root geant4
   edpm install
   ```
3. **Use the Environment**:
   ```bash
   source <(edpm env)   # or edpm env csh > env.csh
   ```
   This makes your newly installed packages available to your shell or CMake builds.

## Why edpm?
- Avoid “version hell” and heavy-lift solutions like Spack when you only need a few well-defined libraries.
- Keep the build and install steps separate: simpler debugging, faster CI, and more control over dependencies.
- Clean integration with CMake through environment variables or optional `CMakePresets.json` / `EDPMConfig.cmake`.

## Contributing & Development
- To hack on edpm itself, clone this repository and install in editable mode:
  ```bash
  pip install -e .
  ```
- We welcome new recipes for scientific libraries, feature requests, and issue reports.

edpm is open-source under the **MIT License**. For complete documentation, recipes, and usage details, please visit the [GitHub project page](https://github.com/DraTeots/edpm).
```