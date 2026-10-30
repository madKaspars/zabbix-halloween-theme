# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Halloween theme contributors
# Provided without warranty; see LICENSE and DISCLAIMER.md.
"""Installer recovery regressions using isolated frontend directories."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('halloween_install', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='halloween-repair-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.frontend = self.base / 'frontend'
        self.backups = self.base / 'backups'
        self.app = self.frontend / installer.APP
        self.app.parent.mkdir(parents=True)
        self.original = (ROOT / 'tests/fixtures/APP.php').read_bytes()
        self.app.write_bytes(self.original)
        (self.frontend / 'assets/styles').mkdir(parents=True)
        (self.frontend / 'assets/styles/dark-theme.css').write_text('/* stock theme */')
        self.defines = self.frontend / 'include/defines.inc.php'
        self.defines.write_text("<?php define('ZABBIX_VERSION', '8.0.0rc3');")
        # Install with the delivered 1.0 script, not the implementation under test.
        self.old_package = self.base / 'old-package'
        self.old_package.mkdir()
        shutil.copy2(ROOT / 'tests/fixtures/legacy_install_v1.py', self.old_package / 'install.py')
        shutil.copytree(ROOT / 'theme', self.old_package / 'theme')
        self.run_cli('--install', script=self.old_package / 'install.py')
        self.backup = self.backups / installer.digest(str(self.frontend).encode())[:16]
        self.state_path = self.backup / 'install.json'
        self.old_state = self.state_path.read_bytes()
        self.upgraded = self.original.replace(b'<?php', b'<?php\n// Current frontend upgrade; preserve this file.')

    def run_cli(self, *flags, status=0, script=None):
        result = subprocess.run([sys.executable, str(script or ROOT / 'install.py'), str(self.frontend),
                                 *flags, '--backup-dir', str(self.backups)], capture_output=True, text=True)
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def snapshot(self):
        return {str(p.relative_to(self.base)): (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
                for p in self.base.rglob('*') if p.is_file()}

    def replace_frontend(self):
        self.app.write_bytes(self.upgraded)
        self.defines.write_text("<?php define('ZABBIX_VERSION', '8.0.0rc4');")
        os.utime(self.app, (1600000000, 1600000000))

    def test_upgrade_repair_with_kept_some_or_no_assets(self):
        for missing_count in (0, 1, len(installer.ASSETS)):
            with self.subTest(missing=missing_count):
                self.replace_frontend()
                for rel in installer.ASSETS[:missing_count]:
                    (self.frontend / rel).unlink(missing_ok=True)
                before = self.snapshot()
                self.assertIn('Repair check passed', self.run_cli('--repair', '--check'))
                self.assertEqual(self.snapshot(), before)
                self.assertIn('Repair check passed', self.run_cli('--check'))
                self.assertEqual(self.snapshot(), before)
                self.run_cli('--repair')
                self.assertIn(b'Current frontend upgrade', self.app.read_bytes())
                self.assertEqual(self.app.read_bytes().count(b'function getThemes('), 1)
                self.assertEqual(self.app.read_bytes().count(b'function getColorScheme('), 1)
                self.assertGreater(self.app.stat().st_mtime, 1600000000)
                self.assertEqual((self.backup / 'APP.php.original').read_bytes(), self.upgraded)
                self.assertEqual(json.loads(self.state_path.read_bytes())['version'], '8.0.0rc4')
                for rel in installer.ASSETS:
                    self.assertEqual((self.frontend / rel).read_bytes(), (ROOT / 'theme' / rel).read_bytes())
                self.assertTrue(list((self.backup / 'repairs').glob('*/install.json')))
                repaired = self.snapshot()
                self.assertIn('are intact', self.run_cli('--repair'))
                self.assertEqual(self.snapshot(), repaired)
                self.run_cli('--uninstall')
                self.assertEqual(self.app.read_bytes(), self.upgraded)
                self.run_cli('--install')

    def test_keeps_current_custom_theme_but_does_not_resurrect_old_php(self):
        self.upgraded = (ROOT / 'tests/fixtures/custom_theme_APP.php').read_bytes().replace(
            b'<?php', b'<?php\n// Current frontend upgrade; preserve this file.')
        self.replace_frontend()
        css = self.frontend / 'assets/styles/example-theme.css'
        css.write_text('Example custom CSS')
        self.run_cli('--repair')
        self.assertIn(b"'example-theme' => _('Example')", self.app.read_bytes())
        self.assertIn(b"'halloween-theme' => _('Halloween')", self.app.read_bytes())
        self.run_cli('--uninstall')
        self.assertEqual(self.app.read_bytes(), self.upgraded)
        self.assertEqual(css.read_text(), 'Example custom CSS')

    def test_missing_assets_only_keep_original_uninstall_baseline(self):
        installed = self.app.read_bytes()
        (self.frontend / installer.ASSETS[0]).unlink()
        self.run_cli('--repair')
        self.assertEqual(self.app.read_bytes(), installed)
        self.assertEqual((self.backup / 'APP.php.original').read_bytes(), self.original)
        self.run_cli('--uninstall')
        self.assertEqual(self.app.read_bytes(), self.original)

    def test_local_css_edits_and_custom_php_are_refused(self):
        self.replace_frontend()
        css = self.frontend / installer.ASSETS[0]
        css.write_bytes(css.read_bytes() + b'/* user edit */')
        before = self.snapshot()
        self.assertIn('local edits', self.run_cli('--repair', status=1))
        self.assertEqual(self.snapshot(), before)
        css.write_bytes((ROOT / 'theme' / installer.ASSETS[0]).read_bytes())
        self.app.write_bytes(self.upgraded.replace(b'class APP extends ZBase {',
                                                  b'class APP extends ZBase {\npublic function custom() {}'))
        before = self.snapshot()
        self.assertIn('custom methods', self.run_cli('--repair', status=1))
        self.assertEqual(self.snapshot(), before)

    def test_incomplete_registration_is_refused(self):
        self.app.write_bytes(self.app.read_bytes().replace(installer.COLOR_BLOCK.encode(), b''))
        before = self.snapshot()
        self.run_cli('--repair', status=1)
        self.assertEqual(self.snapshot(), before)

    def test_unsupported_version_and_corrupt_backup_are_refused(self):
        self.replace_frontend()
        self.defines.write_text("<?php define('ZABBIX_VERSION', '9.0.0');")
        before = self.snapshot()
        self.run_cli('--repair', status=1)
        self.assertEqual(self.snapshot(), before)
        self.defines.write_text("<?php define('ZABBIX_VERSION', '8.0.0rc4');")
        (self.backup / 'APP.php.original').write_bytes(b'corrupt')
        before = self.snapshot()
        self.assertIn('checksum', self.run_cli('--repair', status=1))
        self.assertEqual(self.snapshot(), before)

    def test_symlink_asset_is_refused(self):
        self.replace_frontend()
        path = self.frontend / installer.ASSETS[0]
        path.unlink()
        outside = self.base / 'outside.css'
        outside.write_text('keep')
        path.symlink_to(outside)
        self.run_cli('--repair', status=1)
        self.assertEqual(outside.read_text(), 'keep')

    def test_repair_failure_restores_files_and_records(self):
        self.replace_frontend()
        missing = self.frontend / installer.ASSETS[0]
        missing.unlink()
        original_write = installer.atomic_write
        failed = False

        def fail_once(path, data):
            nonlocal failed
            if path == self.state_path and not failed:
                failed = True
                raise OSError('simulated record write failure')
            original_write(path, data)

        with patch.object(installer, 'atomic_write', fail_once):
            with self.assertRaisesRegex(OSError, 'simulated'):
                installer.repair_installation(self.frontend, self.backup)
        self.assertEqual(self.app.read_bytes(), self.upgraded)
        self.assertFalse(missing.exists())
        self.assertEqual(self.state_path.read_bytes(), self.old_state)
        self.assertEqual((self.backup / 'APP.php.original').read_bytes(), self.original)
        saved = next((self.backup / 'repairs').glob('*/install.json'))
        self.assertEqual(saved.read_bytes(), self.old_state)

    def test_uninstall_preview_and_normal_removal(self):
        before = self.snapshot()
        output = self.run_cli('--uninstall', '--check')
        self.assertIn('Third-party frontend customization', output)
        self.assertIn('BEFORE REMOVAL', output)
        self.assertIn('Uninstall check passed', output)
        self.assertEqual(self.snapshot(), before)
        self.run_cli('--uninstall')
        self.assertEqual(self.app.read_bytes(), self.original)
        self.assertFalse(self.state_path.exists())
        self.assertEqual((self.backup / 'uninstalled.json').read_bytes(), self.old_state)
        for rel in installer.ASSETS:
            self.assertFalse((self.frontend / rel).exists())
        self.assertTrue(list((self.backup / 'uninstalls').glob('*/before/assets/styles/halloween-theme.css')))

    def test_uninstall_after_upgrade_preserves_new_php_without_repair(self):
        self.replace_frontend()
        (self.frontend / installer.ASSETS[0]).unlink()
        extra = self.frontend / 'assets/styles/halloween/personal.svg'
        extra.write_text('leave this unrelated file')
        other = self.frontend / 'assets/styles/example-theme.css'
        other.write_text('leave Example')
        before = self.snapshot()
        self.assertIn('leave that file unchanged', self.run_cli('--uninstall', '--check'))
        self.assertEqual(self.snapshot(), before)
        old_mtime = self.app.stat().st_mtime_ns
        self.run_cli('--uninstall')
        self.assertEqual(self.app.read_bytes(), self.upgraded)
        self.assertEqual(self.app.stat().st_mtime_ns, old_mtime)
        self.assertEqual(extra.read_text(), 'leave this unrelated file')
        self.assertEqual(other.read_text(), 'leave Example')
        for rel in installer.ASSETS:
            self.assertFalse((self.frontend / rel).exists())

    def test_uninstall_refuses_modified_assets_or_unknown_php(self):
        installed = self.app.read_bytes()
        self.app.write_bytes(installed + b'\n// manual customization\n')
        before = self.snapshot()
        self.assertIn('manual removal', self.run_cli('--uninstall', status=1))
        self.assertEqual(self.snapshot(), before)
        self.app.write_bytes(installed)
        css = self.frontend / installer.ASSETS[0]
        css.write_bytes(css.read_bytes() + b'\n/* custom style */')
        before = self.snapshot()
        self.assertIn('local edits', self.run_cli('--uninstall', status=1))
        self.assertEqual(self.snapshot(), before)

    def test_uninstall_failure_restores_registration_assets_and_record(self):
        installed = self.app.read_bytes()
        before_assets = {rel: (self.frontend / rel).read_bytes() for rel in installer.ASSETS}
        real_unlink = Path.unlink
        target = self.frontend / installer.ASSETS[1]

        def fail_asset(path, *args, **kwargs):
            if path == target:
                raise OSError('simulated asset removal failure')
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, 'unlink', fail_asset):
            with self.assertRaisesRegex(OSError, 'simulated'):
                installer.uninstall_installation(self.frontend, self.backup)
        self.assertEqual(self.app.read_bytes(), installed)
        self.assertEqual(self.state_path.read_bytes(), self.old_state)
        for rel, data in before_assets.items():
            self.assertEqual((self.frontend / rel).read_bytes(), data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
