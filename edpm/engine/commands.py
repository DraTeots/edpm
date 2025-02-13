import os
import subprocess
import sys
import click

executed_commands = []


class Command(object):
    """Base abstract class responsible for any command like run, env, etc"""

    def __init__(self):
        self.is_executed = False

    def execute(self):
        """executes the command. Must be implemented in inherited classes"""
        raise NotImplementedError()

    def __str__(self):
        return "Abstract command"


class RunCommand(Command):
    """Runs an OS command"""

    def __init__(self, args):
        super(RunCommand, self).__init__()
        self.args = args
        self.return_code = 1000000

    def execute(self):
        """executes system command"""

        # Print executing command
        click.secho("EXECUTING:", fg='blue', bold=True)
        click.echo(self.args)

        # Execute the command
        self.return_code = subprocess.call(self.args, stdout=sys.stdout, stderr=sys.stderr, shell=True)
        self.is_executed = True

        # Print the result
        click.secho("Execution done. ", fg='blue', bold=True, nl=False)
        click.echo("Return code = ", nl=False)
        click.secho("%i" % self.return_code, fg='red' if self.return_code else 'green', bold=True)
        click.echo()


class WorkDirCommand(Command):
    """Changes current working directory"""

    def __init__(self, path):
        super(WorkDirCommand, self).__init__()
        self.path = path

    def execute(self):
        """change directory according to path"""
        click.secho("WORKDIR: ", fg='blue', bold=True, nl=False)
        click.echo(self.path)
        click.echo()

        os.chdir(self.path)
        self.is_executed = True


class EnvironmentCommand(Command):
    """Sets environment variable"""

    def __init__(self, name, value):
        super(EnvironmentCommand, self).__init__()
        self.name = name
        self.value = value

    def execute(self):
        """ Set environment variable"""

        click.secho("ENV: ", fg='blue', bold=True, nl=False)
        click.echo("%s = %s" % (self.name, self.value))
        click.echo()
        os.environ[self.name] = self.value
        self.is_executed = True


def run(args):
    """Runs an OS command"""

    command = RunCommand(args)
    _execute_command(command)

    # check run command is ended with return code 0
    if command.return_code != 0:
        click.secho("ERROR", fg='red', bold=True, nl=True)
        click.echo(": Command return code != 0. COMMAND CONTENT:")
        click.echo(command.args)
        click.echo()

        raise OSError()


def workdir(path):
    """Changes working directory """

    _execute_command(WorkDirCommand(path))


def env(name, value):
    """Sets environment variable"""

    _execute_command(EnvironmentCommand(name, value))


def _execute_command(command):
    """Executes any command class"""

    assert isinstance(command, Command)  # sanity check
    command.execute()                    # execute the command!

    # add executed command to the list
    global executed_commands
    executed_commands.append(command)


def is_not_empty_dir(path):
    """Checks the path is existing directory and it is not empty"""

    return os.path.exists(path) and os.path.isdir(path) and os.listdir(path)

