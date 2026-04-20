#!/usr/bin/env bash
# Install veraPDF greenfield CLI to /opt/verapdf (Ubuntu/Debian — Story 6.5).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

sudo apt-get update
sudo apt-get install -y openjdk-17-jre-headless curl unzip

ZIP_URL="${VERAPDF_INSTALLER_ZIP:-https://software.verapdf.org/releases/verapdf-installer.zip}"
WORKDIR="${RUNNER_TEMP:-/tmp}/verapdf-install"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
curl -fsSL -o verapdf-installer.zip "${ZIP_URL}"
unzip -q -o verapdf-installer.zip
VDIR=(verapdf-greenfield-*)
cd "${VDIR[0]}"
chmod +x verapdf-install

sudo ./verapdf-install "${REPO_ROOT}/scripts/ci/verapdf-auto-install.xml"
sudo ln -sf /opt/verapdf/verapdf /usr/local/bin/verapdf || true
verapdf --version
