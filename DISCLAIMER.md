# Disclaimer and operational notice

> **NOT FOR PRODUCTION — LABS AND DEMONSTRATIONS ONLY.** Do not deploy this experimental theme on production, business-critical, or safety-critical monitoring systems.

This independent community project is supplied voluntarily. It is not affiliated with, endorsed by, certified by, or supported by Zabbix SIA. References to Zabbix identify the software with which this theme is intended to work. Third-party names and marks belong to their respective owners.

## AI generation and review limits

The project-specific theme customizations, installer, and documentation were generated with AI assistance in OpenAI Codex using **GPT-6 Astra (`gpt-6-astra`)**. Bundled Zabbix source and third-party fonts retain their original authorship and licenses.

AI-generated output can contain defects, security weaknesses, inaccurate explanations, and untested assumptions. Automated checks cover selected cases and do not establish completeness, security, accessibility, or production suitability. No independent security audit or production certification is claimed. Review the source and instructions before experimenting in an isolated, disposable environment. The model and tool attribution is provenance, not an assurance of quality or endorsement by OpenAI or Zabbix SIA.

## No warranty

To the extent permitted by applicable law, this software and its accompanying materials are provided **“AS IS” and “AS AVAILABLE,” without warranties or conditions of any kind**, including merchantability, fitness for a particular purpose, accuracy, security, availability, compatibility, or non-infringement. There is no promise that the software is error-free or suitable for production, regulated, safety-critical, or other particular environments.

## Limitation of liability

The warranty disclaimer and limitation of liability in sections 15–17 of the GNU AGPL v3 apply. To the extent permitted by applicable law, copyright holders and other parties who modify or convey this software are not liable for damages arising from its use or inability to be used, including loss of data, service interruption, lost profits, or other direct, indirect, incidental, special, exemplary, or consequential damages, unless applicable law requires otherwise or liability is agreed to in writing.

Nothing here excludes rights or liabilities that cannot lawfully be excluded, changes the GNU AGPL, or adds restrictions to the permissions granted by the applicable licenses. No disclaimer can guarantee immunity from claims or legal liability. Obtain advice from a qualified lawyer for a particular jurisdiction or use case.

## Deployment responsibility

The operator is responsible for obtaining required authorization, maintaining backups, protecting access, and planning recovery for any lab experiment. This is an experimental preview based on Zabbix 8.0.0rc3 and is not intended for production. These suitability warnings do not add restrictions to the permissions granted by the applicable open-source licenses.

The installer modifies the shared `include/classes/core/APP.php` and installs CSS/SVG files. A registration or PHP error may affect the frontend and JSON-RPC API for all users. Styling can affect legibility and operation. Upgrades may overwrite registration or change compatibility. Automated checks and installer safeguards reduce some risks but cannot cover every configuration or failure.

Test installation, upgrade recovery, and removal only in an isolated lab using the exact frontend build. Do not rely on this experimental styling as the sole basis for operational decisions. Keep a working recovery route outside the web interface, retain the installer backups, and select another theme in user/default preferences before uninstalling. Read [the installation guide](docs/INSTALLATION.md) and [production notice](PRODUCTION-NOTICE.txt).

## Support

Maintenance, issue responses, fixes, compatibility updates, and security responses are voluntary and carry no guaranteed response time or service-level agreement. A separate written agreement, if any, governs separately purchased services.
