import click

from edpm.engine.api import pass_edpm_context, EdpmApi, ENV_SH_PATH, ENV_CSH_PATH


@click.command()
@click.argument('shell_name', nargs=1, default='bash')
@pass_edpm_context
@click.pass_context
def env(ctx, ectx, shell_name):
    """env - prints environment to run installed packages

\b
Examples:
   > edpm env sh   # prints environments in bash and compatible way
   > edpm env csh  # prints for CSH/TCSH syntax
   > edpm env      # same as 'edpm env sh'


\b
So there are 3 ways of managing environment variables

    \b
    1. Dynamically source output of 'edpm env' command (recommended):
     > source <(edpm env)       # for bash

    \b
    2. Save output of 'edpm env' command to a file (can be useful):
      > edpm env sh > your-file.sh     # bash
      > edpm env csh> your-file.csh    # CSH/TCSH

    \b
    3. Use edpm generated 'env.sh' and 'env.csh' files (lazy and convenient):
      > $HOME/.local/share/edpm/env.sh    # bash and compatible
      > $HOME/.local/share/edpm/env.csh   # for CSH/TCSH


      (!) The files are regenerated each time 'edpm <command>' changes something in edpm.
      If you change 'db.json' by yourself, edpm doesn't track it automatically, so call 'edpm env'
      to regenerate these 2 files
    """

    assert isinstance(ectx, EdpmApi)

    # check if DB file already exists
    if not ectx.db.exists():
        print("Database doesn't exist. 'env' command has nothing to do")
        return

    if not shell_name:
        shell_name = 'bash'

    if shell_name in ['csh', 'tcsh']:
        print(ectx.pm.gen_csh_env_text(ectx.db.get_active_installs()))
    else:
        print(ectx.pm.gen_bash_env_text(ectx.db.get_active_installs()))

    print("# env command also regenerated files:")
    print("# {} ".format(ectx.config[ENV_SH_PATH]))
    print("# {} ".format(ectx.config[ENV_CSH_PATH]))
    ectx.save_default_bash_environ()
    ectx.save_default_csh_environ()
