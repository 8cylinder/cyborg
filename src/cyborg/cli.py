import argparse
import sys
import textwrap
from .cyborg import Borg, show_config_info, copy_default_config


def init(cli_args: argparse.Namespace) -> None:
    if cli_args.subparser_name == 'config':
        action = getattr(cli_args, 'action', None)
        if action == 'copy':
            copy_default_config()
        else:
            show_config_info()
        return

    if not cli_args.name:
        sys.stderr.write("error: a profile name is required, eg: cyborg nas run\n")
        sys.exit(1)

    try:
        borg = Borg(dry_run=cli_args.dry_run, backup_name=cli_args.name)
    except AttributeError:
        borg = Borg(backup_name=cli_args.name)

    if cli_args.subparser_name == 'run':
        borg.run()
    elif cli_args.subparser_name == 'prune':
        borg.prune()
    else:
        getattr(borg, cli_args.subparser_name)()


def main() -> None:
    help_msg = textwrap.dedent('''
    🤖 Backup using Borg

    https://borgbackup.readthedocs.io
    https://github.com/borgbackup

    Usage: cyborg NAME COMMAND [OPTIONS]
      eg:  cyborg nas run
           cyborg borgbase extras
           cyborg config
           cyborg config copy

    Config is loaded from (in order): ~/.config/cyborg/, ~/.cyborg/,
    or a .cyborg/ directory in the project root.

    Initial setup:
    --------------
    Run `cyborg config copy` to install the default config, then edit
    it. Run `cyborg NAME extras` to see the borg init command.

    INI file sections:
    ------------------
    Each [section] is a named profile with destination, source, and
    exclude fields. Optionally: passphrase.
    ''')

    parser = argparse.ArgumentParser(
        description=help_msg,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('name', nargs='?', default=None,
                        help='The name of a backup profile (not needed for config)')
    subparsers = parser.add_subparsers(dest='subparser_name')

    # run
    run = subparsers.add_parser('run', help='Run the backup')
    run.add_argument('-d', '--dry-run', default=False, action='store_true')

    # prune
    prune = subparsers.add_parser('prune', help='Prune the repo')
    prune.add_argument('-d', '--dry-run', action='store_true')

    # status
    subparsers.add_parser('status', help='Check the backup')

    # extras
    subparsers.add_parser(
        'extras',
        help='Output extra commands to be copied and pasted in the terminal')

    # config
    config = subparsers.add_parser(
        'config',
        help='Show config info, or copy the default config with "config copy"')
    config.add_argument('action', nargs='?', choices=['copy'],
                        help='copy: install the default config to ~/.config/cyborg/')

    args = parser.parse_args()
    if not args.subparser_name:
        parser.print_help(sys.stderr)
        sys.exit(0)
    init(args)


if __name__ == '__main__':
    main()
