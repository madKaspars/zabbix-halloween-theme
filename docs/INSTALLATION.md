# Halloween for Zabbix — installation guide

Charcoal and violet panels, glowing pumpkin-orange controls, jack-o'-lantern widget headers, bats and a haunted-house backdrop. An original little witch, black cat and pumpkin decorate the login page and tall sidebars. The artwork is static and editable SVG.

Built for Zabbix **8.0.0rc3** from the pinned official Dark theme. Includes compiled CSS, full Sass source, artwork, a reversible installer and an interactive sample preview. No JavaScript is installed in Zabbix. All artwork and fonts load locally.

> **NOT FOR PRODUCTION — LABS AND DEMONSTRATIONS ONLY.** Do not deploy this experimental theme on production, business-critical, or safety-critical monitoring systems.
> The project-specific theme customizations, installer, and documentation were generated with AI assistance in OpenAI Codex using **GPT-6 Astra (`gpt-6-astra`)**. Bundled Zabbix source and third-party fonts retain their original authorship and licenses. AI output may contain defects or inaccurate instructions. Read [the disclaimer](../DISCLAIMER.md).

## Production warning

**This package modifies a shared Zabbix PHP file. It has not been validated on a live production installation and is not intended for production use. Passing automated checks is not an independent security audit or a production certification.**

Registering a theme through `APP.php` is [documented by Zabbix](https://www.zabbix.com/documentation/devel/en/manual/web_interface/theming). That documents the extension mechanism; it does not certify this package or its compatibility with every 8.0 build.

- Installation and repair change `include/classes/core/APP.php`. A PHP syntax or compatibility error can affect the whole web interface and JSON-RPC API, even for users who select another theme. Keep a working shell/deployment rollback route outside the web interface.
- The theme changes CSS across many screens. Existing status/severity declarations are preserved, but layout and contrast still need testing on your actual dashboards, problem lists, forms and graphs.
- Frontend updates may overwrite the registration. Include theme checks and any required rebuild/repair in your upgrade procedure. Avoid running a frontend upgrade and this installer at the same time.
- This build uses 8.0.0rc3 development sources. Accepting an 8.0.x version number is not proof of compatibility with that version.
- The package does not change the database, monitoring server, agents, proxies or running services. It adds local CSS/SVG assets and installs no JavaScript or external asset requests.

For lab experiments, use an isolated, disposable copy of the same frontend build, make PHP CLI available for the installer's syntax check, retain the installer backup, and exercise both installation and uninstall. Start with an individual profile before changing the default/login theme; that limits exposure to the CSS, while the PHP registration remains shared.

The installer prints a concise notice during checks and changes. It does not certify production readiness. See `PRODUCTION-NOTICE.txt` for a short notice that can be distributed with the package.

## Install

All commands below use `/usr/share/zabbix/ui`, the frontend directory for official Zabbix 8.0 packages on RHEL and its derivatives. The [official frontend documentation](https://www.zabbix.com/documentation/8.0/en/manual/installation/frontend) identifies this package location. For a custom installation, replace it with the actual frontend directory containing `assets/` and `include/`.

Extract this package on your frontend server. From the extracted `zabbix-halloween-theme` directory, run:

```sh
python3 install.py /usr/share/zabbix/ui --check
python3 install.py /usr/share/zabbix/ui --install
```

Run as root, or use `sudo` for the installation if required. Select **User settings → Profile → Theme → Halloween**, click **Update**, then reload.

The installer accepts an unmodified `APP.php` or a simple existing theme-list override. It adds Halloween to that list and registers its dark color scheme. It saves the previous `APP.php` outside the web root under `/var/backups/zabbix-halloween/` and adds four files: one CSS file and three SVGs. Existing custom-theme assets are preserved. No database or service changes are made.

Requires Python 3.8 or newer. The installer runs PHP syntax validation if PHP CLI is available. More complex customizations in `APP.php` stop the automatic installation before writing; see the manual merge below.

To also style the login page, an administrator can choose **Halloween** as the default theme under **Administration → General → GUI**. A theme chosen only in your profile applies to your authenticated pages.

The installer refreshes `APP.php`'s modification time so PHP OPcache can discover the new entry. If your PHP runtime has timestamp validation disabled, reload the PHP service that serves this frontend after installation or removal. If the entry appears but old styling remains, hard-refresh the browser with **Ctrl+Shift+R** or **Cmd+Shift+R**.

## Theme disappeared after a frontend upgrade

A frontend upgrade can replace `APP.php` and remove the theme registration while the installation record remains in `/var/backups/zabbix-halloween/`. The `--upgrade` option only updates assets; use `--repair` to recover missing registration.

Use the installer from this package, with the original backup directory still present:

```sh
python3 install.py /usr/share/zabbix/ui --repair --check
python3 install.py /usr/share/zabbix/ui --repair
```

The first command previews recovery without writing. The second registers Halloween in the **current** `APP.php`, restores missing theme files, and updates the installation record. It archives the previous record, previous original PHP backup and pre-repair files under the backup directory's `repairs/` folder. When registration is reapplied, the current frontend file becomes the new uninstall baseline; a later uninstall preserves your upgraded frontend.

Existing supported theme registrations remain. This does not recreate other themes removed by the frontend upgrade. Locally edited Halloween assets or unfamiliar PHP customizations stop the repair before writing. Missing assets are restored; unchanged assets are retained. A healthy installation makes `--repair` a no-op. Standalone `--check` also detects a repairable installation record.

Keep the backup records; do not restore the old whole `APP.php` over the upgraded frontend. Reuse `--backup-dir` if the original installation used a custom backup location. After repair, reopen **User settings → Profile → Theme** and select Halloween. If necessary, refresh the serving PHP runtime's OPcache as described above.

## Preview

Open `preview/index.html`. It includes a dashboard, problems list, filtering, sample acknowledgment and a dialog. **Compare with Dark** switches to the original Zabbix Dark stylesheet. `preview/login.html` shows the sign-in design; no credentials are sent or stored.

The screenshots and preview use reconstructed Zabbix markup and sample data. The witch in the sidebar appears at viewport heights of at least 950px and hides when navigation is compact, leaving room for the menu in shorter windows.

## Compatibility and validation

Pinned upstream commit: `00c492823ad396e2de596f2fd07a9ffdfbf78e41`, identifying itself as **8.0.0rc3**, retrieved 28 October 2026. The installer accepts 8.0.x; later development builds may need a rebuild if components change.

The complete Dark component library is compiled into the theme. Local checks verified selector coverage, unchanged operational status and severity declarations, six text contrast pairs, browser rendering and preview interactions. Installer fixtures cover a fresh frontend and a sample existing custom-theme registration, including byte-for-byte restoration on removal. The 12 recovery/removal tests cover read-only uninstall preview, replaced frontend PHP, missing assets, repeated repair, preservation of another custom theme, uninstall after repair, edited-file protection and rollback after simulated repair/removal failures. See `VALIDATION.txt` for dates and limits. No deployment or live Zabbix integration test was performed, and PHP CLI was unavailable locally.

Classic server-rendered graphs retain the existing/fallback palette because this package does not create a `graph_theme` database record. Configured series colors and thresholds remain under Zabbix's control; the orange and purple lines in the preview are sample chart configuration. Neutral widget styling and default decorative accents follow Halloween.

## Remove or update

Before removing Halloween, select **Dark**, **Blue** or another installed theme in affected user profiles and in the frontend default under **Administration → General → GUI**, if applicable. The file-only installer cannot check or change those saved preferences. Then run the installer from this package:

```sh
python3 install.py /usr/share/zabbix/ui --uninstall --check
python3 install.py /usr/share/zabbix/ui --uninstall
```

The first command previews removal without changing files. The second checks the recorded hashes and removes only the unchanged Halloween assets that still exist. Unknown extra files are retained.

- If `APP.php` still matches the installed registration, removal restores the verified pre-theme file. After a repair, this baseline is the newer frontend saved by that repair.
- If an upgrade already removed Halloween and the current `APP.php` has a supported clean class/simple theme list, removal leaves that PHP file untouched. You do not need to repair just to uninstall.
- Changed theme assets, partial registrations or unfamiliar PHP customizations stop automatic removal. The installer does not force deletion or replace unknown changes.
- Pre-removal files and the installation record are retained under the backup directory's `uninstalls/` folder. On a caught removal failure, it attempts to restore the deleted assets and original registration. Keep the backups; this is not a guarantee against power loss or an unwritable filesystem.

Removal preserves the supported custom-theme registrations present in the saved baseline. Reuse the same `--backup-dir` if you chose a custom location. Refresh PHP OPcache if timestamp validation is disabled, then reload the browser.

For a manual installation or a refusal due to later PHP edits, back up the **current** `APP.php`, remove only the `'halloween-theme'` entry and Halloween-specific dark-scheme condition/method, and preserve other themes and custom methods. Validate the edited PHP before publishing it. Then remove the four package-owned files listed in `install.py` after checking for local edits; never restore an old whole frontend file over a newer one. Keep the old installer records as evidence of the original installation.

For future Halloween asset releases, run the new package's `--upgrade` command. It checks for local edits, saves the old assets and leaves registration and theme selection intact. Use `--repair` when a frontend upgrade removed registration or theme files.

Zabbix frontend upgrades may replace `APP.php`. Use the repair workflow above to register the theme in the new frontend. Rebuild from matching Sass sources when components change; repair does not recompile the theme for a new Zabbix release.

## Manual merge for customized frontends

Back up `include/classes/core/APP.php` outside the web root. Copy the contents of `theme/assets/styles/` into the frontend's `assets/styles/` directory.

If `getThemes()` already exists, add the Halloween entry to its returned theme list. Otherwise add this method inside `class APP extends ZBase`:

```php
public static function getThemes() {
    return array_merge(parent::getThemes(), [
        'halloween-theme' => _('Halloween')
    ]);
}
```

Also add the dark-scheme override. If you already override `getColorScheme()`, merge this condition into that method while preserving your existing logic:

```php
public static function getColorScheme(string $theme): string {
    return $theme === 'halloween-theme'
        ? ZBX_COLOR_SCHEME_DARK
        : parent::getColorScheme($theme);
}
```

Do not define either method twice. Validate the resulting file with your frontend's PHP CLI before publishing it. The automatic installer cannot uninstall a manual merge.

The theme-list registration follows [Zabbix's custom-theme documentation](https://www.zabbix.com/documentation/devel/en/manual/web_interface/theming); the color-scheme method matches the bundled 8.0.0rc3 source.

## Customize and rebuild

- `source/_halloween-palette.scss`: named interface colors.
- `source/_halloween-details.scss`: decorations, rounded corners and focus outlines.
- `theme/assets/styles/halloween/*.svg`: original editable artwork.
- `source/zabbix-sass/`: complete pinned upstream Sass.
- `build.py`: derives `_halloween-dark-base.scss` with overridable variables, then compiles the full theme and preview stylesheets.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-build.txt
python3 build.py
```

No Sass tooling is needed on the server to install the compiled theme. To remove artwork, append this CSS and rebuild or edit the compiled stylesheet:

```css
:root {
    --halloween-scene: none;
    --halloween-witch: none;
    --halloween-pumpkin: none;
}
.signin-container::before,
.sidebar:not(.is-compact):not(.is-hidden) .nav-user::before,
.dashboard-grid-widget-header h4::before {
    display: none;
}
```

## License

GNU AGPL version 3; see `LICENSE`. Includes Zabbix SIA Sass and preview font assets, with full corresponding theme source. The bundled Inter font uses SIL Open Font License 1.1; see `preview/assets/fonts/Inter-LICENSE.txt`. Original Halloween artwork is included under the package's AGPL license. This is an independent custom theme; Zabbix remains a trademark of its owner.

Upstream: [Zabbix at the pinned commit](https://github.com/zabbix/zabbix/tree/00c492823ad396e2de596f2fd07a9ffdfbf78e41).
