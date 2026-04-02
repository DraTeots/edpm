# EIC Conda Recipes

Rattler-build recipes for EIC experiment software packages. These produce conda
packages hosted on ghcr.io and consumed via pixi.

## Prerequisites: Installing the toolchain (Linux)

All tools here are fully open source. No Anaconda license required.

### Option A — pixi (recommended for end users)

pixi is a single binary that manages conda environments. It is the recommended
way to install and use the EIC software stack.

```bash
# Install pixi
curl -fsSL https://pixi.sh/install.sh | bash

# Restart shell or source the profile
source ~/.bash_profile   # or ~/.bashrc / ~/.zshrc

# Verify
pixi --version
```

### Option B — Miniforge (if you want a traditional conda setup)

Miniforge is the community-maintained, fully open source conda distribution.
It ships with `conda` and `mamba` preconfigured to use conda-forge only —
no Anaconda default channel, no Anaconda license concerns.

```bash
# Download the installer
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"

# Run installer (interactive — accept defaults or use -b for batch/unattended)
bash Miniforge3-Linux-x86_64.sh

# Or unattended install to ~/miniforge3
bash Miniforge3-Linux-x86_64.sh -b -p "${HOME}/miniforge3"

# Activate for current session
source "${HOME}/miniforge3/etc/profile.d/conda.sh"

# Initialize shell (adds conda to ~/.bashrc)
conda init bash       # or: conda init zsh

# Restart shell, then verify
conda --version
mamba --version
```

Miniforge includes `mamba`, a faster drop-in replacement for `conda`:
```bash
# Use mamba instead of conda for faster solves
mamba install <package>
mamba create -n myenv python=3.13
```

### Option C — Micromamba (minimal, no base environment)

Micromamba is a standalone C++ reimplementation — no Python required, no base
environment, single binary. Good for containers and CI.

```bash
# Install to ~/.local/bin
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)

# Or manual install
mkdir -p ~/.local/bin
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C ~/.local/bin/ bin/micromamba
echo 'eval "$(~/.local/bin/micromamba shell hook -s bash)"' >> ~/.bashrc
source ~/.bashrc

# Verify
micromamba --version

# Usage mirrors conda/mamba
micromamba create -n eic -c conda-forge python=3.13
micromamba activate eic
```

### rattler-build (for recipe maintainers only)

Only needed if you are building packages. End users installing via pixi do
**not** need rattler-build.

```bash
# Install via pixi global (simplest)
pixi global install rattler-build

# Or download binary directly
curl -SsL "https://github.com/prefix-dev/rattler-build/releases/latest/download/rattler-build-x86_64-unknown-linux-musl" \
  -o ~/.local/bin/rattler-build
chmod +x ~/.local/bin/rattler-build

# Verify
rattler-build --version
```

## Packages built here

| Package       | Version | Source                                    |
|---------------|---------|-------------------------------------------|
| eic-podio     | 1.6     | AIDASoft/podio                            |
| eic-edm4hep   | 0.99.4  | key4hep/EDM4hep                           |
| eic-dd4hep    | 1.35    | AIDASoft/DD4hep                           |
| eic-edm4eic   | 8.8.0   | eic/edm4eic                               |
| eic-acts      | 44.4.0  | acts-project/acts                         |
| eic-jana2     | 2.4.3   | JeffersonLab/JANA2                        |
| eic-irt       | 1.0.10  | eic/irt                                   |
| eic-algorithms| 1.2.0   | eic/algorithms                            |
| eic-epic      | 25.02.0 | eic/epic                                  |
| eic-npsim     | 1.4.6   | eic/npsim                                 |
| eic-eicrecon  | 1.35.2  | eic/EICrecon                              |

Packages from conda-forge (not rebuilt): ROOT, Geant4, Eigen3, HepMC3, fmt,
Catch2, CLHEP, FastJet, Boost, TBB, nlohmann-json, xerces-c, spdlog, occt.

## Version correspondence

Versions track the EIC container spack configuration. See the `spack-packages.yaml`
reference in the repo for the authoritative version set.

## Building locally

```bash
# Install rattler-build
pixi global install rattler-build

# Build a single package (e.g. podio)
rattler-build build --recipe recipes/podio/

# Build with local channel (for packages depending on other eic-* packages)
rattler-build build --recipe recipes/edm4hep/ \
  --channel conda-forge \
  --channel ./output
```

## Adding a new recipe

1. Create `recipes/<name>/recipe.yaml`
2. If the package needs custom env vars, add `activate.sh` and `deactivate.sh`
3. Add the package to the CI build DAG in `.github/workflows/conda-build.yml`
4. Update this README

## Channel

Packages are published to `oci://ghcr.io/eic/eic-conda` and consumed via:

```toml
# pixi.toml
[project]
channels = ["oci://ghcr.io/eic/eic-conda", "conda-forge"]
```
