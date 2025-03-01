# edpm/cli/env.py

import os
import click
from edpm.engine.api import EdpmApi


@click.group("env")
@click.pass_context
def env_group(ctx):
    """
    Manages environment and integration files.

    Subcommands:
      edpm env bash        -> print the bash environment script
      edpm env csh         -> print the csh environment script
      edpm env cmake       -> print the EDPM toolchain .cmake text
      edpm env cmake-prof  -> print the CMakePresets.json text
      edpm env save        -> saves environment scripts & CMake files
    """
    if ctx.obj is None:
        ctx.obj = EdpmApi()
    ctx.obj.load_all()


@env_group.command("bash")
@click.pass_context
def env_bash(ctx):
    """
    Print the pure EDPM Bash environment script (no merging).
    """
    api = ctx.obj
    env_gen = api.create_environment_generator()
    edpm_content = env_gen.build_env_text(shell="bash")
    click.echo(edpm_content)


@env_group.command("csh")
@click.pass_context
def env_csh(ctx):
    """
    Print the pure EDPM C Shell environment script (no merging).
    """
    api = ctx.obj
    env_gen = api.create_environment_generator()
    edpm_content = env_gen.build_env_text(shell="csh")
    click.echo(edpm_content)


@env_group.command("cmake")
@click.pass_context
def env_cmake(ctx):
    """
    Print the EDPM-generated toolchain config (no merging).
    """
    api = ctx.obj
    cm_gen = api.create_cmake_generator()
    text = cm_gen.build_toolchain_text()
    click.echo(text)


@env_group.command("cmake-prof")
@click.pass_context
def env_cmake_prof(ctx):
    """
    Print the EDPM-generated CMakePresets JSON (no merging).
    """
    api = ctx.obj
    cm_gen = api.create_cmake_generator()
    text = cm_gen.build_presets_json()
    click.echo(text)


@env_group.command("save")
@click.pass_context
def env_save(ctx):
    """
    Saves environment scripts & CMake files.

    The Plan file can have, in `global.config`:
      env_bash_in,    env_bash_out,
      env_csh_in,     env_csh_out,
      cmake_toolchain_in,  cmake_toolchain_out,
      cmake_presets_in,    cmake_presets_out

    If *either* the _in or _out is blank (""), we skip.
    If a key is omitted (None), we fallback to planDir + default name for _out
    and we do *not* do any merging for _in.

    For example:
      global:
        config:
          env_bash_in: /home/user/myBaseEnv.sh
          env_bash_out: /home/user/mergedEnv.sh
          cmake_presets_in: /home/user/originalPresets.json
          cmake_presets_out: /home/user/finalPresets.json
          # etc...
    """

    api = ctx.obj
    plan = api.plan
    cfg = plan.global_config_block().data.get("config", {})

    env_gen = api.create_environment_generator()
    cm_gen = api.create_cmake_generator()

    plan_dir = os.path.dirname(os.path.abspath(api.plan_file))

    # Helper to interpret a pair of config keys for "in" and "out"
    def interpret_in_out(key_in, key_out, default_outname):
        """
        Return (inPath, outPath) or (None, None) if we skip.
         - If either is "" => skip with warning
         - If in is None => no merging
         - If out is None => fallback to planDir/default_outname
        """
        vin = cfg.get(key_in, None)
        vout = cfg.get(key_out, None)

        # Check empties
        if vin == "":
            click.echo(f"Warning: config {key_in} is empty => skipping.")
            return (None, None)
        if vout == "":
            click.echo(f"Warning: config {key_out} is empty => skipping.")
            return (None, None)

        if vout is None:
            # fallback to planDir
            vout = os.path.join(plan_dir, default_outname)

        return (vin, vout)

    # 1) BASH
    bash_in, bash_out = interpret_in_out("env_bash_in", "env_bash_out", "env.sh")
    if bash_out is not None:
        env_gen.save_environment_with_infile(shell="bash", in_file=bash_in, out_file=bash_out)

    # 2) CSH
    csh_in, csh_out = interpret_in_out("env_csh_in", "env_csh_out", "env.csh")
    if csh_out is not None:
        env_gen.save_environment_with_infile(shell="csh", in_file=csh_in, out_file=csh_out)

    # 3) Toolchain
    t_in, t_out = interpret_in_out("cmake_toolchain_in", "cmake_toolchain_out", "EDPMToolchain.cmake")
    if t_out is not None:
        cm_gen.save_toolchain_with_infile(in_file=t_in, out_file=t_out)

    # 4) Presets
    p_in, p_out = interpret_in_out("cmake_presets_in", "cmake_presets_out", "CMakePresets.json")
    if p_out is not None:
        cm_gen.save_presets_with_infile(in_file=p_in, out_file=p_out)

    click.echo("Done saving environment & CMake integration files.")
