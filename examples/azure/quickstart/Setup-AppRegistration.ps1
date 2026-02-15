#Requires -Version 7.0
<#
.SYNOPSIS
    Creates Azure AD App Registration for Orthanc OAuth

.DESCRIPTION
    This script creates an Azure AD app registration with client secret
    for OAuth authentication with Azure Health Data Services DICOM.

    Prerequisites:
    - PowerShell 7.0 or later
    - Azure CLI installed and logged in (az login)
    - Sufficient permissions to create app registrations in Azure AD

    Output:
    - app-registration.json with clientId, clientSecret, servicePrincipalObjectId

.EXAMPLE
    ./Setup-AppRegistration.ps1

.NOTES
    Cross-platform: Works on Windows, macOS, and Linux with PowerShell Core
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# ============================================================================
# Configuration
# ============================================================================

$ScriptDir = $PSScriptRoot
$OutputFile = Join-Path $ScriptDir "app-registration.json"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Azure App Registration Setup" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if app-registration.json already exists
if (Test-Path $OutputFile) {
    Write-Host "⚠ app-registration.json already exists" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to create a NEW app registration? (y/N)"

    if ($response -notmatch '^[Yy]$') {
        Write-Host "Keeping existing app-registration.json"
        exit 0
    }
    Write-Host ""
}

# Check Azure CLI login
try {
    $null = az account show 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Error "Not logged into Azure CLI. Please run: az login"
}

$tenantId = (az account show --query tenantId -o tsv)
Write-Host "Tenant ID: $tenantId" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Create App Registration
# ============================================================================

Write-Host "→ Creating app registration..." -ForegroundColor Yellow

$appName = "orthanc-dicom-oauth-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"

# Create app registration
$appId = (az ad app create `
    --display-name $appName `
    --sign-in-audience "AzureADMyOrg" `
    --query appId `
    -o tsv)

if ([string]::IsNullOrEmpty($appId)) {
    Write-Error "Failed to create app registration"
}

Write-Host "  App ID (Client ID): $appId" -ForegroundColor Gray

# ============================================================================
# Create Service Principal
# ============================================================================

Write-Host "→ Creating service principal..." -ForegroundColor Yellow

# Create service principal for the app
$spObjectId = (az ad sp create `
    --id $appId `
    --query id `
    -o tsv)

if ([string]::IsNullOrEmpty($spObjectId)) {
    Write-Error "Failed to create service principal"
}

Write-Host "  Service Principal Object ID: $spObjectId" -ForegroundColor Gray

# ============================================================================
# Create Client Secret
# ============================================================================

Write-Host "→ Creating client secret..." -ForegroundColor Yellow

# Create client secret (valid for 1 year)
$clientSecret = (az ad app credential reset `
    --id $appId `
    --append `
    --display-name "quickstart-secret" `
    --years 1 `
    --query password `
    -o tsv)

if ([string]::IsNullOrEmpty($clientSecret)) {
    Write-Error "Failed to create client secret"
}

Write-Host "  Client Secret: [hidden]" -ForegroundColor Gray
Write-Host "  ⚠ Secret will expire in 1 year" -ForegroundColor Yellow

# ============================================================================
# Save to File
# ============================================================================

Write-Host ""
Write-Host "→ Saving configuration..." -ForegroundColor Yellow

$config = @{
    tenantId = $tenantId
    clientId = $appId
    clientSecret = $clientSecret
    servicePrincipalObjectId = $spObjectId
    displayName = $appName
    createdAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
}

$config | ConvertTo-Json | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "✓ Configuration saved to: $OutputFile" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Display Summary
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "APP REGISTRATION CREATED SUCCESSFULLY" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Application Details:" -ForegroundColor Cyan
Write-Host "  Display Name: $appName"
Write-Host "  Tenant ID: $tenantId"
Write-Host "  Client ID: $appId"
Write-Host "  Service Principal Object ID: $spObjectId"
Write-Host ""

Write-Host "Security:" -ForegroundColor Yellow
Write-Host "  ⚠ Client secret saved to app-registration.json"
Write-Host "  ⚠ Keep this file secure - it contains sensitive credentials"
Write-Host "  ⚠ Secret expires: $(((Get-Date).AddYears(1)).ToString('yyyy-MM-dd'))"
Write-Host "  ⚠ Add app-registration.json to .gitignore"
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review the app registration in Azure Portal:"
Write-Host "     https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$appId"
Write-Host "  2. Run the deployment script: ./Deploy.ps1"
Write-Host ""

Write-Host "Note:" -ForegroundColor Gray
Write-Host "  DICOM Data Owner permissions will be assigned during deployment"
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
