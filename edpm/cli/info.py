# Info - prints extended information of the edpm state

import click

from edpm.engine.api import pass_edpm_context, EdpmApi, print_packets_info
from edpm.engine.db import INSTALL_PATH
from edpm.engine.output import markup_print as mprint


_cmake_opt_help = "List packages in terms of CMake flags"
_flag_help_db = "Prints information about edpm DB"
_flag_help_db_path = "Prints edpm json DB path"


def _no_flags_set(flag_cmake, flag_db, flag_db_path):
    return flag_cmake and flag_db and flag_db_path


@click.command()
@click.option('--cmake', 'flag_cmake', flag_value='cmake', help=_cmake_opt_help)
@click.option('--db', 'flag_db', flag_value='cmake', help=_cmake_opt_help)
@click.option('--db-path', 'flag_db_path', flag_value='cmake', help=_cmake_opt_help)
@pass_edpm_context
@click.pass_context
def info(ctx, ectx, flag_cmake, flag_db, flag_db_path):
    """info - Description

    \b
    Example:
      info --cmake
      info --db-path
    """

    if _no_flags_set(flag_cmake, flag_db, flag_db_path):
        flag_db = True

    assert isinstance(ectx, EdpmApi)

    # We need DB ready for this cli command
    ectx.ensure_db_exists()

    if flag_cmake:
        _print_cmake(ectx)


def _print_cmake(ectx):
    db = ectx.db
    pm = ectx.pm

    flag_names_by_packet_names = pm.recipes_by_name["eicrecon"].cmake_deps_flag_names

    flags = ['-D{}="{}"'.format(flag_names_by_packet_names[name], install_info[INSTALL_PATH])
             for name, install_info in zip(db.packet_names, map(db.get_active_install, db.packet_names))
             if name in flag_names_by_packet_names.keys() and install_info]

    # Fancy print of installed packets
    print(" ".join(flags))


