# EIC Docker Images

Three layered Docker images for EIC (Electron-Ion Collider) software development:

```
ubuntu-root        Ubuntu 24.04 + Clang 18 + CERN ROOT v6-38-00 + system XRootD
    |
    v
eic-base           Full EIC dependency stack (fmt, CLHEP, Eigen3, Geant4, DD4hep,
    |               ACTS, JANA2, PODIO, EDM4hep, EDM4eic, IRT, Algorithms, ...)
    v
eic-full           + EPIC detector geometry + EICrecon reconstruction framework
```

## Quick start

All commands run from the `docker/` directory.

### docker compose (simplest, works out of the box)

```bash
# Build all three images in dependency order
docker compose build

# Build with more threads (default: 8)
BUILD_THREADS=24 docker compose build

# Build only one image (dependencies built first)
docker compose build eic-base

# No-cache rebuild
docker compose build --no-cache

# Build + push to Docker Hub
docker compose build --push

# Custom tag
IMAGE_TAG=v1.0 docker compose build

# Run a container
docker compose run --rm eic-full
```

### docker buildx bake (advanced: linked targets, dry-run)

Uses `docker-bake.hcl`.  The `contexts` blocks wire `FROM` dependencies at
the BuildKit level so targets build in the correct order.

**One-time setup** — linked targets require the `docker-container` driver
(the default `docker` driver ignores `contexts` and builds everything in
parallel):

```bash
docker buildx create --name eic-builder --driver docker-container --use
```

Then:

```bash
# Build + push all (sequential via linked targets)
docker buildx bake -f docker-bake.hcl --push

# Build one target (+ its deps automatically)
docker buildx bake -f docker-bake.hcl --push eic-base

# No cache + push
docker buildx bake -f docker-bake.hcl --no-cache --push

# Dry run — print resolved config as JSON, build nothing
docker buildx bake -f docker-bake.hcl --print

# Custom threads + tag
BUILD_THREADS=24 IMAGE_TAG=v1.0 docker buildx bake -f docker-bake.hcl --push
```

> **Note:** the `docker-container` driver does not support `--load` (importing
> into local Docker). Use `--push` to push to a registry.  To build locally
> without pushing, use `docker compose build` instead.
>
> Always pass `-f docker-bake.hcl` — without it bake discovers
> `docker-compose.yml` first (higher in lookup order) and launches all targets
> in parallel since compose `depends_on` is a runtime concept, not a build
> dependency.

### PowerShell

Environment variables are set differently in PowerShell:

```powershell
# Set variables then build (compose)
$env:BUILD_THREADS = "24"
docker compose build

# Or one-liner with semicolon
$env:BUILD_THREADS = "24"; docker compose build

# Bake
$env:BUILD_THREADS = "24"; docker buildx bake -f docker-bake.hcl --push

# Custom tag
$env:IMAGE_TAG = "v1.0"; docker compose build

# Clean up env vars after
Remove-Item Env:\BUILD_THREADS
Remove-Item Env:\IMAGE_TAG
```

### build_images.py (scripted alternative)

```bash
# Build all (auto-detects CPUs)
python3 docker/build_images.py

# Build with 24 threads, no cache, push
python3 docker/build_images.py --no-cache --push -j 24

# Build only eic-base (assumes ubuntu-root exists)
python3 docker/build_images.py eic-base

# Dry run
python3 docker/build_images.py --dry-run
```

### Building individual images manually

```bash
docker buildx build --tag eicdev/ubuntu-root:latest --build-arg BUILD_THREADS=24 docker/ubuntu-root
docker buildx build --tag eicdev/eic-base:latest    --build-arg BUILD_THREADS=24 docker/eic-base
docker buildx build --tag eicdev/eic-full:latest    --build-arg BUILD_THREADS=24 docker/eic-full
```

## Build arguments

| Argument | Default | Description |
|---|---|---|
| `BUILD_THREADS` | `8` | Parallel make/cmake jobs (`-j`) |
| `CXX_STANDARD` | `20` | C++ standard for all packages |

Image-specific version ARGs (e.g. `VERSION_ACTS`, `VERSION_GEANT4`) can be
overridden at build time but default to versions matching the official EIC
spack environment.

## Package versions (eic-base)

| Package | Version | Source |
|---|---|---|
| fmt | 11.2.0 | GitHub (source) |
| CLHEP | 2.4.7.1 | GitLab CERN (source) |
| Eigen3 | 3.4.0 | GitLab (source) |
| Catch2 | 3.8.1 | GitHub (source) |
| FastJet | 3.5.0 | fastjet.fr (tarball, autotools) |
| HepMC3 | 3.3.0 | GitLab CERN (source) |
| Geant4 | 11.3.2 | GitHub (source) |
| PODIO | 01-06 | GitHub (source) |
| VGM | 5.3.1 | GitHub (source) |
| EDM4HEP | 00-99-04 | GitHub (source) |
| EDM4EIC | 8.8.0 | GitHub (source) |
| DD4hep | 01-35 | GitHub (source) |
| ActsSVG | 0.4.56 | GitHub (source) |
| OnnxRuntime | 1.17.0 | GitHub (prebuilt binary, CPU-only) |
| ACTS | 44.4.0 | GitHub (source) |
| JANA2 | 2.4.3 | GitHub (source) |
| IRT | 1.0.10 | GitHub (source) |
| Algorithms | 1.2.0 | GitHub (source) |

## Package versions (eic-full)

| Package | Version | Source |
|---|---|---|
| EPIC | 25.02.0 | GitHub (source) |
| EICrecon | 1.35.2 | GitHub (source) |

## apt package layout

Dependencies are split across layers to keep rebuilds fast:

**ubuntu-root** installs foundational tools and ROOT build dependencies:
compilers (clang-18, gcc, gfortran), build tools (cmake, ninja, ccache),
X11/GL libraries, XRootD, and Python 3 packages.

**eic-base** adds EIC-specific system libraries:
Boost, Xerces-C, Qt5, OpenCASCADE, Intel TBB, spdlog, ZeroMQ, Microsoft GSL,
and pybind11.

> **Note:** `nlohmann-json3-dev` and `libfmt-dev` are deliberately **not**
> installed. ACTS bundles its own nlohmann/json (v3.10.5) which conflicts with
> the system copy (v3.11.3) due to ABI namespace differences. fmt is built from
> source (v11.2.0) because PODIO requires `fmt::println(FILE*,...)` added in
> fmt 11, while Ubuntu 24.04 ships v10.1.1.

## Debugging builds

Use buildx debug mode to drop into a shell at the failing step:

```bash
# bash/Linux
BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain -f docker/eic-base/Dockerfile docker/eic-base

# PowerShell
$env:BUILDX_EXPERIMENTAL = "1"; docker buildx debug --invoke bash build --progress=plain -f docker/eic-base/Dockerfile docker/eic-base
```

## File structure

```
docker/
  README.md              This file
  docker-compose.yml     For docker compose build/push/run (works out of the box)
  docker-bake.hcl        For docker buildx bake (requires docker-container driver)
  build_images.py        Python build script (alternative)
  ubuntu-root/
    Dockerfile           Layer 1: Ubuntu 24.04 + CERN ROOT
    bashrc               Shell configuration
  eic-base/
    Dockerfile           Layer 2: EIC dependency stack
  eic-full/
    Dockerfile           Layer 3: EPIC + EICrecon
```
