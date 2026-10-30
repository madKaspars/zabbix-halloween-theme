# Copyright, licenses, and provenance

## AI-generation disclosure

The project-specific theme customizations, installer, and documentation were generated with AI assistance in OpenAI Codex using **GPT-6 Astra (`gpt-6-astra`)**. Bundled Zabbix source and third-party fonts retain their original authorship and licenses. No independent security audit or production certification is claimed. See [DISCLAIMER.md](DISCLAIMER.md).

## Licenses and sources

The package is distributed under GNU AGPL version 3 only, except for components with their own license identified below. The unmodified license text is in [LICENSE](LICENSE).

| Material | Origin | License |
| --- | --- | --- |
| `source/zabbix-sass/` | Zabbix SIA; pinned upstream Sass | AGPL-3.0-only |
| Derived Dark base and compiled CSS | Based on the bundled Zabbix source, with Halloween changes | AGPL-3.0-only |
| Zabbix icon font in the preview and source in `source/zabbix-icons/` | Zabbix SIA | AGPL-3.0-only |
| PHP fixtures in `tests/fixtures/` | Based on Zabbix SIA source; the custom-theme fixture adds a sample registration | AGPL-3.0-only |
| Theme palette, decorations, original SVG artwork, installer, build scripts, tests, preview, and project documentation | Halloween theme contributors, 2026 | AGPL-3.0-only |
| Inter font in `preview/assets/fonts/` | Inter authors; see bundled copyright and license | SIL Open Font License 1.1 |

Upstream repository: <https://github.com/zabbix/zabbix>

Pinned commit: `00c492823ad396e2de596f2fd07a9ffdfbf78e41` (Zabbix 8.0.0rc3). The Sass and frontend baseline were retrieved on 28 October 2026. Icon source was added for the public source distribution on 30 October 2026. See [UPSTREAM.txt](UPSTREAM.txt).

Zabbix source notices identify Copyright (C) 2001–2026 Zabbix SIA. Existing copyright and license headers are preserved. The complete corresponding theme source and build script are included. The icon source includes the upstream SVG inputs and build configuration; see its README. The Inter license is included at [preview/assets/fonts/Inter-LICENSE.txt](preview/assets/fonts/Inter-LICENSE.txt).

The Halloween changes replace decorative interface colors and add static artwork, while retaining the upstream component stylesheet and checked operational status/severity declarations. `build.py` derives an overridable Dark base and compiles the theme. The installer adds registration and dark color-scheme selection to the local frontend. It does not distribute a complete Zabbix server or frontend.

When conveying covered material, preserve notices and comply with the GNU AGPL source requirements. Section 13 also addresses source access for users interacting remotely with modified covered software. The license text governs; this summary is not a substitute for it. The package cannot be relicensed as a whole under MIT or placed in the public domain by its theme contributors.

Zabbix is a trademark of its respective owner. This project does not grant trademark rights, imply endorsement, or include characters from a licensed entertainment franchise.
