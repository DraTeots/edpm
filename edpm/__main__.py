# edpm/main.py
from edpm.cli import edpm_cli


def main():
    """
    Main entrypoint if users run `python -m edpm.main`
    or if you have a setup entrypoint referencing `edpm.main:main`.
    """
    edpm_cli()


# If users run "python -m edpm.main", the code below triggers the CLI.
if __name__ == '__main__':
    main()
