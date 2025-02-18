
## Manifest file

Users create manifest file manually or via edpm commands.

Below is a **proposed YAML manifest format** that covers all requested features for EDPM:

1. **`global` block** for top-level build settings and environment changes.
2. **`dependencies` array** for listing each dependency or pre-installed package you want EDPM to manage or reference.
3. **`external-requirements`** for specifying any system-level or external dependencies (apt, pip, dnf, conan, etc.).
4. **Flexible environment instructions** that allow multiple `prepend`, `append`, or `set` actions, including the ability to reference placeholders like `"$install_dir"` or `"$location"`.

After the examples, you’ll find a **detailed manifest specification** describing each field and how EDPM will interpret it.

---

# 1. Full Example with All Features

```yaml
# edpm.dependencies.yaml

############################################################
# EDPM v2 Manifest - Full Example Demonstration
# ----------------------------------------------------------
# This YAML file demonstrates every feature you asked for:
#   1. Global build config
#   2. External system requirements
#   3. Registering pre-installed packages
#   4. Git + CMake recipes
#   5. Inlined environment instructions with placeholders
#   6. Using multiple 'prepend' or 'append' in environment
#
############################################################

global:
  # ---- Typical build config defaults (applies to all dependencies if they support them):
  cxx_standard: 17
  build_threads: 8

  # ---- Example of a global environment block. 
  #      All dependencies will source these instructions in the final environment scripts.
  environment:
    # We can mix multiple environment actions
    - set:
        GLOBAL_VAR: "some_global_value"

    - prepend:
        PATH: "/usr/local/global/bin"

    # You can have as many environment instructions as you want
    - append:
        PYTHONPATH: "/usr/local/global/python"

dependencies:
  ############################################################
  # 1) A "manual" / pre-installed dependency 
  #    - Used to register an already installed package as a dependency
  ############################################################
  - recipe: manual
    name: local_root           # A custom name (unique ID in the lock file)
    location: "/opt/myroot"    # Where the user installed it
    # This environment block is merged with the global environment 
    # when generating shell scripts or setting environment in-process.
    environment:
      - set:
          ROOTSYS: "$location"   # We can reference $location, meaning "/opt/myroot"
      - prepend:
          PATH: "$location/bin"
      - prepend:
          LD_LIBRARY_PATH: "$location/lib"

    # Example external requirements (like if this package also needs some OS-level packages). 
    # The user can run `edpm req apt` or `edpm req pip` to see these.
    external-requirements:
      apt:
        - libx11-dev
        - libssl-dev
      pip:
        - numpy>=1.21
        - pyyaml

  ############################################################
  # 2) A GitHub + CMake-based dependency 
  #    - The recipe 'github-cmake-cpp' might handle cloning & building.
  ############################################################
  - recipe: github-cmake-cpp
    name: MyLib
    repo_address: "https://github.com/example/mylib.git"
    branch: "main"
    cmake_flags: "-DENABLE_FOO=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON"
    environment:
      # environment blocks can have multiple instructions, each with one action
      - prepend:
          PATH: "$install_dir/bin"
      - prepend:
          LD_LIBRARY_PATH: "$install_dir/lib"
      - set:
          MYLIB_HOME: "$install_dir"

    # Additional external requirements. We’re not enumerating all possible keys, 
    # just apt/pip as an example:
    external-requirements:
      apt:
        - libmylib-dev
      pip:
        - mylib_python_bindings==2.0

  ############################################################
  # 3) Another GitHub + CMake dependency, showing multiple environment instructions 
  ############################################################
  - recipe: github-cmake-cpp
    name: ExtraLib
    repo_address: "https://github.com/example/extra_lib.git"
    branch: "develop"
    # We do not override cmake_flags or environment here, 
    # so it inherits whatever the recipe or global config provides by default.
    environment:
      # demonstrating multiple 'prepend' instructions
      - prepend:
          PATH: "$install_dir/utils/bin"
      - prepend:
          PATH: "$install_dir/example/bin"
      - append:
          LD_LIBRARY_PATH: "$install_dir/addons/lib"

    external-requirements:
      apt:
        - libextra-dev
      conan:
        - zlib/1.2.13
        - catch2/3.1.0

  ############################################################
  # 4) Registering “system” requirements without building code 
  #    - Another approach for referencing an installed dependency
  #      or a large system library. It’s just like “manual.”
  ############################################################
  - recipe: manual
    name: system_eigen
    location: "/usr/include/eigen3"
    # Typically no bin or lib, but we still can specify environment if needed:
    environment:
      - set:
          EIGEN_HOME: "$location"

    external-requirements:
      # For demonstration, we might declare a dnf or apt requirement
      apt: 
        - libeigen3-dev

  ############################################################
  # 5) Something hypothetical like a Python “pip-install” recipe
  ############################################################
  - recipe: pip-install
    name: my_python_tool
    package_name: "somepythonlib"
    version: "1.2.3"
    # environment often not needed for pip packages, but let's do an example
    environment:
      - append:
          PYTHONPATH: "$install_dir/site-packages"
    external-requirements:
      # Possibly if this pip tool also needs system-level libs
      apt: [ libsome-dev ]
      pip: [ requests, "Click>=8.0" ]
```

**Key points shown above**:

- **`global:`** defines top-level build config and environment.
- Each entry in **`dependencies:`** can have:
    - **`recipe:`** name of the “installer logic” (e.g., `github-cmake-cpp`, `manual`, etc.).
    - **`name:`** a unique identifier for the lock file.
    - **`location:`** used for “manual” recipes to register an already-installed directory.
    - **`repo_address`, `branch`, `cmake_flags`:** typical Git info for CMake-based builds.
    - **`environment:`** a list of environment operations (`prepend`, `append`, `set`) with placeholders like `$install_dir` or `$location`.
    - **`external-requirements:`** a dictionary keyed by arbitrary strings (`apt`, `dnf`, `pip`, `conda`, `ubuntu22`, etc.), each listing the needed system packages.

---

# 2. Short Example of a Simple Manifest

Below is a **small** manifest that might be enough for someone new to EDPM. It demonstrates only a few key features:

```yaml
# package.edpm.yaml

global:
  cxx_standard: 17
  environment:
    - set:
        GLOBAL_VAR: "test_value"

dependencies:
  # Example 1: A pre-installed library
  - recipe: manual
    name: local_root
    location: "/opt/root"
    # Minimal environment
    environment:
      - prepend:
          PATH: "$location/bin"
      - prepend:
          LD_LIBRARY_PATH: "$location/lib"

  # Example 2: A GitHub + CMake library
  - recipe: github-cmake-cpp
    name: small_lib
    repo_address: "https://github.com/author/small_lib.git"
    environment:
      - prepend:
          PATH: "$install_dir/bin"
    external-requirements:
      apt: [ libssl-dev ]
```

No advanced fields, just **two** dependencies: one “manual” and one “github-cmake-cpp.”

---

# 3. Full Manifest Specification

Below is a more formal outline of how EDPM interprets each part of the manifest. **All fields are optional** unless marked “required.”

---

### 3.1 Top-Level Keys

1. **`global`** *(object)*
    - **Description**: Holds defaults and global environment. Fields you commonly place here:
        - `cxx_standard` *(number or string)*: If your build recipes support a C++ standard, e.g. 17.
        - `build_threads` *(number)*: The default parallel build count.
        - `environment` *(list of environment instructions)*: Global environment instructions that apply to all dependencies.
            - Each item is an object specifying `prepend`, `append`, or `set` (explained [below](#environment-instructions)).

2. **`dependencies`** *(array)*
    - **Description**: A list of dependencies to be installed or registered by EDPM.
    - **Entry Format**: Each item can be either:
        1. A **string** referencing a built-in recipe name (e.g. `"geant4"`) if your tool auto-maps it.
        2. A **dictionary** with detailed overrides (see [Dependency Dictionary](#dependency-dictionary-format)).

---

### 3.2 Dependency Dictionary Format

When you specify a dependency as a dictionary, you can include the following keys:

- **`recipe`** *(string, required)*: The name of the recipe logic to use. Examples: `"manual"`, `"github-cmake-cpp"`, `"pip-install"`, etc.

- **`name`** *(string)*: A unique identifier for the dependency.
    - If not specified, EDPM might use the same name as `recipe`, but **you** can override it to differentiate multiple instances of the same recipe.

- **`location`** *(string)*:
    - Used primarily by “manual” recipes to indicate a **pre-installed** location to reference.
    - Placeholders like `$location` in environment instructions will expand to this path.

- **`repo_address`** *(string)*:
    - Required by Git-based recipes (e.g., “github-cmake-cpp”) to point to the repository URL.

- **`branch`** or **`tag`** *(string)*:
    - The Git branch or tag to check out. Some recipes might call it “version.”

- **`cmake_flags`, `build_threads`, `cxx_standard`, etc.** *(string or number)*:
    - Additional fields used by certain recipes (like “github-cmake-cpp”).
    - EDPM merges these with the `global` config if relevant.

- **`environment`** *(list of instructions)*:
    - **Description**: A list of environment modifications to apply specifically for this dependency.
    - See [Environment Instructions](#environment-instructions) below.
    - **Placeholders**: You can use `$install_dir` (the final installation path if the recipe builds code) or `$location` (for manual external paths).

- **`external-requirements`** *(object)*:
    - **Description**: A dictionary that can hold any number of keys (e.g., `apt`, `dnf`, `pip`, `conda`, `ubuntu22`, etc.)—one for each external system you want to reference.
    - Each key should map to a list of required packages or strings, e.g.:
      ```yaml
      external-requirements:
        apt: [ libsomething-dev, python3-lz4 ]
        pip: [ SomePythonPackage>=1.2 ]
        dnf: [ cmake, gcc ]
      ```
    - **Usage**: If the user runs `edpm req apt`, EDPM can gather and print all `apt` requirements from every dependency. If the user runs `edpm req pip`, it prints all `pip` entries, etc.

---

### 3.3 Environment Instructions

The **`environment`** block (used both in `global:` and within each dependency) is an **array** of objects. Each object must have exactly one of the following keys: `prepend`, `append`, `set`. The value of that key is itself a **mapping of environment variables** to the string you want to add.

**Examples**:

```yaml
environment:
  # 1) "prepend" example. We can have multiple variables in the same action:
  - prepend:
      PATH: "$install_dir/bin"
      LD_LIBRARY_PATH: "$install_dir/lib"
  # 2) "append" example:
  - append:
      PYTHONPATH: "$install_dir/python"
  # 3) "set" example:
  - set:
      MY_APP_HOME: "$install_dir"
```

#### Repeated Actions

It is **perfectly valid** to have multiple entries that say `prepend:`, e.g.:

```yaml
environment:
  - prepend:
      PATH: "$install_dir/tools/bin"
  - prepend:
      PATH: "$install_dir/extra/bin"
```
Each one will be processed in order.

#### Placeholders

- **`$install_dir`**: Usually set by the recipe if it downloads and builds code.
- **`$location`**: Usually set by “manual” or “system” recipes for a pre-installed path.

You can define more placeholders if your recipes or environment logic supports them (e.g., `$build_dir`, `$source_dir`, etc.).
