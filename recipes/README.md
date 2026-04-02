# EIC Conda Recipes

Rattler-build recipes for EIC experiment software packages. These produce conda
packages hosted on ghcr.io and consumed via pixi.

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
