# cli/init.py

import os
import click
import glob
import importlib.util

from edpm.engine.api import EdpmApi
from edpm.engine.output import markup_print as mprint


def get_templates_dir():
    """Get the path to the templates directory."""
    # Find the edpm package directory
    try:
        spec = importlib.util.find_spec("edpm")
        if spec is None:
            return None
        edpm_package_dir = os.path.dirname(spec.origin)
        templates_dir = os.path.join(edpm_package_dir, "templates")
        return templates_dir if os.path.isdir(templates_dir) else None
    except Exception:
        return None


def list_available_templates():
    """List all available template files."""
    templates_dir = get_templates_dir()
    if not templates_dir:
        return []

    pattern = os.path.join(templates_dir, "*-plan.edpm.yaml")
    template_files = glob.glob(pattern)

    # Extract template names (remove path, suffix, and "-plan" part)
    template_names = []
    for file_path in template_files:
        filename = os.path.basename(file_path)
        # Remove .edpm.yaml suffix and -plan suffix
        name = filename.replace("-plan.edpm.yaml", "")
        template_names.append(name)

    return sorted(template_names)


def load_template_content(template_name):
    """Load template content from the templates directory."""
    templates_dir = get_templates_dir()
    if not templates_dir:
        raise FileNotFoundError("Templates directory not found")

    template_filename = f"{template_name}-plan.edpm.yaml"
    template_path = os.path.join(templates_dir, template_filename)

    if not os.path.isfile(template_path):
        available = list_available_templates()
        if available:
            available_str = ", ".join(available)
            raise FileNotFoundError(
                f"Template '{template_name}' not found. Available templates: {available_str}"
            )
        else:
            raise FileNotFoundError(
                f"Template '{template_name}' not found and no templates directory found"
            )

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@click.command("init")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing plan.edpm.yaml if it already exists.")
@click.option("-t", "--template", default="default",
              help="Template to use for initialization (default: default). Use --list-templates to see available options.")
@click.option("--list-templates", is_flag=True, default=False,
              help="List available templates and exit.")
@click.pass_context
def init_command(ctx, force, template, list_templates):
    """
    Creates an EDPM plan template (plan.edpm.yaml) in the current directory.

    You can specify a template using -t/--template option. Templates are loaded
    from the edpm/templates/ directory and should be named <template>-plan.edpm.yaml.

    Examples:
        edpm init                    # Uses default template
        edpm init -t eic             # Uses eic-plan.edpm.yaml template
        edpm init -t tdis            # Uses tdis-plan.edpm.yaml template
        edpm init --list-templates   # Shows available templates
    """

    # Handle --list-templates option
    if list_templates:
        available = list_available_templates()
        if available:
            mprint("<green>Available templates:</green>")
            for tmpl in available:
                mprint("  <blue>{}</blue>", tmpl)
        else:
            mprint("<yellow>No templates found in templates directory.</yellow>")
        return

    edpm_api = ctx.obj
    assert isinstance(edpm_api, EdpmApi)
    target_file = edpm_api.plan_file

    # Check if file already exists
    if os.path.isfile(target_file) and not force:
        mprint("<red>File '{}' already exists.</red> Use --force to overwrite.", target_file)
        return

    # Load template content
    try:
        template_content = load_template_content(template)
        mprint("<green>Using template:</green> <blue>{}</blue>", template)
    except FileNotFoundError as e:
        mprint("<red>Error:</red> {}", str(e))
        return
    except Exception as e:
        mprint("<red>Error loading template:</red> {}", str(e))
        return

    # Write the template content to the target file
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(template_content)

        mprint("<green>Created EDPM plan:</green> {}", target_file)
        mprint(
            "You can now edit '{}' to define your dependencies or global config.\n"
            "Then run 'edpm install' or 'edpm config' to proceed.",
            target_file
        )

        if template != "default":
            mprint("<blue>Note:</blue> Used template '<blue>{}</blue>'. You may need to customize "
                   "the configuration for your specific environment.", template)

    except Exception as e:
        mprint("<red>Error writing plan file:</red> {}", str(e))
        return