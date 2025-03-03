# edpm/engine/generators/environment_generator.py

import os

class EnvironmentGenerator:
    def __init__(self, plan, lock, recipe_manager):
        self.plan = plan
        self.lock = lock
        self.recipe_manager = recipe_manager

    def build_env_text(self, shell="bash") -> str:
        """
        Returns *only* the EDPM environment content as a string.
        """
        lines = []
        if shell == "bash":
            lines.append("#!/usr/bin/env bash\n")
        elif shell == "csh":
            lines.append("#!/usr/bin/env csh\n")
        else:
            # fallback
            lines.append("#!/usr/bin/env bash\n")

        lines.append("# EDPM environment script\n\n")

        # 1) Global environment
        global_env_actions = self.plan.get_global_env_actions()
        for act in global_env_actions:
            if shell == "bash":
                lines.append(act.gen_bash() + "\n")
            else:
                lines.append(act.gen_csh() + "\n")

        # 2) Per dependency
        package_names = self.lock.get_installed_packages()
        for package_name in sorted(package_names):
            dep_data = self.lock.get_installed_package(package_name)
            env_actions = []

            # Get environment from recipe's gen_env
            recipe_cls = self.recipe_manager.recipes_by_name.get(package_name)
            if recipe_cls:
                recipe_env_actions = list(recipe_cls.gen_env(dep_data))
                env_actions.extend(recipe_env_actions)

            install_path = dep_data.get("install_path", "")
            if not install_path or not os.path.isdir(install_path):
                continue
            dep_obj = self.plan.find_package(package_name)
            if not dep_obj:
                continue

            # Get environment from plan's environment block
            placeholders = {
                "install_path": install_path,
                "name": package_name,
                # Add other placeholders as needed
            }
            plan_env_actions = dep_obj.env_block().parse(placeholders)
            env_actions.extend(plan_env_actions)


            lines.append(f"\n# ----- ENV for {package_name} -----\n")
            placeholders = {"install_path": install_path}
            env_actions.extend(dep_obj.env_block().parse(placeholders))
            for act in env_actions:
                if shell == "bash":
                    lines.append(act.gen_bash() + "\n")
                else:
                    lines.append(act.gen_csh() + "\n")

        return "".join(lines)

    def save_environment_with_infile(self, shell: str, in_file: str, out_file: str):
        """
        1. Build the EDPM environment content
        2. If in_file is None => write EDPM content directly to out_file
        3. Else read in_file, look for marker "{{{EDPM-GENERATOR-CONTENT}}}", and place EDPM content there (or append).
        4. Write the merged result to out_file
        """
        edpm_content = self.build_env_text(shell)
        if in_file is None:
            # Just write EDPM content
            self._write_text(out_file, edpm_content)
            return

        # We do merging
        with open(in_file, "r", encoding="utf-8") as f:
            original_lines = f.readlines()

        marker = "{{{EDPM-GENERATOR-CONTENT}}}"
        inserted = False
        new_lines = []
        for line in original_lines:
            if marker in line.strip():
                new_lines.append(edpm_content)
                inserted = True
                # we can keep or discard the marker line. Let's discard it:
                # continue
                # or to keep the marker line, do new_lines.append(line)
            else:
                new_lines.append(line)

        if not inserted:
            # If marker wasn't found, append at the end
            new_lines.append("\n# -- EDPM Content appended:\n")
            new_lines.append(edpm_content)

        merged_text = "".join(new_lines)
        self._write_text(out_file, merged_text)

    def _write_text(self, filename, text):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        # could do a click.echo or logging here
