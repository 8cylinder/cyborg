import click
from importlib.metadata import version
from .cyborg import Borg, show_config_info, copy_default_config


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version('cyborg'), '-V', '--version')
def main() -> None:
    """Backup using Borg

    \b
    https://borgbackup.readthedocs.io
    https://github.com/borgbackup

    Config is loaded from (in order): ~/.config/cyborg/, ~/.cyborg/,
    or a .cyborg/ directory in the project root.

    \b
    Initial setup:
    Run `cyborg config copy` to install the default config, then edit
    it. Run `cyborg extras NAME` to see the borg init command.

    \b
    INI file sections:
    Each [section] is a named profile with destination, source, and
    exclude fields. Optionally: passphrase.
    """


@main.command()
@click.argument('name')
@click.option('-d', '--dry-run', is_flag=True, default=False)
def run(name: str, dry_run: bool) -> None:
    """Run the backup."""
    borg = Borg(dry_run=dry_run, backup_name=name)
    borg.run()


@main.command()
@click.argument('name')
@click.option('-d', '--dry-run', is_flag=True, default=False)
def prune(name: str, dry_run: bool) -> None:
    """Prune the repo."""
    borg = Borg(dry_run=dry_run, backup_name=name)
    borg.prune()


@main.command()
@click.argument('name')
def status(name: str) -> None:
    """Check the backup."""
    borg = Borg(backup_name=name)
    borg.status()


@main.command()
@click.argument('name')
def extras(name: str) -> None:
    """Output extra commands to copy and paste in the terminal."""
    borg = Borg(backup_name=name)
    borg.extras()


@main.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show config info, or copy the default config with 'config copy'."""
    if ctx.invoked_subcommand is None:
        show_config_info()


@config.command('copy')
def config_copy() -> None:
    """Install the default config to ~/.config/cyborg/."""
    copy_default_config()

