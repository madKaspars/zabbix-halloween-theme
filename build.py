#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Halloween theme contributors
# Provided without warranty; see LICENSE and DISCLAIMER.md.
"""Build Halloween from the bundled, pinned Zabbix Dark Sass sources."""
from pathlib import Path
import re
import shutil
import sass

ROOT = Path(__file__).resolve().parent
source = ROOT / 'source'
upstream = source / 'zabbix-sass'
dark = (upstream / 'dark-theme.scss').read_text()
# Keep every dark-only component adjustment. Make its global variables defaults
# so our separate UI palette can override them without touching status colors.
dark = re.sub(r'^(\$[\w-]+:[^\n;]+)(;)',
              lambda m: m[0] if '!default' in m[1] else m[1] + ' !default;', dark, flags=re.M)
(source / '_halloween-dark-base.scss').write_text('// Derived from bundled Zabbix Dark; see LICENSE.\n' + dark)
css = sass.compile(filename=str(source / 'halloween-theme.scss'),
                   include_paths=[str(source), str(upstream)], output_style='expanded')
header = '''/* Halloween 1.0 — Zabbix 8.0 development.
 * Based on Zabbix SIA source, commit 00c492823ad396e2de596f2fd07a9ffdfbf78e41.
 * Copyright (C) 2001-2026 Zabbix SIA and theme contributors.
 * SPDX-License-Identifier: AGPL-3.0-only. Complete corresponding source included.
 */
'''
target = ROOT / 'theme/assets/styles/halloween-theme.css'
target.write_text(header + css)
shutil.copy2(target, ROOT / 'preview/assets/styles/halloween-theme.css')
shutil.copytree(ROOT / 'theme/assets/styles/halloween', ROOT / 'preview/assets/styles/halloween', dirs_exist_ok=True)
(ROOT / 'preview/assets/styles/dark-theme.css').write_text(
    sass.compile(filename=str(upstream / 'dark-theme.scss'), output_style='expanded'))
print(f'Built Halloween: {target.stat().st_size:,} bytes')
