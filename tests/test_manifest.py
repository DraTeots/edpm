"""
test_manifest.py

Minimal unit tests for plan.py using pytest.
"""

import pytest
import os
from textwrap import dedent
from edpm.engine.manifest import PlanFile
from edpm.engine.env_gen import Prepend, Append, Set

@pytest.fixture
def sample_manifest_file(tmp_path):
    # Create a temporary YAML file
    content = dedent('''\
    global:
      cxx_standard: 17
      build_threads: 8
      environment:
        - set:
            GLOBAL_VAR: "global_value"
        - prepend:
            PATH: "/usr/global/bin"

    dependencies:
      - recipe: manual
        name: local_root
        location: "/opt/myroot"
        environment:
          - set:
              ROOTSYS: "$location"
          - prepend:
              PATH: "$location/bin"
        external-requirements:
          apt: [ libx11-dev, libssl-dev ]
      
      - recipe: github-cmake-cpp
        name: MyLib
        repo_address: "https://github.com/example/mylib.git"
        cmake_flags: "-DENABLE_FOO=ON"
        environment:
          - prepend:
              LD_LIBRARY_PATH: "$install_dir/lib"
    ''')
    manifest_path = tmp_path / "edpm.dependencies.yaml"
    manifest_path.write_text(content, encoding="utf-8")
    return manifest_path

def test_manifest_loading(sample_manifest_file):
    manifest = PlanFile.load(str(sample_manifest_file))

    # Check global config
    assert manifest.cxx_standard == 17
    assert manifest.build_threads == 8

    # Check global environment
    global_env = manifest.get_global_env_actions()
    assert len(global_env) == 2
    assert isinstance(global_env[0], Set)
    assert isinstance(global_env[1], Prepend)

    # Check dependencies
    deps = manifest.dependencies
    assert len(deps) == 2

    dep1 = deps[0]
    assert dep1.name == "local_root"
    assert dep1.recipe == "manual"
    assert dep1.location == "/opt/myroot"
    assert "apt" in dep1.external_requirements
    env_steps = dep1.get_env_actions({"location": "/opt/myroot"})
    # The environment has 2 instructions: set ROOTSYS=/opt/myroot, prepend PATH=/opt/myroot/bin
    assert len(env_steps) == 2
    assert isinstance(env_steps[0], Set)
    assert isinstance(env_steps[1], Prepend)

    dep2 = deps[1]
    assert dep2.name == "MyLib"
    assert dep2.recipe == "github-cmake-cpp"
    assert dep2.repo_address == "https://github.com/example/mylib.git"
    assert dep2.cmake_flags == "-DENABLE_FOO=ON"
    env_steps2 = dep2.get_env_actions({"install_dir": "/tmp/MyLib-install"})
    assert len(env_steps2) == 1
    assert isinstance(env_steps2[0], Prepend)

def test_external_requirements(sample_manifest_file):
    manifest = PlanFile.load(str(sample_manifest_file))

    # gather_requirements for apt
    apt_requirements = manifest.gather_requirements("apt")
    # Expecting from the sample: libx11-dev, libssl-dev
    assert "libx11-dev" in apt_requirements
    assert "libssl-dev" in apt_requirements
    assert len(apt_requirements) == 2

    # gather_all_requirements
    all_reqs = manifest.gather_all_requirements()
    assert "apt" in all_reqs
    assert "libx11-dev" in all_reqs["apt"]
    assert "libssl-dev" in all_reqs["apt"]
    # If none of the dependencies had 'pip', it won't appear in all_reqs.
