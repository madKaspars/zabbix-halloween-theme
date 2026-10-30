#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Halloween theme contributors
"""Create the public source package deterministically, without local state."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.2.3'
ROOT_FILES = {
    '.gitattributes', '.gitignore', 'README.md', 'LICENSE', 'NOTICE.md',
    'DISCLAIMER.md', 'CONTRIBUTING.md', 'SECURITY.md',
    'PRODUCTION-NOTICE.txt', 'UPSTREAM.txt', 'VALIDATION.txt',
    'build.py', 'install.py', 'requirements-build.txt', 'requirements-test.txt'
}
ROOT_DIRS = {'.github', 'docs', 'scripts', 'tests', 'source', 'theme', 'preview'}
EXCLUDED = {'.git', '.DS_Store', '__pycache__', '.venv', 'node_modules', 'validation-latest.txt'}


def package():
    files = []
    for item in sorted(ROOT.rglob('*')):
        rel = item.relative_to(ROOT)
        if rel.parts[0] not in ROOT_FILES | ROOT_DIRS:
            continue
        if any(part in EXCLUDED for part in rel.parts) or item.suffix in {'.pyc', '.pyo', '.log'}:
            continue
        if item.is_symlink():
            raise RuntimeError('Refusing symlink: ' + str(rel))
        if item.is_file():
            files.append((item, rel))
    for required in ROOT_FILES:
        if not (ROOT / required).is_file():
            raise RuntimeError('Missing release file: ' + required)
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / ('zabbix-halloween-theme-v' + VERSION + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for item, rel in files:
            info = zipfile.ZipInfo('zabbix-halloween-theme/' + rel.as_posix(), (2026, 10, 30, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, item.read_bytes(), compresslevel=9)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / 'SHA256SUMS').write_text(checksum + '  ' + archive.name + '\n')
    print(str(archive))
    print(str(len(files)) + ' files; SHA-256 ' + checksum)


if __name__ == '__main__':
    package()
