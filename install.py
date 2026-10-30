#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Halloween theme contributors
# Provided without warranty; see LICENSE and DISCLAIMER.md.
"""Install Halloween into a Zabbix 8.0 frontend; no database or service changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

PACKAGE = Path(__file__).resolve().parent
VERSION = '1.0'
INSTALLER_VERSION = '1.2.1'
APP = Path('include/classes/core/APP.php')
ASSETS = [Path('assets/styles/halloween-theme.css'),
          Path('assets/styles/halloween/night.svg'), Path('assets/styles/halloween/witch.svg'),
          Path('assets/styles/halloween/pumpkin.svg')]
ENTRY = "\t\t\t'halloween-theme' => _('Halloween')"
THEMES_BLOCK = """
\t// BEGIN HALLOWEEN THEMES
\tpublic static function getThemes() {
\t\treturn array_merge(parent::getThemes(), [
""" + ENTRY + """
\t\t]);
\t}
\t// END HALLOWEEN THEMES
"""
COLOR_BLOCK = """
\t// BEGIN HALLOWEEN COLOR SCHEME
\tpublic static function getColorScheme(string $theme): string {
\t\treturn $theme === 'halloween-theme'
\t\t\t? ZBX_COLOR_SCHEME_DARK
\t\t\t: parent::getColorScheme($theme);
\t}
\t// END HALLOWEEN COLOR SCHEME
"""

def digest(data):
    return hashlib.sha256(data).hexdigest()

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix='.halloween-', dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        if path.exists():
            st = path.stat()
            shutil.copystat(path, temp)
            # copystat also copies mtime. Refresh it so PHP OPcache can detect
            # changed registration code on both installation and uninstall.
            os.utime(temp, None)
            if hasattr(os, 'chown') and os.geteuid() == 0:
                os.chown(temp, st.st_uid, st.st_gid)
        else:
            temp.chmod(0o644)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def prepare_app(original):
    text = original.decode('utf-8')
    match = re.search(r'(class\s+APP\s+extends\s+ZBase\s*\{)([\s\S]*)(\})\s*$', text)
    if not match:
        raise ValueError('APP.php has an unsupported class structure; no files changed.')
    body = match[2]
    if not body.strip():
        updated = '\n' + THEMES_BLOCK + COLOR_BLOCK + '\n'
    else:
        # Accept only a literal theme-list override.
        # Other methods or executable expressions need a manual merge.
        comment = r'(?:\s*//[^\n]*\n)*\s*'
        method = re.fullmatch(
            comment + r'public\s+static\s+function\s+getThemes\(\)\s*\{\s*'
            r'return\s+array_merge\(parent::getThemes\(\),\s*\[(?P<entries>[\s\S]*?)\]\);\s*\}'
            + comment, body)
        entry = r"'[a-zA-Z0-9_-]+'\s*=>\s*_\('[a-zA-Z0-9 _-]+'\)"
        if not method or not re.fullmatch(r'\s*(?:' + entry + r'\s*,\s*)*(?:' + entry + r'\s*,?)?\s*', method['entries']):
            raise ValueError('APP.php has custom methods beyond a simple theme list. Follow the manual merge instructions; no files changed.')
        if "'halloween-theme'" in method['entries']:
            raise ValueError('Halloween is already registered in APP.php; no files changed.')
        offset = method.start('entries')
        updated = body[:offset] + '\n' + ENTRY + ',' + body[offset:] + COLOR_BLOCK
    return (text[:match.start(2)] + updated + text[match.end(2):]).encode('utf-8')

def php_lint(data):
    php = shutil.which('php')
    if not php:
        print('PHP CLI not found; using the restricted registration templates. Run php -l on APP.php after installation.')
        return
    with tempfile.NamedTemporaryFile(suffix='.php') as temp:
        temp.write(data)
        temp.flush()
        result = subprocess.run([php, '-l', temp.name], capture_output=True, text=True)
        if result.returncode:
            raise ValueError('PHP syntax validation failed: ' + result.stdout + result.stderr)

def frontend_version(root):
    version_file = root / 'include/defines.inc.php'
    if not (root / APP).is_file() or not (root / 'assets/styles/dark-theme.css').is_file() or not version_file.is_file():
        raise ValueError('Not a recognized Zabbix frontend directory: ' + str(root))
    version = re.search(r"define\('ZABBIX_VERSION',\s*'([^']+)'", version_file.read_text())
    if not version or not version[1].startswith('8.0.'):
        raise ValueError('This build targets Zabbix 8.0.x. Rebuild against your exact source version before installing elsewhere.')
    return version[1]

def load_record(root, backup):
    state_path = backup / 'install.json'
    if not state_path.is_file():
        raise ValueError('No installation record found in ' + str(backup))
    saved_state = state_path.read_bytes()
    state = json.loads(saved_state)
    if state.get('frontend') != str(root):
        raise ValueError('Backup belongs to a different frontend.')
    expected_paths = {str(x) for x in [APP] + ASSETS}
    if not isinstance(state.get('installed'), dict) or set(state['installed']) != expected_paths:
        raise ValueError('Unexpected file list in installation record.')
    original = (backup / 'APP.php.original').read_bytes()
    if digest(original) != state.get('original_sha256'):
        raise ValueError('Original APP.php backup failed checksum verification.')
    return state, saved_state, original

def print_notice(uninstall=False):
    print('WARNING: NOT FOR PRODUCTION. Experimental theme for isolated labs and demonstrations only.')
    print('AI-GENERATED project customizations: OpenAI Codex using GPT-6 Astra (gpt-6-astra).')
    print('AI output may contain defects or inaccurate instructions; passing tests is not a security audit.')
    print('NOTICE: Third-party frontend customization. Installation/repair edits include/classes/core/APP.php.')
    print('Built for Zabbix 8.0.0rc3 development. Do not deploy on production or critical monitoring systems.')
    print('Review the source and test in a disposable lab. PHP errors can disrupt the web UI and API; CSS can affect readability.')
    print('Frontend upgrades can remove registration. No database, server binary or service changes are made.')
    if uninstall:
        print('BEFORE REMOVAL: Select another theme in affected user profiles and the frontend default.')
        print('This file-only installer cannot check or change those saved theme selections.')

def uninstall_installation(root, backup, check=False):
    state, saved_state, original = load_record(root, backup)
    current_app = (root / APP).read_bytes()
    restore_app = digest(current_app) == state['installed'][str(APP)]
    if not restore_app:
        try:
            # A replaced, supported APP.php with no Halloween entry needs no
            # restoration. Validate the structure but discard the patch.
            prepare_app(current_app)
        except ValueError as error:
            raise ValueError('APP.php changed and cannot be safely unregistered automatically. '
                             'Preserve it and use the manual removal instructions; no files changed. '
                             + str(error)) from error
    previous = {}
    metadata = {}
    for rel in ASSETS:
        path = root / rel
        if not path.exists():
            continue
        data = path.read_bytes()
        if digest(data) != state['installed'][str(rel)]:
            raise ValueError('Theme asset has local edits; refusing to delete: ' + str(path))
        previous[rel] = data
        metadata[rel] = path.stat()
    if restore_app:
        php_lint(original)
    print('Frontend:', root, '\nBackup:', backup)
    print('Restore the verified pre-theme APP.php.' if restore_app
          else 'Halloween is already absent from the supported current APP.php; leave that file unchanged.')
    print('Remove ' + str(len(previous)) + ' unchanged Halloween assets; retain all backups.')
    if check:
        print('Uninstall check passed. No files changed.')
        return
    removal_backup = backup / 'uninstalls' / str(time.time_ns())
    removal_backup.mkdir(parents=True)
    removal_backup.chmod(0o700)
    atomic_write(removal_backup / 'install.json', saved_state)
    atomic_write(removal_backup / 'before' / APP, current_app)
    for rel, data in previous.items():
        atomic_write(removal_backup / 'before' / rel, data)
    removed = []
    app_touched = False
    try:
        if restore_app:
            app_touched = True
            atomic_write(root / APP, original)
        for rel in previous:
            (root / rel).unlink()
            removed.append(rel)
        (backup / 'install.json').rename(backup / 'uninstalled.json')
    except Exception:
        # Restore assets before re-publishing the registration on failure.
        for rel in removed:
            path = root / rel
            atomic_write(path, previous[rel])
            path.chmod(metadata[rel].st_mode)
            if hasattr(os, 'chown') and os.geteuid() == 0:
                os.chown(path, metadata[rel].st_uid, metadata[rel].st_gid)
        if app_touched:
            atomic_write(root / APP, current_app)
        raise
    try:
        (root / 'assets/styles/halloween').rmdir()
    except OSError:
        pass
    print('Halloween removed. Other theme assets are unchanged; backups retained at ' + str(backup))
    print('If PHP OPcache timestamp validation is disabled, reload the PHP runtime to refresh the theme list.')

def repair_installation(root, backup, check=False):
    """Reapply registration to current PHP; never roll the frontend back."""
    version = frontend_version(root)
    state, saved_state, old_original = load_record(root, backup)
    current_app = (root / APP).read_bytes()
    registration_changed = digest(current_app) != state['installed'][str(APP)]
    if registration_changed:
        # Accept only a clean class or the supported simple theme list. Unknown
        # customizations and partial Halloween edits require a manual merge.
        patched = prepare_app(current_app)
        new_original = current_app
    else:
        patched = current_app
        new_original = old_original
    php_lint(patched)
    payloads = {rel: (PACKAGE / 'theme' / rel).read_bytes() for rel in ASSETS}
    previous = {APP: current_app}
    for rel, data in payloads.items():
        path = root / rel
        previous[rel] = path.read_bytes() if path.exists() else None
        if previous[rel] is not None and digest(previous[rel]) not in (state['installed'][str(rel)], digest(data)):
            raise ValueError('Theme asset has local edits; refusing to overwrite: ' + str(path))
    changed = {rel: data for rel, data in payloads.items() if previous[rel] != data}
    print('Frontend:', root, '\nVersion:', version, '\nBackup:', backup)
    if not registration_changed and not changed:
        print('Halloween registration and assets are intact. No files changed.')
        print('If it is missing from the dropdown, check the served frontend path and refresh its PHP OPcache.')
        return
    print('Repair Halloween registration in the current APP.php; restore/update ' + str(len(changed)) + ' theme assets.')
    print('Archive the previous record and preserve the current frontend as the uninstall baseline.')
    if check:
        print('Repair check passed. No files changed.')
        return
    repair_backup = backup / 'repairs' / str(time.time_ns())
    repair_backup.mkdir(parents=True)
    repair_backup.chmod(0o700)
    atomic_write(repair_backup / 'install.json', saved_state)
    atomic_write(repair_backup / 'APP.php.original', old_original)
    for rel, data in previous.items():
        if data is not None:
            atomic_write(repair_backup / 'before' / rel, data)
    atomic_write(repair_backup / 'missing.json', json.dumps([str(rel) for rel, data in previous.items() if data is None]).encode())
    new_state = dict(state)
    new_state.update(version=version, theme_version=VERSION, installer_version=INSTALLER_VERSION,
                     original_sha256=digest(new_original),
                     installed={str(APP): digest(patched), **{str(rel): digest(data) for rel, data in payloads.items()}})
    touched = []
    try:
        for rel, data in changed.items():
            touched.append(rel)
            atomic_write(root / rel, data)
        if registration_changed:
            touched.append(APP)
            atomic_write(root / APP, patched)
        atomic_write(backup / 'APP.php.original', new_original)
        atomic_write(backup / 'install.json', json.dumps(new_state, indent=2).encode('utf-8'))
    except Exception:
        for rel in reversed(touched):
            if previous[rel] is None:
                (root / rel).unlink(missing_ok=True)
            else:
                atomic_write(root / rel, previous[rel])
        atomic_write(backup / 'APP.php.original', old_original)
        atomic_write(backup / 'install.json', saved_state)
        raise
    print('Repaired. Select User settings > Profile > Theme > Halloween, then update and reload.')
    print('Previous registration and installation record retained at ' + str(repair_backup))
    print('If PHP OPcache timestamp validation is disabled, reload the PHP runtime to refresh the theme list.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frontend', type=Path, help='Frontend directory containing assets/ and include/')
    modes = parser.add_mutually_exclusive_group()
    parser.add_argument('--check', action='store_true', help='Read-only validation; combine with --repair or --uninstall to preview that action')
    modes.add_argument('--install', action='store_true')
    modes.add_argument('--repair', action='store_true', help='Restore registration or missing assets after a frontend upgrade')
    modes.add_argument('--upgrade', action='store_true', help='Update an existing Halloween installation without changing the selected theme')
    modes.add_argument('--uninstall', action='store_true', help='Remove Halloween safely; keep upgraded PHP when registration is already absent')
    parser.add_argument('--backup-dir', type=Path, default=Path('/var/backups/zabbix-halloween'),
                        help='Backup location outside the web root; reuse it for uninstall')
    args = parser.parse_args()
    if not any((args.check, args.install, args.repair, args.upgrade, args.uninstall)):
        parser.error('Choose --check, --install, --repair, --upgrade or --uninstall.')
    if args.check and args.upgrade:
        parser.error('--check can be used alone, with --install, --repair or --uninstall.')
    print_notice(uninstall=args.uninstall)
    root = args.frontend.resolve()
    key = digest(str(root).encode())[:16]
    backup = args.backup_dir.resolve() / key
    state_path = backup / 'install.json'
    if root == backup or root in backup.parents:
        raise ValueError('Choose a backup directory outside the frontend web root.')
    for rel in [APP] + ASSETS:
        path = root / rel
        if root not in path.resolve().parents or path.is_symlink():
            raise ValueError('Refusing a target outside the frontend or a symbolic-link target: ' + str(path))

    if args.repair:
        repair_installation(root, backup, check=args.check)
        return

    if args.uninstall:
        uninstall_installation(root, backup, check=args.check)
        return

    if args.upgrade:
        state, _, original = load_record(root, backup)
        for rel, sha in state['installed'].items():
            path = root / rel
            if not path.is_file() or digest(path.read_bytes()) != sha:
                raise ValueError('Installed file changed or is missing; refusing to overwrite later edits: ' + str(path)
                                 + '. After a frontend upgrade, use --repair --check, then --repair.')
        if args.upgrade:
            # Only replace assets: the existing PHP registration and theme choice stay intact.
            defines = (root / 'include/defines.inc.php').read_text()
            version = re.search(r"define\('ZABBIX_VERSION',\s*'([^']+)'", defines)
            if not version or not version[1].startswith('8.0.'):
                raise ValueError('This theme build targets Zabbix 8.0.x.')
            payloads = {rel: (PACKAGE / 'theme' / rel).read_bytes() for rel in ASSETS}
            previous = {rel: (root / rel).read_bytes() for rel in ASSETS}
            if all(previous[rel] == data for rel, data in payloads.items()):
                print('Halloween ' + VERSION + ' assets are already installed. Reload your browser if needed.')
                return
            update_backup = backup / 'updates' / str(time.time_ns())
            update_backup.mkdir(parents=True)
            update_backup.chmod(0o700)
            old_state = state_path.read_bytes()
            atomic_write(update_backup / 'install.json', old_state)
            for rel, data in previous.items():
                atomic_write(update_backup / rel, data)
            new_state = dict(state)
            new_state['installed'] = dict(state['installed'])
            new_state['installed'].update({str(rel): digest(data) for rel, data in payloads.items()})
            new_state['theme_version'] = VERSION
            try:
                for rel, data in payloads.items():
                    atomic_write(root / rel, data)
                atomic_write(state_path, json.dumps(new_state, indent=2).encode('utf-8'))
            except Exception:
                for rel, data in previous.items():
                    atomic_write(root / rel, data)
                atomic_write(state_path, old_state)
                raise
            print('Updated to Halloween ' + VERSION + '. Existing theme selection and APP.php unchanged.')
            print('Previous theme assets saved at ' + str(update_backup))
            print('Hard-refresh the browser (Ctrl+Shift+R or Cmd+Shift+R) to load the new colors and artwork.')
            return
    version = frontend_version(root)
    if state_path.exists():
        if args.check:
            repair_installation(root, backup, check=True)
            return
        raise ValueError('An installation record already exists. After a frontend upgrade use --repair --check, then --repair. Use --upgrade for asset-only updates.')
    for rel in ASSETS:
        if (root / rel).exists():
            raise ValueError('Refusing to overwrite an existing asset: ' + str(root / rel))
    original = (root / APP).read_bytes()
    patched = prepare_app(original)
    php_lint(patched)
    payloads = {APP: patched}
    payloads.update({rel: (PACKAGE / 'theme' / rel).read_bytes() for rel in ASSETS})
    print('Frontend:', root, '\nVersion:', version, '\nBackup:', backup)
    print('Register Halloween in APP.php and add four theme files. No database or service changes.')
    if args.check:
        print('Check passed. No files changed.')
        return
    backup.mkdir(parents=True, exist_ok=True)
    backup.chmod(0o700)
    atomic_write(backup / 'APP.php.original', original)
    state = {'frontend': str(root), 'version': version, 'theme_version': VERSION, 'installer_version': INSTALLER_VERSION, 'original_sha256': digest(original),
             'installed': {str(rel): digest(data) for rel, data in payloads.items()}}
    written = []
    try:
        # Publish assets before registering the theme so it is never selectable without CSS.
        for rel in ASSETS:
            atomic_write(root / rel, payloads[rel])
            written.append(root / rel)
        atomic_write(root / APP, patched)
        atomic_write(state_path, json.dumps(state, indent=2).encode('utf-8'))
    except Exception:
        atomic_write(root / APP, original)
        for path in written:
            path.unlink(missing_ok=True)
        raise
    print('Installed. Select User settings > Profile > Theme > Halloween, then update and reload.')
    print('If PHP OPcache timestamp validation is disabled, reload the PHP runtime to refresh the theme list.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)
