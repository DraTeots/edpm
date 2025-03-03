# cli/init.py

import os
import click

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint

TEMPLATE_CONTENT = """\
# EDPM Manifest Template
# ----------------------
# This file defines:
#   1) A 'global' section for top-level build and environment settings
#   2) A 'dependencies' array of packages that EDPM will install or manage

# Global configuration block
global:
  # cxx_standard: 17      # e.g. 17 or 20 for C++
  # build_threads: 8      # Number of parallel build threads
  environment:
    # - set:
    #     GLOBAL_VAR: "global_value"
    # - prepend:
    #     PATH: "/usr/local/global/bin"
    # - append:
    #     PYTHONPATH: "/usr/local/global/python"

# Dependencies array
dependencies:
  # Example 1: A pre-installed dependency ("manual" recipe)
  # - recipe: manual
  #   name: local_root
  #   location: "/opt/myroot"
  #   environment:
  #     - set:
  #         ROOTSYS: "$location"
  #     - prepend:
  #         PATH: "$location/bin"
  #     - prepend:
  #         LD_LIBRARY_PATH: "$location/lib"

  # Example 2: A GitHub + CMake-based dependency
  # - recipe: github-cmake-cpp
  #   name: MyLib
  #   repo_address: "https://github.com/example/mylib.git"
  #   branch: "main"
  #   cmake_flags: "-DENABLE_FOO=ON"
  #   environment:
  #     - prepend:
  #         PATH: "$install_dir/bin"
  #     - prepend:
  #         LD_LIBRARY_PATH: "$install_dir/lib"

  # Example 3: Another approach for system-level libraries
  # - recipe: manual
  #   name: system_eigen
  #   location: "/usr/include/eigen3"
  #   environment:
  #     - set:
  #         EIGEN_HOME: "$location"

  # require:
  #   apt: [ libeigen3-dev ]
"""

@click.command()
@click.option("--force", is_flag=True, default=False, help="Overwrite existing plan.edpm.yaml if it already exists.")
@click.pass_context
def init(ctx, force):
    """
    Creates a minimal EDPM plan template (plan.edpm.yaml)
    in the current directory with commented placeholders.
    """
    edpm_api = ctx.obj
    # Ensure plan & lock are loaded
    assert isinstance(edpm_api, EdpmApi)
    target_file = edpm_api.plan_file


    if os.path.isfile(target_file) and not force:
        mprint("<red>File '{}' already exists.</red> Use --force to overwrite.", target_file)
        return

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(TEMPLATE_CONTENT)

    mprint("<green>Created minimal EDPM plan:</green> {}", target_file)
    mprint(
        "You can now edit '{}' to define your dependencies or global config.\n"
        "Then run 'edpm install' or 'edpm config' to proceed.",
        target_file
    )
