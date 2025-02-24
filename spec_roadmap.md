Below is a **step-by-step blueprint** for building and extending EDPM, focusing on **safe, iterative progress**. We’ll start high-level, then break down each phase into smaller, more granular steps. Afterward, we’ll refine the steps again if needed, ensuring they’re neither too large (hard to maintain) nor too small (overly fragmented).

---

## **High-Level Plan**

1. **Fix the Environment Handling**
    - **Goal**: Ensure that when installing a new package, the **environment** from previously installed packages is automatically applied.
    - **Approach**: Modify the `run()` function (and possibly `workdir()`) so that any commands are executed in a shell that has already sourced `env.sh`, or else apply environment actions in-process.

2. **Implement CMake Presets**
    - **Goal**: Generate a [CMake Preset file](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html) so that downstream CMake projects can automatically discover EDPM-installed packages without manual environment variables.
    - **Approach**: Add a method in `EdpmApi` or a new helper module that writes `CMakePresets.json` (or `EDPMConfig.cmake`) based on the Lock file data.

3. **Additional Features and Cleanup**
    - **Examples**:
        - Polish the CLI, ensuring commands like `edpm env`, `edpm config`, etc., work smoothly.
        - Add better error handling around missing `repo_address`, etc.
        - Expand or refine recipe coverage (e.g., finishing the `phasm` recipe).
        - Write more robust integration tests.

We will now break **each** of these major goals into **iterative phases**, then refine each phase further.

---

## **Step-by-Step with Iterative Chunks**

### **Phase 1: Fix the Environment Handling**

**Overall Goal**: When EDPM builds a new package, it sees the environment from previously installed packages, so that “Package B” can see the install path of “Package A.”

---

#### **1A. Preparatory: Confirm environment script generation is stable**

1. **Review the existing `save_shell_environment()` code**:
    - Check how it aggregates environment actions from all installed packages.
    - Verify it generates `env.sh` (and optionally `env.csh`) as intended.

2. **Confirm the `generate_shell_env()` method** merges the global environment and per-dependency environment properly:
    - If needed, add debug prints or quick tests to confirm that all environment lines appear in `env.sh`.

3. **Write a mini-test** (manual or automated) that installs **one** package (e.g., `root` or a trivial “manual” package) and calls `edpm env`.
    - Ensure `env.sh` is valid.
    - If you run `source env.sh` in your shell, check if the environment variables are as expected (e.g., `LD_LIBRARY_PATH` includes the new path).

---

#### **1B. Modify `run()` to use the environment script automatically**

1. **Decide on a technique**:
    - Option A: **Spawn a subshell** that sources `env.sh`, then runs the command. Something like:
      ```python
      subprocess.call(
        f'bash -c "source {env_file} && exec {actual_command}"',
        shell=True
      )
      ```
    - Option B: **Apply environment changes in-process** before each command, by parsing `env.sh` or re-running environment actions.
    - For simplicity, many prefer the “spawn a subshell” approach.

2. **Implement** it in `commands.py` or in `run(args)`:
    - For example, if the original code does:
      ```python
      self.return_code = subprocess.call(self.args, ...)
      ```
      you might do:
      ```python
      sh_script = "source path/to/env.sh && " + self.args
      self.return_code = subprocess.call(sh_script, shell=True, ...)
      ```
    - **Important**: Confirm `env.sh` already exists and is up-to-date before running commands.

3. **Handle edge cases**:
    - If user is installing the **first** package (where `env.sh` might be empty or non-existent).
    - If user is on csh (you could default to bash, or detect shell preference).
    - Possibly let the user override with a CLI flag if they want to skip environment injection.

4. **Test**:
    - **Install** a package that depends on an already-installed package. For instance:
        - Install “root” (which sets certain environment).
        - Then install “geant4” (which might want `ROOTSYS` to be set).
        - Confirm that the second install’s build step can see `ROOTSYS` automatically.
    - Check that the environment variables are truly available in the sub-shell.

---

#### **1C. Clean up & Document**

1. **Cleanup** any debug prints or inline “todo” lines.
2. **Update** docs/README if needed, explaining how EDPM automatically sources `env.sh` for each build command.
3. **(Optional)** Add a small note in the CLI help text that environment is handled automatically—no manual `source env.sh` is required for the build process, though it’s still recommended for user interactions.

At this point, **Phase 1** is **complete**: new packages can see the environment of previously installed packages automatically.

---

### **Phase 2: Implement CMake Presets**

**Overall Goal**: Provide a **CMakePresets.json** (or `EDPMConfig.cmake`) that references all EDPM-installed packages in the lock file, making it easy for the user’s CMake project to locate them without manually setting `CMAKE_PREFIX_PATH`.

---

#### **2A. Create a function for generating the preset/config file**

1. **Choose the format**:
    - For modern CMake (3.21+), a **CMakePresets.json** file can hold build configurations.
    - Alternatively, a simpler `EDPMConfig.cmake` that does something like:
      ```cmake
      set(CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH}:/path/to/packageA:/path/to/packageB")
      ```
    - Decide which is best for your user base. You can do both if you want to.

2. **Implement** a new method, e.g. `EdpmApi.save_cmake_preset()`, that:
    - Loads all installed dependencies from the Lock file.
    - For each installed dependency, **appends** its `install_path` to a list.
    - Writes out a `CMakePresets.json` or `EDPMConfig.cmake`.

3. **Use** the recipe’s config to see if there is a special subfolder that should be appended to the prefix path (e.g., some packages install to `install_path/lib/cmake/MyPackage`). The recipe or lock data might store that info.

4. **Add** a new CLI command if you’d like, for instance:
   ```bash
   edpm cmake-preset
   ```
   That regenerates the file. Or do it automatically as part of the `install` final step.

---

#### **2B. Integrate with main workflows**

1. **In `install_dependency_chain()`** or after each `install`, call your new `save_cmake_preset()`.
    - So each time you finish installing something, you update the CMake config/preset.

2. **Document** how to use it:
    - For a Presets-based approach, you might say:
      ```bash
      cd myProject
      cmake --preset=edpm
      ```
      Or for a config-based approach, you might say:
      ```cmake
      list(APPEND CMAKE_PREFIX_PATH "/home/user/.edpm/installed" )
      include("path/to/EDPMConfig.cmake")
      ```
    - Provide a short example in the README.

3. **Test**:
    - A minimal test CMakeLists that just does `find_package(MyLib REQUIRED)`.
    - Confirm that after installing `MyLib` via EDPM, the `CMakePresets.json` or `EDPMConfig.cmake` approach can find it automatically.

---

#### **2C. Final Review & Cleanup**

1. **Polish** any edge cases, such as no installed packages -> empty file.
2. **Add** a small unit test or integration test that calls `edpm install` and then verifies the presence of `CMakePresets.json` or `EDPMConfig.cmake`.
3. **(Optional)** Extend the logic to handle advanced usage, like if different packages want different `-DCMAKE_INSTALL_PREFIX`, etc.

Now **Phase 2** is **complete**: We have environment-based installs plus a helpful CMake config/preset mechanism.

---

### **Phase 3: Additional Features & Cleanup**

This is more open-ended. Here are examples of tasks that can be done in iterative chunks:

1. **Refine CLI Commands**:
    - E.g., ensure `edpm add`, `edpm clean`, `edpm rm`, etc. handle corner cases gracefully.
    - Possibly unify `rm` and `clean` or clarify their differences.

2. **Improve Error Handling**:
    - If a Git-based recipe is missing `repo_address`, raise a user-friendly error, etc.
    - If the user tries installing a second time without `--force`, confirm we skip gracefully.

3. **Complete/Polish Certain Recipes**:
    - For instance, the `PhasmRecipe` currently has a placeholder. You might fill in the actual build steps.

4. **Better Tests**:
    - Add more integration tests that spin up ephemeral builds:
        - Create a small “HelloWorld” Git repo as a test fixture.
        - Have EDPM install it with a `github-cmake-cpp` recipe.
        - Validate that the installed output is correct.

5. **Finish Documentation**:
    - Possibly add an official “EDPM user guide” explaining how to create a Plan file, how to add custom recipes, etc.
    - Expand the “Troubleshooting” section with examples from real-world usage.

Each of these can be subdivided similarly. For example, if you want to tackle “Complete the PhasmRecipe” in smaller steps:

1. **Find or confirm** the correct Git repo.
2. **Add** its build options to `phasm.py`.
3. **Test** installation locally.
4. **Add** environment steps (if needed).
5. **Document** typical usage (`edpm install phasm`).

---

## **Refined Steps and Iterations**

Below is an **even more granular** view of the first two big phases, to illustrate how you might break them down into bite-sized tasks with a test after each step. Adjust as you see fit:

---

### **Phase 1 Detailed Iteration**

1. **(1A-i)**: Log the environment actions in `generate_shell_env()` so you can see each line.
    - *Test:* Run a `edpm env` on a single manual package, confirm lines are correct.

2. **(1A-ii)**: Ensure `env.sh` is actually stored in a known location (maybe `~/.local/share/edpm/env.sh`).
    - *Test:* Re-run `edpm env`, confirm `env.sh` is created at that location.

3. **(1B-i)**: Modify `commands.py` → `run()` to wrap the command in a `bash -c "source ... && <CMD>"`.
    - *Test:* Install “root”, then “geant4.” Check that geant4 sees `ROOTSYS`.

4. **(1B-ii)**: Handle the “no `env.sh` yet” scenario by writing an empty or minimal file if no dependencies are installed.
    - *Test:* Attempt installing the **very first** dependency. Should not crash.

5. **(1C)**: Cleanup logs, finalize code.
    - *Test:* Confirm everything is stable. Possibly do an integration test across multiple packages.

---

### **Phase 2 Detailed Iteration**

1. **(2A-i)**: Create a minimal function `generate_cmake_config()` in `api.py` that scans `lockfile` and returns a string with a list of `CMAKE_PREFIX_PATH` entries.
    - *Test:* Confirm the string looks correct in a simple print statement.

2. **(2A-ii)**: Write that string to `EDPMConfig.cmake` in `save_cmake_preset()`.
    - *Test:* Confirm the file gets created at the correct location. `cat EDPMConfig.cmake` to verify.

3. **(2B-i)**: Insert a call to `save_cmake_preset()` after `install_dependency_chain()` finishes.
    - *Test:* Install two packages, confirm the final config file references both paths.

4. **(2B-ii)**: Optional: Add the `edpm cmake-preset` CLI subcommand that calls `save_cmake_preset()` on demand.
    - *Test:* Just run `edpm cmake-preset` after installing packages, check the file.

5. **(2C)**: Document usage in README or a docstring.
    - *Test:* Attempt building a small project with `include("EDPMConfig.cmake")`.

---

At that point, the system can install packages, unify environment at build time, and provide a CMake config. The next phases are truly “polish and add features.”

---

## **Conclusion**

Following the above step-by-step plan ensures **safe, incremental** progress. At each step you have:

- **A small, well-defined task**.
- **Immediate tests** to confirm you didn’t break existing functionality.
- **A meaningful improvement** that the project can use right away.

This approach **lowers risk** and **increases confidence**, letting you build EDPM’s environment logic, CMake integration, and advanced features in a systematic, thoroughly tested manner.