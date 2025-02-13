import inspect
import io
import os
import click


from edpm.engine.db import PacketStateDatabase, merge_db
from edpm.engine.recipe import Recipe
from edpm.engine.recipe_manager import RecipeManager
from edpm.engine.output import markup_print as mprint
from edpm.engine.manifest import EdpmManifest

EDPM_HOME_PATH = 'edpm_home_path'       # Home path of the edpm
EDPM_DATA_PATH = 'edpm_data_path'       # Path where
DB_FILE_PATH = 'db_file_path'           # Database file path
ENV_SH_PATH = 'env_sh_path'             # SH environment generated file path
ENV_CSH_PATH = 'env_csh_path'           # CSH environment generated file path


class EdpmApi(object):
    """This class holds data that is provided to most edpm CLI commands"""

    def __init__(self):
        self.db = PacketStateDatabase()
        self.pm = RecipeManager()
        self.config = {}
        self._set_paths()

    def load_shmoad_ugly_toad(self, manifest_file):
        """Load the state from disk. DB and packet installers"""

        manifest = EdpmManifest.load(manifest_file)

        db_existed = self.load_db_if_exists()   # Try to load the DB

        self.pm.load_installers()               # load installers

        # Update DB "known installers"
        self.db.known_packet_names = self.pm.recipes_by_name.keys()

        return db_existed

    def load_db_if_exists(self):
        if self.db.exists():
            self.db.load()
            return True
        return False

    def merge_external_db(self, file_path):
        import_db = PacketStateDatabase()
        import_db.file_path = file_path
        import_db.load()
        merge_db(self.db, import_db)

    def ensure_db_exists(self):
        """Check if DB exist, create it or aborts everything

         All ensure_xxx functions check the problem, fix it or write message and call Click.Abort()
         """
        # save DB no db...
        if not self.db.exists():
            mprint("<green>creating database...</green>")
            self.db.save()

    def ensure_installer_known(self, packet_name):
        """Check if packet_name is of known packets or aborts everything

           All ensure_xxx functions check the problem, fix it or write message and call Click.Abort()
        """

        # Check if packet_name is all, missing or for known packet
        names = [str(n) for n in self.pm.recipes_by_name.keys()]
        is_valid_packet_name = str(packet_name) in names

        if not is_valid_packet_name:
            print("Packet with name '{}' is not found".format(packet_name))  # don't know what to do
            raise click.Abort()

    def save_shell_environ(self, file_path, shell):
        """Generates and saves shell environment to a file
        :param file_path: Path to file
        :param shell: 'bash' or 'csh'
        """

        with io.open(file_path, 'w', encoding='utf8') as outfile:    # Write file
            outfile.write(str(self.pm.gen_shell_env_text(self.db.get_active_installs(), shell=shell)))

    def save_default_bash_environ(self):
        """Generates and saves bash environment to a default file path"""
        self.save_shell_environ(self.config[ENV_SH_PATH], 'bash')

    def save_default_csh_environ(self):
        """Generates and saves csh/tcsh environment to a default file path"""
        self.save_shell_environ(self.config[ENV_CSH_PATH], 'csh')

    def _set_paths(self):
        """Sets edpm paths"""

        # edpm home path
        # call 'dirname' 3 times as we have <db path>/edpm/cli
        edpm_home_path = os.path.dirname(os.path.dirname(os.path.dirname(inspect.stack()[0][1])))
        self.config[EDPM_HOME_PATH] = edpm_home_path

        #
        # edpm data path. It is where db.json and environment files are located
        # We try to read it from EDPM_DATA_PATH environment variable and then use standard (XDG) location
        edpm_data_path = os.environ.get('EDPM_DATA_PATH', None)
        if not edpm_data_path:
            # Get the default (XDG or whatever) standard path to store user data
            edpm_data_path = os.getcwd()

            # In this case we care and create the directory
            if not os.path.isdir(edpm_data_path):
                from edpm.engine.commands import run
                run('mkdir -p "{}"'.format(edpm_data_path))

        self.config[EDPM_DATA_PATH] = edpm_data_path

        #
        # Database path
        self.db.file_path = os.path.join(edpm_data_path, "scipm.lock.json")
        self.config[DB_FILE_PATH] = self.db.file_path

        #
        # environment script paths
        self.config[ENV_SH_PATH] = os.path.join(edpm_data_path, "scipm_env.sh")
        self.config[ENV_CSH_PATH] = os.path.join(edpm_data_path, "scipm_env.csh")

    def configure_recipes(self):
        config = {}
        config.update(self.db.get_global_config())
        for recipe in self.pm.recipes_by_name.values():
            assert isinstance(recipe, Recipe)
            recipe.config.update(config)

    def update_python_env(self, process_chain=(), mode=''):
        """ Update python os.environ assuming we will install missing packets

           This func gets all 'active installation' of packages out of db to build environment
           if process_chain and mode are given, then depending on 'mode':
              'missing' : replace missing installations assuming we will install the package
              'all'     : replace all packets installation path assuming we will install all by our script
              ''        : just skip missing
        """

        if process_chain is None:
            process_chain = []
        from edpm.engine.db import IS_OWNED, IS_ACTIVE, INSTALL_PATH

        # Pretty header
        mprint("\n")
        mprint("<magenta>=========================================</magenta>")
        mprint("<green> SETTING ENVIRONMENT</green>")
        mprint("<magenta>=========================================</magenta>\n")

        # 1st, we need all data we have. All because installing packets can utilize the fa
        packet_data_by_name = {name: inst for name, inst in self.db.get_active_installs().items() if inst}

        # if we have process_chain
        for request in process_chain:
            packet_data = None
            if mode == 'missing' and (request.name not in packet_data_by_name.keys()):
                # There is no installation data for the packet, but we assume we will install it now!
                packet_data = {
                    INSTALL_PATH: request.recipe.install_path,
                    IS_ACTIVE: True,
                    IS_OWNED: True
                }
            elif mode == 'all':
                # We overwrite installation path for the packet
                packet_data = {
                    INSTALL_PATH: request.recipe.install_path,
                    IS_ACTIVE: True,
                    IS_OWNED: True
                }
            if packet_data:
                packet_data_by_name[request.name] = packet_data

        for name, data in packet_data_by_name.items():
            if name not in self.pm.env_generators.keys():  # Skip if we don't know environment generator for a packet
                continue
            # If we have a generator for this program and installation data
            mprint("<blue><b>Updating python environment for '{}'</b></blue>".format(name))
            generators = self.pm.env_generators[name]
            for step in generators(packet_data_by_name[name]):  # Go through 'env generators' look engine/env_gen.py
                step.update_python_env()  # Do environment update

    def req_get_known_os(self):
        names_set = set()
        for name in self.pm.recipes_by_name.keys():
            if 'required' in self.pm.os_deps_by_name[name]:
                for key in self.pm.os_deps_by_name[name]['required'].keys():
                    names_set.add(key)
        return names_set                # TODO change for

    def req_get_deps(self, os_name, packet_names=None):
        """ Returns
        # No packets provided, so all packets are selected

        :param os_name: Name of os like centos, ubuntu
        :param packet_names: If set, returns requirements for this packages and their deps. If None - all packages deps
        :return: list of required and optional packages
        """

        # Step 0 - What exactly packets are involved?
        if packet_names:
            names_with_deps = []    # Names of packets and their dependencies

            # get all dependencies
            for packet_name in packet_names:
                self.ensure_installer_known(packet_name)
                names_with_deps += self.pm.get_installation_chain_names(packet_name)  # func returns name + its_deps

            names_with_deps = list(set(names_with_deps))  # remove repeating names

        else:
            # No packets provided, so all packets are selected
            names_with_deps = self.pm.recipes_by_name.keys()

        # Step 1 - Form results
        required = []
        optional = []
        for name in names_with_deps:
            if os_name in self.pm.os_deps_by_name[name]['required'].keys():
                required.extend(self.pm.os_deps_by_name[name]['required'][os_name].replace(',', ' ').split())
            if os_name in self.pm.os_deps_by_name[name]['optional'].keys():
                optional.extend(self.pm.os_deps_by_name[name]['optional'][os_name].replace(',', ' ').split())

        # remove emtpy elements and repeating elements
        required = list(set([r for r in required if r]))
        optional = list(set([o for o in optional if o]))

        return required, optional


# Create a database class and @pass_db decorator so our commands could use it
pass_edpm_context = click.make_pass_decorator(EdpmApi, ensure=True)


def print_packets_info(db):
    """Prints known installations of packets and what packet is selected"""

    from edpm.engine.db import IS_OWNED, IS_ACTIVE, INSTALL_PATH
    assert (isinstance(db, PacketStateDatabase))

    installed_names = [name for name in db.packet_names]

    # Fancy print of installed packets
    if installed_names:
        mprint('\n<b><magenta>INSTALLED PACKETS:</magenta></b> (*-active):')
        for packet_name in installed_names:
            mprint(' <b><blue>{}</blue></b>:'.format(packet_name))
            installs = db.get_installs(packet_name)
            for i, installation in enumerate(installs):
                is_owned_str = '<green>(owned)</green>' if installation[IS_OWNED] else ''
                is_active = installation[IS_ACTIVE]
                is_active_str = '*' if is_active else ' '
                path_str = installation[INSTALL_PATH]
                id_str = "[{}]".format(i).rjust(4) if len(installs) > 1 else ""
                mprint("  {}{} {} {}".format(is_active_str, id_str, path_str, is_owned_str))

    not_installed_names = [name for name in db.known_packet_names if name not in installed_names]

    # Fancy print of installed packets
    if not_installed_names:
        mprint("\n<b><magenta>NOT INSTALLED:</magenta></b>\n(could be installed by 'edpm install')")
        for packet_name in not_installed_names:
            mprint(' <b><blue>{}</blue></b>'.format(packet_name))
