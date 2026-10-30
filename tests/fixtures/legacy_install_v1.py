#!/usr/bin/env python3
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frontend', type=Path, help='Frontend directory containing assets/ and include/')
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check', action='store_true', help='Validate and show the install plan without writing')
    modes.add_argument('--install', action='store_true')
    modes.add_argument('--upgrade', action='store_true', help='Update an existing Halloween installation without changing the selected theme')
    modes.add_argument('--uninstall', action='store_true', help='Restore the saved APP.php if installed files are unchanged')
    parser.add_argument('--backup-dir', type=Path, default=Path('/var/backups/zabbix-halloween'),
                        help='Backup location outside the web root; reuse it for uninstall')
    args = parser.parse_args()
    root = args.frontend.resolve()
    key = digest(str(root).encode())[:16]
    backup = args.backup_dir.resolve() / key
    state_path = backup / 'install.json'
    for rel in [APP] + ASSETS:
        path = root / rel
        if root not in path.resolve().parents or path.is_symlink():
            raise ValueError('Refusing a target outside the frontend or a symbolic-link target: ' + str(path))

    if args.uninstall or args.upgrade:
        if not state_path.exists():
            raise ValueError('No installation record found in ' + str(backup))
        state = json.loads(state_path.read_text())
        if state['frontend'] != str(root):
            raise ValueError('Backup belongs to a different frontend.')
        expected_paths = {str(x) for x in [APP] + ASSETS}
        if set(state['installed']) != expected_paths:
            raise ValueError('Unexpected file list in installation record.')
        for rel, sha in state['installed'].items():
            path = root / rel
            if not path.is_file() or digest(path.read_bytes()) != sha:
                raise ValueError('Installed file changed; refusing to overwrite later edits: ' + str(path))
        original = (backup / 'APP.php.original').read_bytes()
        if digest(original) != state['original_sha256']:
            raise ValueError('Original APP.php backup failed checksum verification.')
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
        php_lint(original)
        atomic_write(root / APP, original)
        for rel in ASSETS:
            (root / rel).unlink()
        try:
            (root / 'assets/styles/halloween').rmdir()
        except OSError:
            pass
        state_path.rename(backup / 'uninstalled.json')
        print('Halloween removed. Original APP.php restored; backup retained at ' + str(backup))
        return

    version_file = root / 'include/defines.inc.php'
    if not (root / APP).is_file() or not (root / 'assets/styles/dark-theme.css').is_file() or not version_file.is_file():
        raise ValueError('Not a recognized Zabbix frontend directory: ' + str(root))
    version = re.search(r"define\('ZABBIX_VERSION',\s*'([^']+)'", version_file.read_text())
    if not version or not version[1].startswith('8.0.'):
        raise ValueError('This build targets Zabbix 8.0.x. Rebuild against your exact source version before installing elsewhere.')
    if state_path.exists():
        raise ValueError('Halloween is already installed. Use --upgrade to update its theme assets.')
    for rel in ASSETS:
        if (root / rel).exists():
            raise ValueError('Refusing to overwrite an existing asset: ' + str(root / rel))
    original = (root / APP).read_bytes()
    patched = prepare_app(original)
    php_lint(patched)
    payloads = {APP: patched}
    payloads.update({rel: (PACKAGE / 'theme' / rel).read_bytes() for rel in ASSETS})
    print('Frontend:', root, '\nVersion:', version[1], '\nBackup:', backup)
    print('Register Halloween in APP.php and add four theme files. No database or service changes.')
    if args.check:
        print('Check passed. No files changed.')
        return
    if root == backup or root in backup.parents:
        raise ValueError('Choose a backup directory outside the frontend web root.')
    backup.mkdir(parents=True, exist_ok=True)
    backup.chmod(0o700)
    atomic_write(backup / 'APP.php.original', original)
    state = {'frontend': str(root), 'version': version[1], 'theme_version': VERSION, 'original_sha256': digest(original),
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
