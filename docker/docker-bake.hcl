// EIC Docker image chain:  ubuntu-root  ->  eic-base  ->  eic-full
//
// IMPORTANT: Linked targets (`contexts = { ... = "target:..." }`) require
// the docker-container driver. The default docker driver builds all targets
// in parallel, ignoring the dependency chain.
//
// One-time setup (creates a builder that supports linked targets):
//
//   docker buildx create --name eic-builder --driver docker-container --use
//
// Then:
//
//   docker buildx bake -f docker-bake.hcl --push             Build + push all
//   docker buildx bake -f docker-bake.hcl eic-base           Build one + deps
//   docker buildx bake -f docker-bake.hcl --no-cache --push  No cache + push
//   docker buildx bake -f docker-bake.hcl --print            Dry run
//   BUILD_THREADS=24 docker buildx bake -f docker-bake.hcl --push
//
// NOTE: the docker-container driver does not support --load (local image
// import). Use --push to push to a registry, then pull locally if needed.
// Or use `docker compose build` instead (works with the default driver).

variable "BUILD_THREADS" {
  default = "8"
}

variable "CXX_STANDARD" {
  default = "20"
}

variable "IMAGE_TAG" {
  default = "latest"
}

// ---------------------------------------------------------------------
//  Shared build args
// ---------------------------------------------------------------------
group "default" {
  targets = ["ubuntu-root", "eic-base", "eic-full", "eic-extra"]
}

target "_common" {
  args = {
    BUILD_THREADS = BUILD_THREADS
    CXX_STANDARD  = CXX_STANDARD
  }
}

// ---------------------------------------------------------------------
//  Layer 1: Ubuntu + CERN ROOT
// ---------------------------------------------------------------------
target "ubuntu-root" {
  inherits   = ["_common"]
  context    = "./ubuntu-root"
  dockerfile = "Dockerfile"
  tags       = ["eicdev/ubuntu-root:${IMAGE_TAG}"]
}

// ---------------------------------------------------------------------
//  Layer 2: EIC base stack
// ---------------------------------------------------------------------
target "eic-base" {
  inherits   = ["_common"]
  context    = "./eic-base"
  dockerfile = "Dockerfile"
  tags       = ["eicdev/eic-base:${IMAGE_TAG}"]
  // When Dockerfile says FROM eicdev/ubuntu-root:latest, use the output
  // of the ubuntu-root target — not the registry image.
  contexts = {
    "eicdev/ubuntu-root:latest" = "target:ubuntu-root"
  }
}

// ---------------------------------------------------------------------
//  Layer 3: Full EIC (EPIC + EICrecon)
// ---------------------------------------------------------------------
target "eic-full" {
  inherits   = ["_common"]
  context    = "./eic-full"
  dockerfile = "Dockerfile"
  tags       = ["eicdev/eic-full:${IMAGE_TAG}"]
  contexts = {
    "eicdev/eic-base:latest" = "target:eic-base"
  }
}

// ---------------------------------------------------------------------
//  Layer 4: EIC extra tools (rucio client + EIC policy package)
// ---------------------------------------------------------------------
target "eic-extra" {
  inherits   = ["_common"]
  context    = "./eic-extra"
  dockerfile = "Dockerfile"
  tags       = ["eicdev/eic-extra:${IMAGE_TAG}"]
  contexts = {
    "eicdev/eic-full:latest" = "target:eic-full"
  }
}
