# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Halloween theme contributors
# Provided without warranty; see LICENSE and DISCLAIMER.md.
from pathlib import Path
import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import sass
import tinycss2

root = Path(__file__).resolve().parents[1]
lines = []
def report(text):
    lines.append(text)
    print(text)

def rules(css):
    result = {}
    parsed = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
    assert not [r for r in parsed if r.type == 'error']
    for rule in parsed:
        if rule.type != 'qualified-rule':
            continue
        declarations = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
        assert not [d for d in declarations if d.type == 'error']
        text = [(d.name,tinycss2.serialize(d.value).strip(),d.important) for d in declarations if d.type=='declaration']
        selectors, chunk = [], []
        for token in rule.prelude:
            if token.type == 'literal' and token.value == ',':
                selectors.append(tinycss2.serialize(chunk).strip())
                chunk = []
            else:
                chunk.append(token)
        selectors.append(tinycss2.serialize(chunk).strip())
        for selector in selectors:
            result[selector] = text
    return result

base_css = sass.compile(filename=str(root/'source/zabbix-sass/dark-theme.scss'),output_style='expanded')
theme_css = (root/'theme/assets/styles/halloween-theme.css').read_text()
baseline = rules(base_css)
theme = rules(theme_css)
assert set(baseline).issubset(theme)
report(f'PASS: Compiled and parsed full theme; retained all {len(baseline)} upstream selectors.')
semantic = [s for s in baseline if re.search(r'^\.(?:red|green|yellow|orange|problem-(?:unack|ack)|ok-(?:unack|ack)|status-(?:red|green|yellow)|(?:log-)?(?:na|normal|info|warning|average|high|disaster)-bg)(?:\W|$)',s) and '.blink-hidden a' not in s]
for selector in semantic:
    assert baseline[selector] == theme[selector], selector
report(f'PASS: {len(semantic)} semantic color/status selector declarations unchanged from upstream build.')
assert '@import ' not in theme_css
for asset in re.findall(r'url\([\'"]?(halloween/[^\)\'\"]+)', theme_css):
    assert (root/'theme/assets/styles'/asset.split('?')[0]).is_file()
report('PASS: Standalone CSS; all custom image references resolve; no external assets added.')

def luminance(hexcolor):
    channels=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
    c=[n/12.92 if n<=0.04045 else ((n+.055)/1.055)**2.4 for n in channels]
    return sum(x*y for x,y in zip(c,[.2126,.7152,.0722]))
for name,foreground,background in [('Panel text','#f6ece3','#241d2b'),('Links','#ffb56e','#241d2b'),('Secondary text','#c3b3c8','#241d2b'),('Primary button','#171018','#ff983e'),('Sidebar navigation','#e8d8cb','#17111d'),('Sidebar selected','#171018','#ff983e')]:
    hi,lo=sorted([luminance(foreground),luminance(background)],reverse=True)
    ratio=(hi+.05)/(lo+.05)
    assert ratio>=4.5,(name,ratio)
    report(f'PASS: {name} contrast {ratio:.2f}:1 (normal-state theme pair).')

with tempfile.TemporaryDirectory(prefix='halloween-validation-') as folder:
    temp=Path(folder); frontend=temp/'frontend'; backup=temp/'backups'
    def fixture(content=None):
        shutil.rmtree(frontend,ignore_errors=True)
        shutil.rmtree(backup,ignore_errors=True)
        (frontend/'include/classes/core').mkdir(parents=True)
        (frontend/'assets/styles').mkdir(parents=True)
        (frontend/'include/classes/core/APP.php').write_bytes(content or (root/'tests/fixtures/APP.php').read_bytes())
        shutil.copy2(root/'tests/fixtures/defines.inc.php',frontend/'include/defines.inc.php')
        (frontend/'assets/styles/dark-theme.css').write_text('/* fixture */')
    def run(mode,expect=0):
        result=subprocess.run([sys.executable,str(root/'install.py'),str(frontend),mode,'--backup-dir',str(backup)],capture_output=True,text=True)
        assert result.returncode==expect,result.stdout+result.stderr
        return result
    fixture(); app=frontend/'include/classes/core/APP.php'; original=app.read_bytes()
    old_mtime = 1600000000
    os.utime(app, (old_mtime, old_mtime))
    original_mode = app.stat().st_mode
    run('--check'); assert app.read_bytes()==original; assert not backup.exists()
    run('--install'); installed=app.read_bytes()
    assert installed.count(b'function getThemes(')==1 and installed.count(b'function getColorScheme(')==1
    assert b"'halloween-theme' => _('Halloween')" in installed and b'ZBX_COLOR_SCHEME_DARK' in installed
    assert b'parent::getColorScheme($theme)' in installed
    assert app.stat().st_mtime > old_mtime, 'APP.php must get a fresh timestamp for OPcache'
    assert app.stat().st_mode == original_mode, 'APP.php permissions must be preserved'
    for asset in (root/'theme').rglob('*'):
        if asset.is_file(): assert (frontend/asset.relative_to(root/'theme')).read_bytes()==asset.read_bytes()
    run('--install',1)
    assert 'already installed' in run('--upgrade').stdout
    # Simulate an earlier asset build with its valid install record.
    state_path = next(backup.glob('*/install.json'))
    state = json.loads(state_path.read_text())
    css = frontend/'assets/styles/halloween-theme.css'
    previous_css = css.read_bytes()+b'\n/* earlier build fixture */'
    css.write_bytes(previous_css)
    state['installed']['assets/styles/halloween-theme.css']=hashlib.sha256(previous_css).hexdigest()
    state_path.write_text(json.dumps(state))
    installed_mtime = app.stat().st_mtime_ns
    run('--upgrade')
    assert app.read_bytes()==installed and app.stat().st_mtime_ns==installed_mtime
    assert css.read_bytes()==(root/'theme/assets/styles/halloween-theme.css').read_bytes()
    assert next((state_path.parent/'updates').glob('*/assets/styles/halloween-theme.css')).read_bytes()==previous_css
    css.write_bytes(css.read_bytes()+b'/* user edit */')
    run('--upgrade',1); assert css.read_bytes().endswith(b'/* user edit */')
    css.write_bytes((root/'theme/assets/styles/halloween-theme.css').read_bytes())
    app.write_bytes(installed+b'\n// later edit\n');run('--uninstall',1);assert b'later edit' in app.read_bytes()
    app.write_bytes(installed);os.utime(app, (old_mtime, old_mtime))
    run('--uninstall');assert app.read_bytes()==original
    assert app.stat().st_mtime > old_mtime, 'Uninstall must also refresh the timestamp'
    assert not css.exists()
    report('PASS: Installer check is read-only; fresh install and uninstall restore APP.php byte-for-byte.')
    report('PASS: One theme-list method and one dark-scheme override; other themes delegate to the parent scheme.')
    report('PASS: Installation and uninstall refresh PHP modification time and preserve permissions.')
    report('PASS: Asset upgrade backs up the earlier build and preserves APP.php; repeat upgrade is a no-op.')
    report('PASS: Duplicate installs and upgrade/uninstall after user edits are rejected without overwriting edits.')
    custom_app=(root/'tests/fixtures/custom_theme_APP.php').read_bytes()
    fixture(custom_app)
    custom_asset=frontend/'assets/styles/example-theme.css'; custom_asset.write_text('existing Example CSS')
    run('--check');assert app.read_bytes()==custom_app
    run('--install'); combined=app.read_bytes()
    assert combined.count(b'function getThemes(')==1
    assert b"'example-theme' => _('Example')" in combined
    assert b"'halloween-theme' => _('Halloween')" in combined
    assert b'ZBX_COLOR_SCHEME_DARK' in combined
    run('--uninstall');assert app.read_bytes()==custom_app
    assert custom_asset.read_text()=='existing Example CSS'
    report('PASS: Installation alongside a sample custom-theme registration retains both entries and all existing assets; uninstall restores the exact baseline APP.php.')
    fixture(original.replace(b'class APP extends ZBase {',b'class APP extends ZBase {\n public function custom() {}'))
    untouched=app.read_bytes();run('--install',1);assert app.read_bytes()==untouched
    assert not (frontend/'assets/styles/halloween-theme.css').exists()
    fixture();(frontend/'include/defines.inc.php').write_text("<?php define('ZABBIX_VERSION', '7.0.1');")
    run('--install',1)
    fixture();(frontend/'assets/styles/halloween-theme.css').write_text('existing');run('--install',1)
    assert (frontend/'assets/styles/halloween-theme.css').read_text()=='existing'
    report('PASS: Unrecognized custom APP.php methods, unsupported versions and existing assets are preserved and rejected.')

report('PASS: PHP lint was available for installer checks.' if shutil.which('php') else 'LIMIT: No local PHP CLI; PHP lint was not executed. Installer invokes it when available on the target.')
report('LIMIT: No live Zabbix frontend/server integration test or deployment was performed.')
(root/'tests/validation-latest.txt').write_text('Halloween theme validation — 30 October 2026\n\n'+'\n'.join(lines)+'\n')
