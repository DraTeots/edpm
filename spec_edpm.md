Below is a **developer-ready specification** that captures the overall **requirements**, **architecture choices**, *
*data handling**, **error handling**, and **testing plan** for the next-generation EDPM. It is distilled from all prior
discussion and is intended to give new developers a clear roadmap for implementing (and extending) EDPM.

---

# EDPM (Easy Dependency Packet Manager) v3

## 1. **Purpose and Goals**

1. **Manage external C++ (and optionally Python) packages** in a way that is:
    - **Decoupled from CMake** (i.e., EDPM can fetch and build dependencies in a standalone manner, independent of any
      particular build system).
    - **Integrates with CMake** through generated configuration files (so that a user’s CMake project can easily locate
      the installed dependencies).
    - **Remains flexible** enough to handle non-CMake packages (Autotools, manual, Python libraries, etc.) by falling
      back to environment-variable–based consumption.

2. **Support a Manifest(Plan) + Lock file design**, ensuring:
    - **Plan** - Manifest in edpm is called "Plan"
    - **Plan file** (`plan.edpm.yaml`) describes *what* packages and configuration of *how* you want them built.
    - **Lock file** (`plan-lock.edpm.yaml`) records *where* they were installed and *exact configuration details* when it
      was installed, ensuring reproducibility.

3. **Keep the dependency graph simple**:
    - EDPM **does not** attempt advanced resolution of version conflicts or deep transitive dependencies. Instead, each
      user-labeled package is installed in a straightforward manner with minimal “chaining.”
    - If package A depends on package B, the user ensures that B is "above in the manifest", 
      i.e. installed (or references it) in a manner consistent with the user’s environment.
    - There is a helper methods to suggest which **external**, i.e. system or other packet managers dependencies 
      one may need to install. But those are no more than suggestions to user. 

---

## 2. **High-Level Architecture**

Below is a conceptual overview of how EDPM v3 works:

1. **Plan file**
    - A YAML file describing:
        - **Global** config (e.g., `cxx_standard`, `build_threads`) and global environment steps.
        - A **list of packages**, each with:
            - A **`recipe`** name (determines how to fetch/build — e.g., `GitCmakeRecipe`, `ManualRecipe`, etc.).
            - A `config` block with fields relevant to that recipe (e.g., `repo_address`, `branch`, etc.).
            - An `environment` block of environment actions that should be applied once the package is installed (used
              for non-CMake or general environment).
            - Optional external requirements (like `apt`, `pip`).

2. **Lock File**
    - A YAML file that stores:
        - The final location of each dependency (`install_path`, any discovered install subfolders).
        - The combined config that was actually used to build (in case defaults or global overrides were merged).
        - The “installed” state, so EDPM knows if a package is up-to-date or not.

3. **Recipes**
    - **Base `Recipe` class**: abstract structure with typical lifecycle steps: `fetch()`, `patch()`, `build()`,
      `install()`, and `post_install()`.
    - **Common Derivatives**:
        - `GitCmakeRecipe` for Git + CMake–based software.
        - `ManualRecipe` for user-installed or pre-built software that just needs to be “registered.”
        - `TarballRecipe` for .tar.gz–based packages (Autotools, etc.).
        - Additional specialized recipes (e.g., `RootRecipe`, `Pythia8Recipe`, etc.).
    - Some number of specialized recipes with predefined configs - for common NP packages such as cern root, geant4, etc.
    - Each recipe can produce an **environment** snippet (via `gen_env()`) so that packages that do not rely on CMake
      can be found via `PATH`, `LD_LIBRARY_PATH`, etc.
    - Since there is no single standard where Cmake puts its resulting config files and many cmakes don't produce
      configs at all, packet is responsible to provide cmake hints (if it is used for cmake)

4. **Environment and CMake Integration**
    - **Environment scripts**: EDPM generates shell scripts (e.g., `env.sh` and `env.csh`) that contain all environment
      updates from *all* installed packages. Sourcing them in the user’s shell makes all packages visible to other
      build systems.
    - **CMake configuration**: EDPM can  generate cmake preset file with the intended configuations. 
    - or equivalently load a single `EDPMConfig.cmake`. This bridging is especially helpful for purely CMake-based
      consumers.

5. **Command-Line Interface (CLI)**
    - **`init`**: Creates a minimal `plan.edpm.yaml` if one doesn’t exist.
    - **`add`**: Adds a new dependency entry to the manifest.
    - **`install`**: Installs packages (either all missing or specific ones).
    - **`env`**: Displays or regenerates the environment scripts.
    - **`info`**: Summarizes installed packages, possible CMake usage instructions, etc.
    - **`config`**: Updates or displays configuration options for packages or global config.
    - **`pwd`** / `set` / `rm` / `clean` etc.: Additional housekeeping commands for pointing EDPM to pre-existing
      installs or removing them.

---

## 3. **Data Handling and Core Objects**

1. **Plan File**
   - Users create plan file manually or via edpm commands.
   - The minimal plan file has only packet names to install
   - The full specification of the plan file is in the separate document. It has:
      1. **`global` block** for top-level build settings and environment changes.
      2. **`packages` array** for listing each dependency or pre-installed package you want EDPM to manage or reference.
      3. **`requirements`** for specifying any system-level or external dependencies (apt, pip, dnf, conan, etc.).
      4. **Flexible environment instructions** that allow multiple `prepend`, `append`, or `set` actions, including the ability to reference placeholders like `"$install_dir"` or `"$location"`.
   - Load and save using `ruamel.yaml` to preserve user comments.

2. **Lock File (`LockfileConfig`)**
    - Internal structure:
      ```python
      {
        "file_version": 1,
        "top_dir": "/absolute/path/where/installed",
        "packages": {
          "foo": {
            "install_path": "/where/it/was/actually/installed",
            "built_with_config": { ... }  # final merged config
          },
          ...
        }
      }
      ```
    - Also loaded/saved with `ruamel.yaml` (though comment preservation may be less critical here).

3. **Recipes (`Recipe` hierarchy)**
    - Each recipe has:
        - A unique `name` identifier (the “key” used by the user).
        - A `config` dictionary storing recipe-specific build instructions (e.g., `repo_address`, `branch`,
          `cmake_flags`, etc.).
        - Lifecycle methods: `fetch()`, `patch()`, `build()`, `install()`, `post_install()`.
        - `gen_env(installed_data)` method returning environment actions for any environment-based consumption.
        - For CMake-based recipes, methods can also produce or update a central `EDPMConfig.cmake` to add `Foo_DIR` or
          `CMAKE_PREFIX_PATH`.

4. **Environment Actions**
    - Types: `Set`, `Append`, `Prepend`, or advanced commands like `RawText`.
    - EDPM aggregates these from **all** packages.
    - Each action can produce:
        - **Bash** snippet.
        - **csh** snippet.
        - (Optionally) a “python environment” update in-process.

5. **Using “Previous” Packages** in Build Steps
    - For CMake-based recipes, EDPM can pass `-DCMAKE_PREFIX_PATH=<path>` for each previously installed dependency. That
      path is discovered from the lock file.
    - For non-CMake or in-process builds, EDPM sets environment variables (e.g., `export PATH=...`) before `make` or
      `configure`.
    - In practice, the API merges known installed packages into the environment or CMake flags (depending on the
      recipe).

---

## 4. **Core Workflow**

1. **Initialization**
    - `edpm init` writes a minimal `plan.edpm.yaml` if none exists.
    - For existing projects, the developer hand-edits or `edpm add`s packages.

2. **Install**
    1. EDPM reads the manifest and lock file.
    2. Merges the user’s **global config** with each dependency’s **config**.
    3. For each dependency in the user-specified install list (or all “missing”):
        - If not already installed (i.e., lock file has no valid `install_path`), EDPM:
            - Prepares environment 
            - **Instantiates** the appropriate recipe class.
            - **Performs** `recipe.run_full_pipeline()` → calls `fetch`, `build`, `install`.
            - On success, writes final `install_path` and config to the lock file.
            - If a package is a `ManualRecipe` and has a user location, EDPM simply records it.
        - If already installed, EDPM skips or re-installs only if `--force` was specified.
    4. After all installs, EDPM **updates** environment scripts (bash/csh) and any consolidated CMake config file.

3. **Environment Generation**
    - `edpm env` or part of the `install` final step:
        - Loads all installed packages from the lock file.
        - For each, calls `recipe.gen_env()` to gather environment actions.
        - Writes aggregated output to `env.sh` and `env.csh`.
        - Writes edpm cmake preset file.
        - Writes or updates a `EDPMConfig.cmake` (or similarly named file) so that a user’s CMake can do
          `find_package()` or at least get the right `CMAKE_PREFIX_PATH`.

4. **Usage in a Build System**
    - **CMake** usage:
        - The user can do one of the following:
            1. `source env.sh` to pick up `PATH`, `LD_LIBRARY_PATH`, etc. Then run `cmake`.
            2. Or `-DCMAKE_PREFIX_PATH=/path/to/edpm_installs` (the location set by EDPM).
            3. Or `include(/path/to/EDPMConfig.cmake)` inside their own CMakeLists.
    - **Non-CMake** usage:
        - Rely purely on the environment script (`env.sh` or `env.csh`).

---

## 5. **Error Handling Strategy**

1. **Recipe Execution Failures**
    - If `fetch`/`build`/`install` fails (e.g., nonzero return code), EDPM logs an error, **does not** mark that
      dependency as installed, and typically aborts the entire installation process.
    - Partial installations remain recorded in the lock file with no `install_path`, or an empty one, so the user can
      diagnose or re-run after fixing the issue.

2. **Config or Manifest Errors**
    - If a dependency references a `recipe` name that does not exist, EDPM should fail fast with a clear error:  
      `"Unknown recipe 'XYZ'. Ensure you spelled it correctly or implemented it."`
    - If a mandatory config field (e.g., `repo_address` for Git-based recipes) is missing, EDPM should raise a
      `ValueError` at recipe initialization.

3. **Lock File Conflicts**
    - If the lock file references an installed path that no longer exists on disk, EDPM can warn and optionally
      re-install if the user sets `--force`.

4. **Topological or “Missing Dep” Errors**
    - Because EDPM does not do a robust dependency resolution, any “dep chaining” is effectively user-driven. If a
      recipe absolutely cannot build without a prior dependency, it should either:
        - Attempt to read it from the lock file environment, or
        - Raise an error if not found.
    - This keeps the system simpler while ensuring clarity for the developer.

---

## 6. **Testing Plan**

To ensure correctness and maintainability, the following **test strategy** is recommended:

1. **Unit Tests** (using `pytest` or similar):
    - **Manifest & Lock File**:
        - Loading/saving with `ruamel.yaml`. Check that user comments remain intact.
        - Edge cases: empty manifest, missing sections, unusual environment steps.
    - **Recipe Classes**:
        - Each recipe has tests that mock or stub out `run()` commands and verifies correct `fetch`/`build` strings.
        - Test environment generation: check the resulting `env.sh` lines or function calls.
    - **Environment Action**:
        - `Set`, `Append`, `Prepend`, `RawText` produce the right shell lines.
        - Confirm that Python environment is updated in-process as expected.

2. **Integration / Smoke Tests**:
    - **Local ephemeral directories**:
        - Make a small “hello world” Git + CMake project. Add it to a test manifest. Run `edpm install` and confirm the
          final artifacts are placed in the lock file.
    - **ManualRecipe**:
        - Provide a “fake” manual dependency and confirm `ld_library_path` is appended properly.
    - **Check synergy**:
        - Install a second package that references the first via environment or CMake. Confirm it sees the first
          package’s location.

3. **System / End-to-End Tests** (Optional in CI if time allows):
    - A Docker-based approach that uses a real minimal OS image (e.g., Ubuntu 20.04) to test installing a known set of
      “real” scientific dependencies (ROOT, Geant4, etc.). This ensures the entire chain works.

4. **Error-Handling Cases**:
    - **Missing config**: Attempt to install a Git recipe with no `repo_address`. Confirm EDPM halts with a readable
      error.
    - **Lock file mismatch**: Remove the installed path from disk. Re-run `edpm install`. Check it suggests
      re-installation or uses `--force`.

By covering these levels of testing, developers can be confident that EDPM remains stable and consistent even as new
recipes or features are introduced.

---

## 7. **Summary and Next Steps**

With this specification, a developer can immediately begin:

1. **Implementing or refining** the `EdpmManifest` and `LockfileConfig` classes with `ruamel.yaml`, ensuring comment
   preservation.
2. **Completing** any missing recipes or integrating them in the `RecipeManager`.
3. **Refining** the CLI commands (`init`, `add`, `install`, `env`, etc.) based on the described workflow.
4. **Writing** automated tests according to the above plan, ensuring coverage of corner cases.

This design gives EDPM v3 a **clear, maintainable architecture** that:

- Manages dependencies in a **manifest/lock** style,
- Provides both **shell environment** and **CMake-based** consumption,
- Accommodates both **CMake** and **non-CMake** dependencies,
- Keeps the approach **lightweight** and **developer-friendly**.

Once implemented, EDPM offers a reproducible, easily scriptable approach to installing (and reusing) scientific software
packages—*without* the overhead or complexity of larger package managers.

Below is an **updated specification** for EDPM v3 that incorporates the **input/output file** mechanism for environment and CMake integration scripts. This update clarifies how users can configure **“in/out”** files (e.g., `env_bash_in`, `env_bash_out`, `cmake_toolchain_in`, `cmake_toolchain_out`, etc.) within the **global** config of their **Plan** file.

---

## 8. **Additional Global Configuration: In/Out Files**

A key enhancement is that **EDPM** can **merge** or **append** its generated output into “existing” user files, or produce brand new files. This is controlled by **in** and **out** file variables in the **global config** block of the Plan. For each integration script, you can set:

- **`env_bash_in` / `env_bash_out`**
   - If you specify `env_bash_in`, EDPM will read that file as a **template**. It looks for a marker line like
     ```bash
     # {{{EDPM-GENERATOR-CONTENT}}}
     ```  
     If found, EDPM will inject the generated environment content in place of that marker.  
     If not found, EDPM appends the environment content to the end.
   - The resulting merged content is saved to `env_bash_out` (or if `env_bash_out` is empty, the user can skip saving).

- **`env_csh_in` / `env_csh_out`**
   - Same approach for C Shell environment scripts.

- **`cmake_toolchain_in` / `cmake_toolchain_out`**
   - For a `.cmake` toolchain/config file.
   - If `cmake_toolchain_in` is set, EDPM will load it, look for the marker line:
     ```cmake
     # {{{EDPM-GENERATOR-CONTENT}}}
     ```  
     If found, it replaces that line with EDPM’s auto-generated lines. If not found, EDPM appends.
   - Then writes the final result to `cmake_toolchain_out`.

- **`cmake_presets_in` / `cmake_presets_out`**
   - A JSON-based approach. If `cmake_presets_in` is set, EDPM will load it as JSON.
   - EDPM merges in the discovered variables/paths (e.g., appending to `cacheVariables`), then writes out the final JSON to `cmake_presets_out`.

### Example Excerpt of `global.config`:

```yaml
global:
  config:
    # Environment files
    env_bash_in: "/home/user/my_bash_base.sh"
    env_bash_out: "/home/user/my_full_bash.sh"
    env_csh_in: "/home/user/my_csh_base.csh"
    env_csh_out: "/home/user/my_full_csh.csh"

    # CMake files
    cmake_toolchain_in: "/home/user/MyBaseToolchain.cmake"
    cmake_toolchain_out: "/home/user/MyCompleteToolchain.cmake"
    cmake_presets_in: "/home/user/BaseCMakePresets.json"
    cmake_presets_out: "/home/user/MergedCMakePresets.json"
```

When running `edpm env save`, EDPM merges the generated content with those input files (if present) and writes the results to the specified output files.

**If any “_out” variable is empty or missing, EDPM does not save** that specific file (and may display a warning). If any “_in” variable is empty, EDPM simply **doesn’t** do the merging logic and either writes a brand-new file (if `_out` is set) or prints a warning.

**Out files default location:** 

1. wherever `xx_out` is in configs
2. otherwise where --top-dir is pointing to
3. otherwise current working directory

---
