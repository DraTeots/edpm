Below is an updated **Plan (Manifest) file specification** that incorporates the new approach of *
*“fetch”** and **“make”** fields for “composed” recipes, along with the simplified mechanism where a
dependency can also be just a **string** referencing a known built-in recipe (e.g. `"root"`, `"geant4"`).

---

# EDPM Plan (Manifest) Specification

## 1. File Structure

An EDPM plan file is a YAML document with **two main** top-level keys:

1. **`global`** *(optional)*
2. **`dependencies`** *(required)*

### 1.1 `global` Section

The `global:` block can set:

- **Default build configuration** (e.g. `cxx_standard`, `build_threads`)
- **Environment** that applies to *all* dependencies
- **Any other** top-level settings you wish

Example:

```yaml
global:
  cxx_standard: 17
  build_threads: 8
  environment:
    - set:
        GLOBAL_VAR: "some_global_value"
    - prepend:
        PATH: "/usr/local/global/bin"
    - append:
        PYTHONPATH: "/usr/local/global/python"
```

### 1.2 `dependencies` Section

The `dependencies:` key is an array. Each array item describes **one** dependency.  
Each item can be:

1. A **string** naming a known built-in recipe (example: `"root"`, `"geant4"`, `"clhep"`)
2. A **dictionary** that uses a custom name (e.g. `my_packet:`) or direct `'name:'` to define a 
   **composed** or custom recipe with fields like `fetch: ...`, `make: ...`, etc.

---

## 2. Minimal vs. Detailed Dependencies

### 2.1 Minimal Dependency (String Form)

If the user wants to install a well-known pre-baked recipe:

```yaml
dependencies:
  - root
  - geant4
  - clhep
```

In this scenario, EDPM will interpret these strings (`"root"`, `"geant4"`, `"clhep"`) as references
to **specialized** classes (e.g. `RootRecipe`, `Geant4Recipe`, etc.).

### 2.2 Detailed Dependency (Dictionary Form)

When the user needs more control, or wants to define a new package with custom fetch/build, they can
create an entry that is a dictionary of the form:

```yaml
dependencies:
  - my_packet:
    # <key>: <value> pairs describing how to fetch, build, environment, etc.
```

Inside that dictionary, you can mix fields like `fetch:`, `make:`, environment blocks, or anything
else. For instance:

```yaml
dependencies:
  - my_packet:
      fetch: "https://github.com/example/mylib.git"
      make: "cmake"
      branch: "main"
      cmake_flags: "-DENABLE_FOO=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON"

      environment:
        - prepend:
            PATH: "$install_dir/bin"
        - prepend:
            LD_LIBRARY_PATH: "$install_dir/lib"
```

**Explanation**:

- **`my_packet:`** is the *name* of this dependency.
- **`fetch:`** indicates how to fetch the source code (see below for autodetection vs. explicit
  specification).
- **`make:`** indicates how to build it (e.g. `"cmake"`, `"autotools"`, `"custom"`).
- Additional keys (`branch`, `cmake_flags`, etc.) end up in the internal config dictionary for the
  “composed” recipe.
- **`environment:`** is a list of environment operations that EDPM merges into your final
  environment scripts (`env.sh`,
  `env.csh`).

---

## 3. Fetch Mechanism

### 3.1 Autodetection via `fetch:`

If the user sets:

- `fetch: "https://github.com/author/mylib.git"`  
  EDPM deduces **git** fetcher (with default logic, e.g. `git clone`).

- `fetch: "https://example.com/mylib.tar.gz"`  
  EDPM deduces **tarball** fetcher (downloading + extracting).

- `fetch: "/home/user/sources/mylib/"`  
  EDPM deduces a **filesystem** fetcher (local directory or local archive).

### 3.2 Explicitly Specifying Fetcher

Alternatively, the user might prefer to be explicit, separating “which fetcher” from “where to
fetch.” In that case:

```yaml
- my_packet:
    fetch: "git"
    url: "https://github.com/author/mylib.git"
    # optional branch, shallow clone, etc.
```

Or:

```yaml
- my_tar_dep:
    fetch: "tarball"
    url: "https://example.com/mylib.tar.gz"
    # optional extract flags, etc.
```

Or:

```yaml
- localdep:
    fetch: "filesystem"
    path: "/home/romanov/files/my_local_src"
```

In all these cases, EDPM sees `fetch: "git"|"tarball"|"filesystem"` and then uses the associated
“fetcher component.”
The additional fields (`url`, or `path`) go into the config dictionary for that
fetcher.

---

## 4. Make Mechanism

### 4.1 Typical “make:” Options

- **`make: "cmake"`** for a CMake-based build
- **`make: "autotools"`** (or “automake” if you prefer) for a classic
  `./configure && make && make install`
- **`make: "custom"`** or something similar for your own scripts

### 4.2 Additional Make Fields

Any relevant fields can appear under that same dictionary entry. For example, if `make: "cmake"`:

- `cmake_flags`: `"-DUSE_BOOST=ON"`
- `build_threads`: `4`
- etc.

If `make: "autotools"`:

- `configure_flags`: `--enable-shared --prefix=...`
- etc.

All of these would be stored in the internal config dictionary used by the “maker component.”

---

## 5. Referencing Other Dependencies’ Install Paths

It’s common to want:

```yaml
cmake_flags: "-DCMAKE_MODULE_PATH=$root.install_dir/lib/cmake"
```

Where `$root.install_dir` means “the install directory from the lock file for the dependency named
`root`.” EDPM can
expand these placeholders at build time.

**Placeholders**:

- `$<depname>.install_dir`
- `$install_dir` (the current package’s own install path)
- Potentially `$build_dir`, `$source_dir`, etc. (the current package’s build or source directories)

---

## 6. Environment Block

The `environment:` key is a list of environment instructions. Each instruction is an object with
exactly one of `set:`,
`prepend:`, or `append:`.

Example:

```yaml
environment:
  - set:
      MYLIB_HOME: "$install_dir"
  - prepend:
      PATH: "$install_dir/bin"
  - prepend:
      LD_LIBRARY_PATH: "$install_dir/lib"
```

You can combine this with the “maker default environment logic” if you want certain expansions to
happen automatically.
Or you can rely purely on the plan’s environment blocks.

---

## 7. External Requirements

You may still want to declare *system-level* dependencies:

```yaml
external-requirements:
  apt:
    - libssl-dev
    - cmake
  pip:
    - PyYAML>=5.1
```

This can be placed either in the **global** block or inside each **dependency**. Then
`edpm req apt` (for instance) can
print these system packages to install.

---

## 8. Full Example of a Modern EDPM Plan

Below is an **expanded** example combining everything:

```yaml
# plan.edpm.yaml

global:
  cxx_standard: 17
  build_threads: 8
  environment:
    - set:
        GLOBAL_THING: "1"
    - prepend:
        PATH: "/usr/local/global/bin"

dependencies:
  # (A) Minimal usage, just referencing known recipes
  - root
  - geant4

  # (B) A “my_packet” that uses Git fetch + CMake build
  - my_packet:
      fetch: "https://github.com/example/mylib.git"
      make: "cmake"
      branch: "main"
      cmake_flags: "-DCMAKE_MODULE_PATH=$root.install_dir/lib/cmake -DENABLE_FOO=ON"
      environment:
        - prepend:
            PATH: "$install_dir/bin"
        - prepend:
            LD_LIBRARY_PATH: "$install_dir/lib"

  # (C) Another custom dep, explicitly stating fetchers
  - my_tar_dep:
      fetch: "tarball"
      url: "https://example.com/something.tar.gz"
      make: "autotools"
      configure_flags: "--enable-extra"

  # (D) A local filesystem approach
  - local_dep:
      fetch: "filesystem"
      path: "/home/romanov/files/my_local_src"
      make: "cmake"
      cmake_flags: "-DSOME_OPTION=ON"

  # (E) External Requirements
  - datafiles:
      fetch: "filesystem"
      path: "/data/myfiles"
      environment:
        - set:
            DATAFILES_PATH: "$install_dir"
      external-requirements:
        apt:
          - some-data-utils
        pip:
          - requests
```

**Explanation**:

1. **`- root`** or **`- geant4`**: Strings referencing specialized “baked-in” recipes.
2. **`my_packet:`** → `fetch: "git" (autodetected by URL) + make: "cmake"`. The user sets additional
   config fields (
   `branch`, `cmake_flags`).
3. **`my_tar_dep:`** → sets `fetch: "tarball"` explicitly. Then `url: "..."` is used. Builds
   with `autotools`.
4. **`local_dep:`** → uses `fetch: "filesystem"`. The user just points to a local source dir. They
   choose `cmake` for
   building.
5. **`datafiles:`** → also uses `fetch: "filesystem"`. Doesn’t compile anything, but it might still
   set environment or
   have external system-level requirements.

---

## 9. Summary

This **new** plan format merges the best of both worlds:

1. **String dependencies** for **pre-baked** recipes (like `root`, `geant4`).
2. **Dictionary-based** dependencies for **composed** logic, with:
    - `fetch:` (autodetect or explicit)
    - `make:` (which build system to use)
    - Additional config fields (branch, cmake_flags, etc.)
    - Optional environment blocks
    - Optional external requirements

**Placeholders** like `$root.install_dir` or `$install_dir` allow cross-dependency references and
expansions at build
time. This approach fosters both **simplicity** for common packages and **flexibility** for custom
ones.