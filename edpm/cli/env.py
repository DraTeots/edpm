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

    api.save_generator_scripts()
