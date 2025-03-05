import os
import sys
import subprocess
import click


executed_commands = []

class Command(object):
    def __init__(self):
        pass

    def execute(self):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__

class RunCommand(Command):
    def __init__(self, args, env_file):
        super(RunCommand, self).__init__()
        self.args = args
        self.env_file = env_file
        self.return_code = None

    def execute(self):
        click.secho("EXECUTING:", fg='blue', bold=True)
        click.echo(self.args)

        # Wrap actual command so we source env_file first in a bash subshell
        if self.env_file:
            shell_cmd = f'bash -c "source \\"{self.env_file}\\" && env && {self.args}"'
        else:
            shell_cmd = self.args
        self.return_code = subprocess.call(shell_cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True)

        click.secho("Execution done. ", fg='blue', bold=True, nl=False)
        click.echo("Return code = ", nl=False)
        click.secho(f"{self.return_code}", fg='red' if self.return_code else 'green', bold=True)
        click.echo()


class WorkDirCommand(Command):
    def __init__(self, path):
        super(WorkDirCommand, self).__init__()
        self.path = path

    def execute(self):
        click.secho("WORKDIR: ", fg='blue', bold=True, nl=False)
        click.echo(self.path)
        os.chdir(self.path)

class EnvironmentCommand(Command):
    def __init__(self, name, value):
        super(EnvironmentCommand, self).__init__()
        self.name = name
        self.value = value

    def execute(self):
        click.secho("ENV: ", fg='blue', bold=True, nl=False)
        click.echo(f"{self.name} = {self.value}")
        os.environ[self.name] = self.value

def run(args, env_file=None):
    """
    Replaces 'args' with a command that first sources the EDPM environment script if env_file is given,
    ensuring all installed package environment variables are present.
    """

    command = RunCommand(args, env_file)
    _execute_command(command)
    if command.return_code != 0:
        click.secho("ERROR", fg='red', bold=True)
        click.echo(": Command returned nonzero code. The failing command was:")
        click.echo(command.args)
        raise OSError(f"Command failed with return code {command.return_code}")

def workdir(path):
    _execute_command(WorkDirCommand(path))

def env(name, value):
    _execute_command(EnvironmentCommand(name, value))

def _execute_command(command):
    assert isinstance(command, Command), "Passed object is not a Command subclass!"
    command.execute()
    executed_commands.append(command)

def is_not_empty_dir(path):
    return os.path.exists(path) and os.path.isdir(path) and os.listdir(path)
