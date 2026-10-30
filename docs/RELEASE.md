# Halloween for Zabbix

A dark Halloween theme for Zabbix 8.0, with pumpkin-orange controls, violet panels, bats, a haunted backdrop, and original witch, cat, and jack-o’-lantern artwork.

> [!WARNING]
> **NOT FOR PRODUCTION — LABS AND DEMONSTRATIONS ONLY.** Do not deploy this experimental theme on production, business-critical, or safety-critical monitoring systems. The installer modifies the shared `include/classes/core/APP.php`; a PHP error can disrupt the web interface and API for all users. CSS changes can obscure information or affect readability.

> [!IMPORTANT]
> **AI-GENERATED PROJECT CUSTOMIZATIONS.** The project-specific theme customizations, installer, and documentation were generated with AI assistance in OpenAI Codex using **GPT-6 Astra (`gpt-6-astra`)**. Bundled Zabbix source and third-party fonts retain their original authorship and licenses. AI output may contain defects or inaccurate instructions. Passing automated checks is not an independent security audit or production certification. Naming these tools does not imply endorsement by OpenAI or Zabbix SIA.

The package contains compiled CSS, editable SVG artwork, full theme source, an offline preview, and an installer with checks, backups, repair, asset updates, and uninstall. It targets the pinned Zabbix **8.0.0rc3** frontend; other builds require compatibility testing.

Download `zabbix-halloween-theme-v1.2.3.zip` and verify it against `SHA256SUMS`. Follow the repository README and installation guide. The examples use `/usr/share/zabbix/ui`, the frontend directory for official Zabbix 8.0 packages on RHEL and its derivatives. For a custom installation, supply its actual frontend directory.

Use an isolated, disposable lab with backups and a recovery route outside the web interface. Before uninstalling, select another installed theme in affected profiles and the frontend default. Frontend upgrades may require repair or a stylesheet rebuild.

Licensed under GNU AGPL v3, with Inter fonts under OFL 1.1. Provided as is, without warranty, with liability exclusions only to the extent permitted by law; no disclaimer guarantees immunity from claims. No guaranteed support or response time. The suitability warnings do not impose additional license restrictions. Read the repository LICENSE, NOTICE.md, and DISCLAIMER.md.
