#!/usr/bin/env python3
"""Build (and optionally push) the EIC Docker image chain using docker buildx.

Image chain (each layer depends on the previous one):

    ubuntu-root  ->  eic-base  ->  eic-full

Usage examples:

    # Build all three images sequentially (default)
    python3 build_images.py

    # Build only ubuntu-root and eic-base
    python3 build_images.py ubuntu-root eic-base

    # Build all, no cache, 24 threads, and push
    python3 build_images.py --no-cache --push -j 24

    # Build and tag as v1.0 (images get both :v1.0 and :latest)
    python3 build_images.py --tag v1.0 --latest --push

    # Multi-platform build + push  (requires buildx builder with multi-arch)
    python3 build_images.py --platform linux/amd64,linux/arm64 --push
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import shlex
import subprocess
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

# ---------------------------------------------------------------------------
#  Logging
# ---------------------------------------------------------------------------
log = logging.getLogger("build_images")

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent

# Ordered dict: name -> (org, subdir, depends_on)
# The order defines the default build sequence.
IMAGE_CHAIN: OrderedDict[str, dict] = OrderedDict([
    ("ubuntu-root", {
        "org": "eicdev",
        "path": SCRIPT_DIR / "ubuntu-root",
        "depends_on": None,
    }),
    ("eic-base", {
        "org": "eicdev",
        "path": SCRIPT_DIR / "eic-base",
        "depends_on": "ubuntu-root",
    }),
    ("eic-full", {
        "org": "eicdev",
        "path": SCRIPT_DIR / "eic-full",
        "depends_on": "eic-base",
    }),
])


# ---------------------------------------------------------------------------
#  Data classes
# ---------------------------------------------------------------------------
@dataclass
class ImageSpec:
    """Everything needed to build one image."""
    name: str
    org: str
    path: Path
    tag: str = "latest"
    depends_on: Optional[str] = None
    build_args: dict = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.org}/{self.name}:{self.tag}"

    @property
    def latest_name(self) -> str:
        return f"{self.org}/{self.name}:latest"


@dataclass
class BuildResult:
    """Outcome of a single build / push step."""
    action: str
    image: str
    retcode: int
    start: datetime
    end: datetime

    @property
    def duration(self):
        return self.end - self.start

    @property
    def duration_str(self):
        return str(self.duration).split(".")[0]  # drop microseconds


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------
def _run(cmd: str | list[str], *, dry_run: bool = False) -> BuildResult:
    """Run *cmd*, stream output live, return a BuildResult."""

    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    header = " ".join(cmd)
    log.info("=" * min(len(header) + 6, 120))
    log.info("RUN:  %s", header)
    log.info("=" * min(len(header) + 6, 120))

    if dry_run:
        log.info("[dry-run] skipped")
        now = datetime.now()
        return BuildResult("dry-run", "", 0, now, now)

    start = datetime.now()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.stdout is not None
    for raw_line in iter(proc.stdout.readline, b""):
        line = raw_line.decode("utf-8", errors="replace")
        sys.stdout.write(line)
        sys.stdout.flush()

    proc.wait()
    end = datetime.now()

    log.info("--- done (retcode %d, %s) ---\n", proc.returncode, str(end - start).split(".")[0])
    return BuildResult("", "", proc.returncode, start, end)


# ---------------------------------------------------------------------------
#  Builder
# ---------------------------------------------------------------------------
class DockerBuilder:
    def __init__(
        self,
        images: Sequence[ImageSpec],
        *,
        no_cache: bool = False,
        push: bool = False,
        tag_latest: bool = False,
        platform: Optional[str] = None,
        progress: str = "auto",
        dry_run: bool = False,
    ):
        self.images = list(images)
        self.no_cache = no_cache
        self.push = push
        self.tag_latest = tag_latest
        self.platform = platform
        self.progress = progress
        self.dry_run = dry_run
        self.results: list[BuildResult] = []

    # -- public API ---------------------------------------------------------

    def build_all(self) -> int:
        """Build every image in order.  Returns 0 on success, first non-zero retcode on failure."""
        for img in self.images:
            rc = self._build_one(img)
            if rc != 0:
                log.error("Build of %s FAILED (retcode %d) — aborting chain.", img.full_name, rc)
                return rc
        return 0

    # -- internals ----------------------------------------------------------

    def _build_one(self, img: ImageSpec) -> int:
        # Assemble the buildx command
        cmd: list[str] = ["docker", "buildx", "build"]

        # Tags
        tags = [img.full_name]
        if self.tag_latest and img.tag != "latest":
            tags.append(img.latest_name)
        for t in tags:
            cmd += ["--tag", t]

        # Build args
        for k, v in img.build_args.items():
            cmd += ["--build-arg", f"{k}={v}"]

        # Flags
        if self.no_cache:
            cmd.append("--no-cache")

        if self.platform:
            cmd += ["--platform", self.platform]

        cmd += ["--progress", self.progress]

        # Push or load
        if self.push:
            cmd.append("--push")
        else:
            cmd.append("--load")

        # Context directory (where the Dockerfile lives)
        cmd.append(str(img.path))

        # Run
        result = _run(cmd, dry_run=self.dry_run)
        result.action = "build+push" if self.push else "build"
        result.image = img.full_name
        self.results.append(result)

        return result.retcode

    # -- summary ------------------------------------------------------------

    def print_summary(self):
        log.info("")
        log.info("SUMMARY")
        log.info("-" * 100)
        log.info("%-14s %-40s %-9s %-12s %-20s %-20s",
                 "ACTION", "IMAGE", "RETCODE", "DURATION", "START", "END")
        log.info("-" * 100)
        for r in self.results:
            log.info("%-14s %-40s %-9d %-12s %-20s %-20s",
                     r.action, r.image, r.retcode,
                     r.duration_str,
                     r.start.strftime("%Y-%m-%d %H:%M:%S"),
                     r.end.strftime("%Y-%m-%d %H:%M:%S"))
        log.info("-" * 100)


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main(argv: Sequence[str] | None = None) -> int:
    cpu_count = max(1, multiprocessing.cpu_count() - 1)

    parser = argparse.ArgumentParser(
        description="Build the EIC Docker image chain (ubuntu-root -> eic-base -> eic-full).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "images", nargs="*",
        help=(
            "Images to build, in order.  "
            f"Known names: {', '.join(IMAGE_CHAIN)}.  "
            "Default: build the full chain."
        ),
    )
    parser.add_argument("--tag", default="latest",
                        help="Image tag (default: latest)")
    parser.add_argument("--latest", action="store_true",
                        help="Also tag images as :latest (useful with --tag=v1.0)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Pass --no-cache to docker buildx build")
    parser.add_argument("--push", action="store_true",
                        help="Push images after building (uses buildx --push)")
    parser.add_argument("--platform", default=None,
                        help="Target platform(s), e.g. linux/amd64,linux/arm64")
    parser.add_argument("--progress", default="auto", choices=["auto", "plain", "tty", "rawjson"],
                        help="Buildx progress output style (default: auto)")
    parser.add_argument("-j", "--jobs", type=int, default=cpu_count,
                        help=f"BUILD_THREADS passed to cmake (default: {cpu_count})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Also write log output to this file")

    args = parser.parse_args(argv)

    # --- logging setup ---
    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    log.addHandler(console)
    log.setLevel(logging.DEBUG)

    if args.log_file:
        fh = logging.FileHandler(args.log_file)
        fh.setFormatter(fmt)
        log.addHandler(fh)

    # --- resolve which images to build ---
    if args.images:
        names = args.images
    else:
        names = list(IMAGE_CHAIN.keys())
        log.info("No images specified — building full chain: %s", " -> ".join(names))

    # Validate names
    for n in names:
        if n not in IMAGE_CHAIN:
            log.error("Unknown image '%s'.  Known images: %s", n, ", ".join(IMAGE_CHAIN))
            return 1

    # Build ImageSpec list
    specs: list[ImageSpec] = []
    for n in names:
        info = IMAGE_CHAIN[n]
        spec = ImageSpec(
            name=n,
            org=info["org"],
            path=info["path"],
            tag=args.tag,
            depends_on=info["depends_on"],
            build_args={"BUILD_THREADS": str(args.jobs)},
        )
        specs.append(spec)

    log.info("Images to build: %s", " -> ".join(s.full_name for s in specs))
    log.info("Build threads:   %d", args.jobs)
    log.info("Push:            %s", args.push)
    log.info("No-cache:        %s", args.no_cache)
    if args.platform:
        log.info("Platform:        %s", args.platform)
    log.info("")

    # --- build ---
    builder = DockerBuilder(
        specs,
        no_cache=args.no_cache,
        push=args.push,
        tag_latest=args.latest,
        platform=args.platform,
        progress=args.progress,
        dry_run=args.dry_run,
    )

    retcode = builder.build_all()
    builder.print_summary()

    return retcode


if __name__ == "__main__":
    sys.exit(main())
