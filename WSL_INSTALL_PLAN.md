# WSL Installation Fix Plan

## Diagnosis

`wsl --install` fails at *"Installing: Windows Subsystem for Linux 3.0.3"* with
**Catastrophic failure**.

- Windows: Windows 11 Home Single Language, build **26200** (AMD64 / Ryzen 5 5600H)
- Windows username: `Nagendra Pai` (contains a **space**)
- `wsl.exe` is only the in-box stub (`10.0.26100.1`); no WSL package is installed

This is a known Microsoft bug on **build 26200**, confirmed in
[microsoft/WSL issue #13806](https://github.com/microsoft/WSL/issues/13806).
Microsoft's developer (OneBlue) stated the trigger is **a space in the Windows
username**, and it is only fixed in insider builds. The official workaround is to
**install the WSL MSI manually**.

The correct, verified installer is already on disk:

- Path: `D:\Temp\wsl.3.0.3.0.x64.msi`
- Size: `367,575,040` bytes
- SHA256: `ae977286974255bd26bf925f00f40f5692c6b2084155cbc0563c09aea091f211` (matches the official 3.0.3 x64 asset)

## Plan to resolve

### 0. Verify the MSI (optional re-check)

```powershell
(Get-FileHash 'D:\Temp\wsl.3.0.3.0.x64.msi' -Algorithm SHA256).Hash
```

### 1. Open PowerShell as Administrator

The MSI needs elevation.

### 2. Install the WSL package manually (bypasses the buggy Store/WDD path)

```powershell
Start-Process msiexec.exe -ArgumentList '/i','D:\Temp\wsl.3.0.3.0.x64.msi','/qb' -Verb RunAs -Wait
```

Or silently, with no UI:

```powershell
Start-Process msiexec.exe -ArgumentList '/i','D:\Temp\wsl.3.0.3.0.x64.msi','/qn' -Verb RunAs -Wait
```

You can also simply double-click the MSI in Explorer.

### 3. Reboot (required)

```powershell
Restart-Computer
```

### 4. Verify WSL is now working

```powershell
wsl --version
wsl --status
```

Expect a real WSL version (`3.0.3.0`) instead of the "not installed" stub.

### 5. Ensure the Windows features are on (if `wsl --status` complains)

Run in an admin PowerShell:

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
```

### 6. Install the Linux distro

```powershell
wsl --list --online
wsl --install -d Ubuntu
```

First launch sets your UNIX username/password.

### 7. Install Docker Desktop (WSL2 backend)

```powershell
winget install --id Docker.DockerDesktop -e
```

Then Docker Desktop -> Settings -> verify **"Use the WSL 2 based engine"** and enable
your Ubuntu distro under **Resources -> WSL Integration**.

## Fallback if it still fails

The space in the username is the persistent culprit. If the manual MSI still errors,
the robust fix is a **space-free Windows account**:

```powershell
# admin PowerShell
net user wsluser <Password> /add
net localgroup Administrators wsluser /add
```

Log in as `wsluser` and rerun `wsl --install`.

> Renaming the existing profile folder is *not* recommended - it breaks
> registry/profile paths.

## Notes / tradeoffs

- Run MSI install and DISM as **Administrator**; distro installs do not need admin.
- If BIOS virtualization is off, you'll get `0x80370102` - enable SVM/VT-x.
  Task Manager -> Performance -> CPU -> "Virtualization: Enabled" checks this.
- Windows 11 **Home** is fine - WSL2 only needs "Virtual Machine Platform", not Hyper-V.
