# GitHub Actions workflows

This directory contains GitHub Actions workflows for the Canals Workbench project.

## Workflows

### `build.yml` — full multi-platform build (recommended)

Builds and tests on Linux, Windows, and macOS. Also publishes a PyPI package.

**Triggers:**
- Push to `main` / `master` / `develop`
- Pull request to those branches
- Manual via the Actions tab
- Tag push matching `v*` (e.g., `v1.4.0`) — creates a GitHub Release

**Jobs:**
1. `test` — runs unit tests on Python 3.10, 3.11, 3.12
2. `build-linux` — produces `Canals-linux-x64.tar.gz` (~125 MB)
3. `build-windows` — produces `Canals-windows-x64.zip` containing `Canals.exe` (~130 MB)
4. `build-macos` — produces `Canals-macos-universal.tar.gz` (~70 MB)
5. `build-pypi` — produces sdist + wheel for `pip install canals-workbench`
6. `release-summary` — prints a release summary (only on tag pushes)

**Approximate build times:**
- Linux: ~ 3 min
- Windows: ~ 5 min
- macOS: ~ 5 min
- PyPI: ~ 1 min

Total wall-clock: ~ 6 min (jobs run in parallel after `test`).

### `build-windows-only.yml` — Windows .exe only (faster)

Builds **only** the Windows executable. Useful if you only need the `.exe`
and don't want to wait for Linux/macOS.

**Triggers:** same as above.

**Jobs:**
- `build-windows` — produces `Canals-windows-x64.zip`

**Approximate build time:** ~ 4 min.

## How to use

### Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/abbas-hebah/canals-workbench.git
git push -u origin main
```

GitHub will automatically run `build.yml` on every push. Download the
artifacts from the Actions tab.

### Create a release

```bash
git tag v1.4.0
git push origin v1.4.0
```

GitHub will:
1. Run all builds
2. Create a GitHub Release at https://github.com/YOUR_USER/canals-workbench/releases/tag/v1.4.0
3. Attach the binaries (`Canals-windows-x64.zip`, `Canals-macos-universal.tar.gz`, `Canals-linux-x64.tar.gz`) as release assets

### Run manually

Open the GitHub repo → Actions tab → "Build Canals Workbench" → "Run workflow".

## Artifacts

After a successful run, artifacts are available at:
- `https://github.com/YOUR_USER/canals-workbench/actions/runs/<run-id>#artifacts`

Each artifact is a downloadable zip / tar.gz:
- `Canals-windows-x64.zip` — `Canals.exe`, ~ 130 MB, the standalone Windows binary
- `Canals-linux-x64.tar.gz` — `Canals`, ~ 125 MB, the standalone Linux binary
- `Canals-macos-universal.tar.gz` — `Canals`, ~ 70 MB, the macOS universal binary
- `Canals-pypi` — `*.whl` and `*.tar.gz` for `pip install`

## Optional: PyPI publishing

To automatically publish to PyPI on tag push, add this step to `build-pypi`:

```yaml
- name: Publish to PyPI
  if: startsWith(github.ref, 'refs/tags/v')
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
```

You'll need to:
1. Create a PyPI account at https://pypi.org/
2. Generate an API token at https://pypi.org/manage/account/token/
3. Add it as a GitHub repository secret named `PYPI_API_TOKEN`

## Optional: code signing on Windows

To reduce Windows Defender false positives, sign the .exe with a code-signing
certificate:

1. Buy a code-signing certificate (e.g., from Sectigo, DigiCert) — ~ $200/year
2. Convert to PFX format
3. Add `WINDOWS_CERT_PFX` and `WINDOWS_CERT_PASSWORD` as GitHub secrets
4. Add a signing step to `build-windows`:

```yaml
- name: Sign executable
  if: startsWith(github.ref, 'refs/tags/v')
  shell: pwsh
  run: |
    $pfx = [Convert]::FromBase64String($env:WINDOWS_CERT_PFX_BASE64)
    $pfxPath = Join-Path $env:RUNNER_TEMP 'cert.pfx'
    [IO.File]::WriteAllBytes($pfxPath, $pfx)
    Set-AuthenticodeSignature -FilePath "dist\Canals.exe" `
      -Certificate (Get-PfxCertificate -FilePath $pfxPath `
        -Password (ConvertTo-SecureString -String $env:WINDOWS_CERT_PASSWORD -AsPlainText -Force))
  env:
    WINDOWS_CERT_PFX_BASE64: ${{ secrets.WINDOWS_CERT_PFX }}
    WINDOWS_CERT_PASSWORD: ${{ secrets.WINDOWS_CERT_PASSWORD }}
```

## License

MIT — see LICENSE in the parent directory.
