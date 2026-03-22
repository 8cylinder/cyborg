#!/usr/bin/env bin-python.bash

import os
import sys
import datetime
import subprocess
import configparser
import socket
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Optional
from platformdirs import user_config_dir


import click


def log(msg: str, msg_type: str = 'info') -> None:
    dt = datetime.datetime.now()
    timestamp = dt.strftime('%y-%m-%d %X')
    timestamp = click.style(timestamp, fg='blue')
    msg_types = {
        'info': ['INFO', 'green'],
        'warn': ['WARN', 'red'],
        'error': [' ERR', 'red'],
        'cmd': [' CMD', 'yellow'],
    }
    status = msg_types[msg_type][0]
    color = msg_types[msg_type][1]
    status = click.style(status, fg=color, bold=True)
    msg = click.style(msg, fg=color)
    out = f'{timestamp} {status}: {msg}'
    click.secho(out)


def log_error(msg: str) -> None:
    log(msg, msg_type='error')


def log_cmd(msg: str | list[str]) -> None:
    if isinstance(msg, list):
        msg = ' '.join(msg)
    log(msg, msg_type='cmd')


def warn(msg: str) -> None:
    log(msg, msg_type='warn')


def error(msg: str) -> None:
    log_error(msg)
    now = datetime.datetime.now().isoformat()
    alert_filename = f'CYBORG-ERROR--{now}--{"!" * 50}'
    alert_file = Path(Path.home(), alert_filename)
    alert_file.touch()
    alert_file.write_text(msg)
    sys.exit(1)


def run_prog(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [i for i in cmd if i]  # remove empty fields
    # Convert command list into a string since prune requires a shell
    # to work.  But `shell=True` requires a string for the command.
    cmd_str = ' '.join(cmd)
    log_cmd(cmd_str)
    result = subprocess.run(
        cmd_str,
        capture_output=True,
        shell=True,
        text=True,
    )
    result.stdout = result.stdout.strip()
    result.stderr = result.stderr.strip()
    return result


def columnize(data: str) -> str | bool:
    import math
    from itertools import zip_longest

    rows = [i for i in data.split('\n') if i]
    if not rows:
        return False

    spaces_between_columns = 2
    spaces = ' ' * spaces_between_columns
    max_word_len = max([len(i) for i in rows])
    display_width, _ = shutil.get_terminal_size()
    columns = int(display_width / (max_word_len + spaces_between_columns))

    backups = len(rows)
    chunk_len = math.ceil(backups / columns)
    chunks = []
    for i in range(columns):
        start = i * chunk_len
        end = (i + 1) * chunk_len
        chunks.append(rows[start:end])

    columnized = ''
    for row in zip_longest(*chunks, fillvalue=''):
        columnized += spaces.join([i.ljust(max_word_len) for i in row]) + '\n'
    return columnized.strip()


def get_config_dir() -> str:
    """
    Check for configuration directory in standard locations using platformdirs.
    Falls back to legacy ~/.cyborg if the standard location doesn't exist but the legacy one does.
    Finally checks the project root for a .cyborg directory.
    """
    app_name = "cyborg"
    config_dir = user_config_dir(app_name)
    if os.path.exists(config_dir):
        log(f"Using configuration directory: {config_dir}")
        return config_dir

    # Legacy check
    legacy_dir = os.path.expanduser("~/.cyborg")
    if os.path.exists(legacy_dir):
        log(f"Using configuration directory: {legacy_dir}")
        return legacy_dir

    # Project root check
    # Assumes structure: project_root/src/cyborg/cyborg.py
    project_root = Path(__file__).resolve().parent.parent.parent
    project_config_dir = project_root / ".cyborg"
    if project_config_dir.exists():
        log(f"Using configuration directory: {project_config_dir}")
        return str(project_config_dir)

    log(f"Configuration directory not found, defaulting to: {config_dir}")
    return config_dir


def _config_dirs() -> list[tuple[str, str]]:
    """Return list of (label, path) for all candidate config directories."""
    platform_dir = user_config_dir("cyborg")
    legacy_dir = os.path.expanduser("~/.cyborg")
    project_dir = str(Path(__file__).resolve().parent.parent.parent / ".cyborg")
    return [
        ("Platform (~/.config/cyborg)", platform_dir),
        ("Legacy (~/.cyborg)",          legacy_dir),
        ("Project root (.cyborg)",       project_dir),
    ]


def show_config_info() -> None:
    bundled = files('cyborg') / 'default_config'
    click.secho("Bundled default config:", bold=True)
    click.secho(f"  {bundled}\n")

    click.secho("Candidate config directories (checked in order):", bold=True)
    active: Optional[str] = None
    for label, path in _config_dirs():
        exists = os.path.exists(path)
        marker = click.style("exists", fg="green") if exists else click.style("not found", fg="red")
        click.secho(f"  {label}")
        click.secho(f"    {path}  [{marker}]")
        if exists and active is None:
            active = path

    print()
    if active:
        click.secho(f"Active config: {active}", fg="green", bold=True)
    else:
        click.secho("No config directory found. Run `cyborg config copy` to install the default config.", fg="yellow")


def copy_default_config() -> None:
    for _, path in _config_dirs():
        if os.path.exists(path):
            click.secho(f"Config directory already exists: {path}", fg="yellow")
            click.secho("Remove it first if you want to reinstall the default config.")
            return

    dest = Path(user_config_dir("cyborg"))
    dest.mkdir(parents=True, exist_ok=True)

    bundled = files('cyborg').joinpath('default_config')
    for item in bundled.iterdir():
        dest_file = dest / item.name
        dest_file.write_bytes(item.read_bytes())
        click.secho(f"  Copied: {dest_file}")

    click.secho(f"\nDefault config installed to: {dest}", fg="green", bold=True)
    click.secho("Edit config.ini to set your backup destinations.")


class Borg:
    settings_dir: str
    settings_file: str
    installed_apps: str
    timestamp_file: str
    dry_run: str
    destination: str
    passphrase: str
    exclude_list: str
    source: list[str]
    now: datetime.datetime

    def __init__(self, dry_run: bool = True, backup_name: str = 'default') -> None:
        log(f'Using backup named: {backup_name}', msg_type='info')

        result = run_prog(['pidof', '-sx', 'borg'])
        if not result.returncode:
            error('Borg already running, wait for it to finish.')

        self.settings_dir = get_config_dir()
        self.settings_file = os.path.join(self.settings_dir, 'config.ini')
        self.installed_apps = os.path.join(self.settings_dir, 'installed-apps.txt')
        self.timestamp_file = os.path.join(self.settings_dir, 'LAST-RUN')

        self.dry_run = '--dry-run'
        if not dry_run:
            self.dry_run = ''

        # load settings file
        self.load_settings(backup_name)

        self.check_file(self.exclude_list)

        self.now = datetime.datetime.now()

    def check_file(self, filename: str) -> None:
        if filename.startswith('ssh://'):
            return

        if not os.path.exists(filename):
            error(f'file does not exist: {filename}.')

    def load_settings(self, backup_name: str) -> None:
        config = configparser.ConfigParser(inline_comment_prefixes=('#',))
        try:
            config.read(self.settings_file)
        except configparser.ParsingError as e:
            error(' '.join(str(e).split()))

        try:
            settings = config[backup_name]
        except KeyError:
            error(f'{self.settings_file} does not exist or does not contain a "[{backup_name}]" section.')
        try:
            destination = settings['destination'].strip('"\'')
        except KeyError as e:
            error(f'Key not set in {self.settings_file}: {e}')

        self.destination = os.path.expanduser(destination)

        try:
            phrase = settings['passphrase']
        except KeyError:
            phrase = ''
        self.passphrase = f'BORG_PASSPHRASE={phrase}' if phrase else ''

        try:
            exclude = settings['exclude']
            exclude = os.path.expanduser(exclude)
            if not os.path.isabs(exclude):
                exclude = os.path.join(self.settings_dir, exclude)
            self.exclude_list = exclude
        except KeyError as e:
            error(f'Key not set in {self.settings_file}: {e}')

        try:
            self.source = [s.strip() for s in settings['source'].split(',')]
        except KeyError as e:
            error(f'Key not set in {self.settings_file}: {e}')

    def status(self) -> None:
        # show a list of all backup sets
        cmd = [self.passphrase, 'borg', 'list', '--short', self.destination]
        result = run_prog(cmd)
        output = result.stdout
        backup_list = columnize(output)
        last_backup = 'BACKUP-NAME'
        if backup_list:
            print(backup_list)
            last_backup = output.split('\n')[-1].split()[0]
        else:
            print()
            click.secho(' NO BACKUPS FOUND ', bg='red', fg='white')

        print()
        commands = [
            ['# show more info:', 'green'],
            [f'{self.passphrase} borg list {self.destination}', 'yellow'],
            ['# list all files in last backup:', 'green'],
            [f'{self.passphrase} borg list {self.destination}::{last_backup}', 'yellow'],
            ['# show details about backup repo:', 'green'],
            [f'{self.passphrase} borg info -v {self.destination}', 'yellow'],
            ['# show details about backup repo and the last backup:', 'green'],
            [f'{self.passphrase} borg info -v {self.destination}::{last_backup}', 'yellow'],
        ]
        [click.secho(i[0].lstrip(), fg=i[1]) for i in commands]

    def save_last_run(self) -> None:
        timestamp = self.now.isoformat() + '\n'
        with open(self.timestamp_file, 'w') as f:
            f.write(timestamp)

    def run(self) -> None:
        # generate list of installed applications
        installed_generator = '/home/sm/bin/backup-apps-list'
        result = run_prog([installed_generator])
        if result.returncode:
            warn(f'Installed list generator not found: {installed_generator}')
        else:
            with open(self.installed_apps, 'w') as f:
                f.write(result.stdout)
                log(f'Wrote {self.installed_apps}')

        # backup
        timestamp = self.now.strftime('%Y-%m-%d__%H-%M')
        archive_name = f'{self.destination}::{socket.gethostname()}__{timestamp}'
        log(f'Starting backup to {archive_name}')

        cmd = [self.passphrase, 'borg', 'create', self.dry_run, '-v',
               f'--exclude-from={self.exclude_list}',
               '--one-file-system',
               '--compression=zlib,6',
               '--exclude-caches',
               archive_name,
               *self.source,
        ]
        result = run_prog(cmd)
        if result.returncode == 1:
            warn(result.stderr)
        elif result.returncode == 2:
            errmsg = result.stderr.split('\n')[-1]
            error(errmsg)
        log('Borg backup successful')
        self.prune()
        self.save_last_run()

    def prune(self) -> None:
        cmd = [
            self.passphrase, 'borg', 'prune', self.dry_run, '--debug', self.destination,
            f'--prefix="{socket.gethostname()}__"',
            '--keep-within=2d', '--keep-daily=14', '--keep-weekly=4',
            '--keep-monthly=6', '--keep-yearly=1'
        ]
        result = run_prog(cmd)
        if result.returncode:
            errmsg = result.stderr.split('\n')[-1]
            error(errmsg)
        log('Borg prune successful')

    def extras(self) -> None:
        """Print out extra commands that can be copied and pasted to the command line"""
        last_backup = 'BACKUP_NAME'
        commands = [
            ['', ''],
            ['# BORG', 'green'],
            ['# ----', 'green'],
            ['# show more info:', 'green'],
            [f'{self.passphrase} borg list {self.destination}', 'yellow'],
            ['# list all files in last backup:', 'green'],
            [f'{self.passphrase} borg list {self.destination}::{last_backup}', 'yellow'],
            ['# show details about backup repo:', 'green'],
            [f'{self.passphrase} borg info -v {self.destination}', 'yellow'],
            ['# show details about backup repo and the last backup:', 'green'],
            [f'{self.passphrase} borg info -v {self.destination}::{last_backup}', 'yellow'],

            [f'{self.passphrase} borg init --encryption=none {self.destination}', 'yellow'],
            ['# CAUTION, restores to current dir only', 'green'],
            [f'{self.passphrase} borg restore --dry-run {self.destination}', 'yellow'],
            [f'{self.passphrase} borg break-lock {self.destination}', 'yellow'],
            [f'{self.passphrase} borg list {self.destination}', 'yellow'],
            ['# note: takes a long time', 'green'],
            [f'{self.passphrase} borg check {self.destination}', 'yellow'],
            [f'{self.passphrase} borg mount {self.destination} MOUNTPOINT', 'yellow'],
            [f'{self.passphrase} borg umount MOUNTPOINT', 'yellow'],
            [f'{self.passphrase} borg prune {self.dry_run} -v {self.destination} --prefix="{socket.gethostname()}__" --keep-within=10d --keep-weekly=4 --keep-monthly=6 --keep-yearly=1', 'yellow'],
        ]
        [click.secho(i[0].lstrip(), fg=i[1]) for i in commands]
        print()
        click.secho('https://borgbackup.readthedocs.io', fg='blue', underline=True)
        click.secho('https://github.com/borgbackup/borg', fg='blue', underline=True)
