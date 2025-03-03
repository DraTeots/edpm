# tests/test_planfile.py
import pytest
import os
from ruamel.yaml import YAML
from tempfile import TemporaryDirectory

from edpm.engine.planfile import PlanFile, PlanPackage

def test_planfile_init_empty():
    pf = PlanFile({})
    assert "global" in pf.data
    assert isinstance(pf.data["packages"], list)
    assert pf.data["packages"] == []

    # default config
    cfg = pf.global_config()
    assert cfg["build_threads"] == 4
    assert cfg["cxx_standard"] == 17
    assert pf.data["global"]["environment"] == []

def test_planfile_load_and_save():
    with TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "plan.edpm.yaml")

        # Create a minimal plan file
        yaml = YAML()
        initial_data = {
            "global": {
                "config": {
                    "build_threads": 8,
                    "cxx_standard": 20
                },
                "environment": []
            },
            "packages": ["root"]
        }
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(initial_data, f)

        # Load
        pf = PlanFile.load(plan_path)
        assert pf.data["global"]["config"]["build_threads"] == 8
        assert pf.data["packages"] == ["root"]

        # Modify
        pf.data["packages"].append("geant4@v11.03")
        pf.save(plan_path)

        # Reload
        pf2 = PlanFile.load(plan_path)
        assert pf2.data["packages"] == ["root", "geant4@v11.03"]

def test_planfile_packages():
    raw_data = {
        "global": {
            "config": {
                "build_threads": 8
            },
            "environment": []
        },
        "packages": [
            "root",
            "geant4@v11.03",
            {
                "mylib": {
                    "fetch": "git",
                    "branch": "main",
                    "environment": [
                        {"prepend": {"PATH": "$install_dir/bin"}},
                    ]
                }
            }
        ]
    }
    pf = PlanFile(raw_data)
    pkgs = pf.packages()
    assert len(pkgs) == 3

    # root
    p0 = pkgs[0]
    assert p0.name == "root"
    assert p0.is_baked_in
    assert p0.config == {}

    # geant4@v11.03
    p1 = pkgs[1]
    assert p1.name == "geant4"
    assert p1.is_baked_in
    assert p1.config == {"version": "v11.03"}

    # mylib
    p2 = pkgs[2]
    assert p2.name == "mylib"
    assert not p2.is_baked_in
    assert p2.config["fetch"] == "git"
    assert p2.config["branch"] == "main"
    env_steps = p2.env_block().parse()
    assert len(env_steps) == 1
    # We won't check the entire step type here, just ensure it parsed.

def test_planfile_add_package():
    pf = PlanFile({})
    assert pf.data["packages"] == []

    # Add a string
    pf.add_package("root")
    assert pf.data["packages"] == ["root"]

    # Add a dictionary
    pf.add_package({"geant4": {"fetch": "git"}})
    assert len(pf.data["packages"]) == 2
    assert pf.data["packages"][1] == {"geant4": {"fetch": "git"}}

    # Confirm we can parse them into PlanPackage objects
    pkgs = pf.packages()
    assert len(pkgs) == 2
    assert pkgs[0].name == "root"
    assert pkgs[1].name == "geant4"
    assert pkgs[1].config == {"fetch": "git"}

def test_planfile_has_and_find():
    raw_data = {
        "packages": ["root", "geant4@v11.03", {"mylib": {"fetch": "git"}}]
    }
    pf = PlanFile(raw_data)

    assert pf.has_package("root") is True
    assert pf.has_package("geant4") is True
    assert pf.has_package("mylib") is True
    assert pf.has_package("foo") is False

    p = pf.find_package("geant4")
    assert p is not None
    assert p.name == "geant4"
    assert p.config["version"] == "v11.03"
