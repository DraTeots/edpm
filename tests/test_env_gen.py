import os
import pytest

# Path to temporary files for testing
TEST_DIR = ""
BASH_IN_PATH = os.path.join(TEST_DIR, "env_bash_in.sh")
BASH_OUT_PATH = os.path.join(TEST_DIR, "env_bash_out.sh")
CSH_IN_PATH = os.path.join(TEST_DIR, "env_csh_in.csh")
CSH_OUT_PATH = os.path.join(TEST_DIR, "env_csh_out.csh")

@pytest.fixture
def setup_test_environment():
    # Prepare the testing environment directory
    os.makedirs(TEST_DIR, exist_ok=True)

    # Create an initial env_bash_in file with a placeholder
    with open(BASH_IN_PATH, "w") as f:
        f.write("# Initial content\n# {{{EDPM-CONTENT}}}\n# End content\n")

    # Create an initial env_csh_in file with a placeholder
    with open(CSH_IN_PATH, "w") as f:
        f.write("# Initial content\n# {{{EDPM-CONTENT}}}\n# End content\n")

    yield  # Test will run here

    # Clean up
    os.remove(BASH_IN_PATH)
    os.remove(BASH_OUT_PATH)
    os.remove(CSH_IN_PATH)
    os.remove(CSH_OUT_PATH)
    os.rmdir(TEST_DIR)


def test_env_save_with_in_out_files(setup_test_environment):
    from edpm.engine.api import EdpmApi

    # Simulating plan and lock file loading (these would be created or read from test fixtures)
    plan_file = "/path/to/plan.edpm.yaml"
    lock_file = "/path/to/plan-lock.edpm.yaml"

    # Mocked EDPM API to load plan and perform the actions
    api = EdpmApi(plan_file=plan_file, lock_file=lock_file)
    api.load_all()  # Simulate loading the plan and lock files

    # Define global config settings for in and out files
    api.plan.data["global"]["config"] = {
        "env_bash_in": BASH_IN_PATH,
        "env_bash_out": BASH_OUT_PATH,
        "env_csh_in": CSH_IN_PATH,
        "env_csh_out": CSH_OUT_PATH,
    }

    # Mock the generated content for testing
    generated_bash_content = "# Generated EDPM content for bash\nexport PATH=/usr/local/bin:$PATH"
    generated_csh_content = "# Generated EDPM content for csh\nsetenv PATH /usr/local/bin:$PATH"

    # Call the function to save the generated files
    api.save_shell_environment(shell="bash", filename=BASH_OUT_PATH)
    api.save_shell_environment(shell="csh", filename=CSH_OUT_PATH)

    # Verify that content is correctly merged into the "out" files
    with open(BASH_OUT_PATH, "r") as f:
        content = f.read()
        assert "# Initial content" in content
        assert "# Generated EDPM content for bash" in content  # EDPM content should be inserted

    with open(CSH_OUT_PATH, "r") as f:
        content = f.read()
        assert "# Initial content" in content
        assert "# Generated EDPM content for csh" in content  # EDPM content should be inserted


def test_env_save_without_in_files(setup_test_environment):
    from edpm.engine.api import EdpmApi

    # Prepare the API without setting any "in" files
    api = EdpmApi(plan_file="/path/to/plan.edpm.yaml", lock_file="/path/to/plan-lock.edpm.yaml")
    api.load_all()

    # Ensure no "in" files are set (empty values)
    api.plan.data["global"]["config"] = {}

    # Call the function to save the generated files
    api.save_shell_environment(shell="bash", filename=BASH_OUT_PATH)
    api.save_shell_environment(shell="csh", filename=CSH_OUT_PATH)

    # Verify that the files were created and contain only the generated content
    with open(BASH_OUT_PATH, "r") as f:
        content = f.read()
        assert "# Generated EDPM content for bash" in content
        assert "export PATH=/usr/local/bin:$PATH" in content

    with open(CSH_OUT_PATH, "r") as f:
        content = f.read()
        assert "# Generated EDPM content for csh" in content
        assert "setenv PATH /usr/local/bin:$PATH" in content


def test_cmake_toolchain_in_out(setup_test_environment):
    # Similar test for cmake toolchain files
    CM_TOOLCHAIN_IN_PATH = os.path.join(TEST_DIR, "cmake_toolchain_in.cmake")
    CM_TOOLCHAIN_OUT_PATH = os.path.join(TEST_DIR, "cmake_toolchain_out.cmake")

    with open(CM_TOOLCHAIN_IN_PATH, "w") as f:
        f.write("# Initial content\n# {{{EDPM-CONTENT}}}\n")

    from edpm.engine.api import EdpmApi

    api = EdpmApi(plan_file="/path/to/plan.edpm.yaml", lock_file="/path/to/plan-lock.edpm.yaml")
    api.load_all()

    # Define global config settings for cmake toolchain files
    api.plan.data["global"]["config"] = {
        "cmake_toolchain_in": CM_TOOLCHAIN_IN_PATH,
        "cmake_toolchain_out": CM_TOOLCHAIN_OUT_PATH
    }

    # Mock the generated content for testing
    generated_toolchain_content = "# Generated EDPM content for CMake\nset(CMAKE_PREFIX_PATH /usr/local)"

    # Save the toolchain file
    api.save_cmake_toolchain(CM_TOOLCHAIN_OUT_PATH)

    # Verify that content is correctly merged into the "out" files
    with open(CM_TOOLCHAIN_OUT_PATH, "r") as f:
        content = f.read()
        assert "# Initial content" in content
        assert "# Generated EDPM content for CMake" in content  # EDPM content should be inserted


def test_cmake_presets_in_out(setup_test_environment):
    # Testing for CMake presets
    CM_PRESETS_IN_PATH = os.path.join(TEST_DIR, "cmake_presets_in.json")
    CM_PRESETS_OUT_PATH = os.path.join(TEST_DIR, "cmake_presets_out.json")

    # Create a simple initial JSON file for presets
    initial_json_content = '{"version": 3, "configurePresets": [{"name": "edpm"}]}'
    with open(CM_PRESETS_IN_PATH, "w") as f:
        f.write(initial_json_content)

    from edpm.engine.api import EdpmApi
    api = EdpmApi(plan_file="/path/to/plan.edpm.yaml", lock_file="/path/to/plan-lock.edpm.yaml")
    api.load_all()

    # Define global config settings for cmake presets
    api.plan.data["global"]["config"] = {
        "cmake_presets_in": CM_PRESETS_IN_PATH,
        "cmake_presets_out": CM_PRESETS_OUT_PATH
    }

    # Call to generate and save CMake presets
    api.save_cmake_presets(CM_PRESETS_OUT_PATH)

    # Verify that the JSON content is merged properly
    with open(CM_PRESETS_OUT_PATH, "r") as f:
        content = f.read()
        assert '{"version": 3,' in content
        assert '"name": "edpm"' in content
        assert '"cacheVariables": {}' in content  # Example cache variable inclusion

