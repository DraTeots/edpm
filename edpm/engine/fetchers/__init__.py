import os
from abc import ABC, abstractmethod
from typing import Dict, Any
from edpm.engine.commands import run, workdir


# -------------------------------------
# F E T C H E R   I N T E R F A C E
# -------------------------------------

class IFetcher(ABC):
    """ Interface for "fetchers" that handle retrieving source code, etc. """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def preconfigure(self):
        """
        This function can be used to add or refine config entries
        needed before the actual fetch step. Default: do nothing.
        """
        pass

    @abstractmethod
    def fetch(self):
        """
        Actually perform the fetch/cloning/copying step
        (e.g. git clone, tarball download+extract, etc.).
        """
        pass


class GitFetcher(IFetcher):
    """
    A fetcher that uses `git clone`.
    """

    def preconfigure(self):
        """
        EnvSet up config['clone_command'] if not already provided.
        For example, set shallow clone if branch != (master|main).
        """
        # If user doesn't specify 'git_clone_depth', pick default
        if "git_clone_depth" not in self.config:
            is_main_branch = self.config.get("branch", "") not in ["master", "main"]
            self.config["git_clone_depth"] = "--depth 1" if is_main_branch else ""

        version = self.config.get("version", "")
        branch = self.config.get("branch", "")
        if version:
            # e.g. treat version as git branch or tag
            if branch:
                print(f"'version'='{version}' is explicitly set and overrides 'branch'='{branch}' (this might be desired)")
            self.config["branch"] = version

        # For convenience, build a 'clone_command' string
        self.config["clone_command"] = (
            "git clone {git_clone_depth} -b {branch} {url} {source_path}"
            .format(**self.config)
        )

    def fetch(self):
        repo_url = self.config.get("url", "")
        source_path = self.config.get("source_path", "")
        clone_command = self.config.get("clone_command", "")

        if not repo_url:
            raise ValueError(
                "[GitFetcher] 'url' is missing in config. Current config: {}".format(self.config)
            )

        # If already cloned or source_path is not empty, skip
        if os.path.exists(source_path) and os.path.isdir(source_path) and os.listdir(source_path):
            # The directory exists and is not empty. Do nothing.
            return

        # Ensure the parent directories exist
        run('mkdir -p "{}"'.format(source_path))

        # Execute the clone
        run(clone_command)

    def use_common_dirs_scheme(self):
        """Function sets common directory scheme."""
        if 'app_path' in self.config:
            # The directory, where binary is installed
            if not "install_path" in self.config:
                self.config["install_path"] = "{app_path}/{app_name}-{branch}".format(**self.config)


class TarballFetcher(IFetcher):
    """
    A fetcher that downloads a tarball from a URL, extracts it,
    and places contents in `source_path`.
    """

    def preconfigure(self):
        # Optionally refine or default something, e.g. local temp name
        if "tar_temp_name" not in self.config:
            self.config["tar_temp_name"] = "/tmp/temp.tar.gz"

    def fetch(self):
        file_url = self.config.get("file_url", "")
        app_path = self.config.get("app_path", "")
        source_path = os.path.join(app_path, "src")  # or use source_path from config

        if not file_url:
            raise ValueError("[TarballFetcher] 'file_url' not specified in config.")

        # Create the source_path
        run('mkdir -p "{}"'.format(source_path))

        download_cmd = f"wget {file_url} -O {self.config['tar_temp_name']}"
        run(download_cmd)

        extract_cmd = f"tar zxvf {self.config['tar_temp_name']} -C {source_path} --strip-components=1"
        run(extract_cmd)


class FileSystemFetcher(IFetcher):
    """
    A fetcher that simply uses a local directory as 'source_path'.
    Optionally can copy it, or do nothing if the user wants to build in-place.
    """

    def fetch(self):
        # The user might store it in config["path"]
        # or config["source_path"]. Decide which to rely on:
        path = self.config.get("path", "")
        source_path = self.config.get("source_path", "")

        if not path:
            raise ValueError("[FileSystemFetcher] No 'path' provided in config.")
        if not os.path.isdir(path):
            raise ValueError(f"[FileSystemFetcher] Provided 'path' is not a directory: {path}")

        # A typical usage: just copy or do nothing. We'll do a naive copy example:
        # If user actually wants an in-place usage, they can skip copying.
        # For demonstration, let's copy to source_path if different:
        if source_path and source_path != path:
            run(f'mkdir -p "{source_path}"')
            # A naive copy with rsync (example):
            copy_cmd = f'rsync -a "{path}/" "{source_path}/"'
            run(copy_cmd)
        else:
            # If user sets them the same, we do nothing.
            pass


def make_fetcher(config: Dict[str, Any]) -> IFetcher:
    """
    Factory that picks the fetcher based on config['fetch'] or tries to autodetect
    from 'fetch' value if it is a URL or local path.
    """
    fetch_val = config.get("fetch", "")
    if not fetch_val:
        # No fetch step
        return None

    # If user explicitly says "git", "tarball", or "filesystem"
    if fetch_val in ("git", "tarball", "filesystem"):
        if fetch_val == "git":
            return GitFetcher(config)
        elif fetch_val == "tarball":
            return TarballFetcher(config)
        else:
            return FileSystemFetcher(config)

    # Otherwise, do an autodetect:
    if fetch_val.endswith(".git"):
        return GitFetcher(config)
    elif fetch_val.endswith(".tar.gz"):
        return TarballFetcher(config)
    else:
        # assume local filesystem
        return FileSystemFetcher(config)
