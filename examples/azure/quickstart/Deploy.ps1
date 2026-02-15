#Requires -Version 7.0
<#
.SYNOPSIS
    Deploys Orthanc OAuth Azure Quickstart

.DESCRIPTION
    This script deploys a completely self-contained Orthanc instance with OAuth
    authentication that works on brand new Azure subscriptions.

    Prerequisites:
    - PowerShell 7.0 or later
    - Azure CLI installed and logged in (az login)
    - Docker Desktop running
    - app-registration.json (or run Setup-AppRegistration.ps1)

.EXAMPLE
    ./Deploy.ps1

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
$ParamsFile = Join-Path $ScriptDir "deployment-params.json"
$AppRegFile = Join-Path $ScriptDir "app-registration.json"
$OutputFile = Join-Path $ScriptDir "deployment-output.json"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Orthanc OAuth Azure Quickstart Deployment" -ForegroundColor Cyan
Write-Host "Truly standalone - works on brand new Azure subscriptions" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Validate Prerequisites
# ============================================================================

Write-Host "→ Step 1/7: Validating prerequisites..." -ForegroundColor Yellow

# Check files exist
if (-not (Test-Path $ParamsFile)) {
    Write-Error "deployment-params.json not found. Please create it with required parameters."
}

if (-not (Test-Path $AppRegFile)) {
    Write-Error "app-registration.json not found. Please run: ./Setup-AppRegistration.ps1"
}

# Check Azure CLI
try {
    $null = az account show 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Error "Not logged into Azure CLI. Please run: az login"
}

# Check Docker
try {
    $null = docker info 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop"
}

Write-Host "✓ Prerequisites validated" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 2: Load Configuration
# ============================================================================

Write-Host "→ Step 2/7: Loading configuration..." -ForegroundColor Yellow

$params = Get-Content $ParamsFile | ConvertFrom-Json
$appReg = Get-Content $AppRegFile | ConvertFrom-Json

$environmentName = $params.environmentName
$location = $params.location
$resourceGroup = $params.resourceGroupName
$postgresAdminUser = $params.postgresAdminUsername
$postgresAdminPassword = $params.postgresAdminPassword
$orthancUsername = $params.orthancUsername
$orthancPassword = $params.orthancPassword

$tenantId = $appReg.tenantId
$oauthClientId = $appReg.clientId
$oauthClientSecret = $appReg.clientSecret
$servicePrincipalObjectId = $appReg.servicePrincipalObjectId

Write-Host "  Environment: $environmentName"
Write-Host "  Location: $location"
Write-Host "  Resource Group: $resourceGroup"
Write-Host ""

# ============================================================================
# Step 3: Register Azure Resource Providers
# ============================================================================

Write-Host "→ Step 3/7: Registering Azure resource providers..." -ForegroundColor Yellow
Write-Host "  (Required for brand new subscriptions)"
Write-Host ""

$providers = @(
    "Microsoft.ContainerRegistry",
    "Microsoft.HealthcareApis",
    "Microsoft.Storage",
    "Microsoft.DBforPostgreSQL",
    "Microsoft.App",
    "Microsoft.OperationalInsights"
)

foreach ($provider in $providers) {
    Write-Host "  Checking $provider..." -NoNewline

    $regState = (az provider show --namespace $provider --query "registrationState" -o tsv 2>$null)

    if ($regState -ne "Registered") {
        Write-Host " Registering..." -ForegroundColor Yellow
        az provider register --namespace $provider --wait | Out-Null
        Write-Host "    ✓ $provider registered" -ForegroundColor Green
    } else {
        Write-Host " ✓ Already registered" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✓ All resource providers registered" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 4: Deploy Infrastructure
# ============================================================================

Write-Host "→ Step 4/8: Deploying Azure infrastructure..." -ForegroundColor Yellow
Write-Host "  This creates all resources including:" -ForegroundColor Gray
Write-Host "    - Azure Container Registry (new!)" -ForegroundColor Gray
Write-Host "    - Healthcare Workspace + DICOM Service" -ForegroundColor Gray
Write-Host "    - PostgreSQL Database" -ForegroundColor Gray
Write-Host "    - Storage Account" -ForegroundColor Gray
Write-Host "    - Container Apps Environment" -ForegroundColor Gray
Write-Host "    - Log Analytics" -ForegroundColor Gray
Write-Host ""
Write-Host "  Note: Container App will be deployed in next phase after image push" -ForegroundColor Gray
Write-Host ""

$deploymentName = "orthanc-infra-$environmentName-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# PHASE 1: Deploy infrastructure WITHOUT Container App (image doesn't exist yet)
Write-Host "  Phase 1: Deploying infrastructure (ACR, Healthcare, DB, Storage)..." -ForegroundColor Gray

$deploymentParams = @{
    environmentName = $environmentName
    location = $location
    resourceGroupName = $resourceGroup
    tenantId = $tenantId
    oauthClientId = $oauthClientId
    oauthClientSecret = $oauthClientSecret
    servicePrincipalObjectId = $servicePrincipalObjectId
    postgresAdminUsername = $postgresAdminUser
    postgresAdminPassword = $postgresAdminPassword
    orthancUsername = $orthancUsername
    orthancPassword = $orthancPassword
    deployContainerApp = $false
}

$paramsJson = $deploymentParams | ConvertTo-Json -Compress
$tempParamsFile = Join-Path ([System.IO.Path]::GetTempPath()) "deploy-params-$([guid]::NewGuid()).json"
$paramsJson | Out-File -FilePath $tempParamsFile -Encoding UTF8

try {
    az deployment sub create `
        --name $deploymentName `
        --location $location `
        --template-file (Join-Path $ScriptDir "main.bicep") `
        --parameters "@$tempParamsFile" `
        --query properties.outputs `
        -o json | Out-File -FilePath $OutputFile -Encoding UTF8

    if ($LASTEXITCODE -ne 0) {
        throw "Infrastructure deployment failed"
    }
} finally {
    Remove-Item $tempParamsFile -ErrorAction SilentlyContinue
}

Write-Host "✓ Infrastructure deployed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 5: Get ACR Details
# ============================================================================

Write-Host "→ Step 5/8: Getting Container Registry details..." -ForegroundColor Yellow

$outputs = Get-Content $OutputFile | ConvertFrom-Json
$containerRegistryName = $outputs.containerRegistryName.value
$containerImage = "${containerRegistryName}.azurecr.io/orthanc-oauth:latest"

Write-Host "  Registry: $containerRegistryName"
Write-Host "  Image: $containerImage"
Write-Host ""

# Get ACR credentials
$acrPassword = (az acr credential show --name $containerRegistryName --query "passwords[0].value" -o tsv)

if ([string]::IsNullOrEmpty($acrPassword)) {
    Write-Error "Failed to get ACR password"
}

Write-Host "✓ Container Registry credentials retrieved" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 6: Build and Push Docker Image
# ============================================================================

Write-Host "→ Step 6/8: Building and pushing Docker image..." -ForegroundColor Yellow
Write-Host "  CRITICAL: Building for linux/amd64 (Azure Container Apps requirement)" -ForegroundColor Magenta
Write-Host ""

# Login to Docker registry
Write-Host "  Logging into ACR..."
$acrPassword | docker login "${containerRegistryName}.azurecr.io" --username $containerRegistryName --password-stdin

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker login failed"
}

# Navigate to project root
$projectRoot = Join-Path $ScriptDir ".." | Join-Path -ChildPath ".." | Join-Path -ChildPath ".."
Push-Location $projectRoot

try {
    # Build with explicit platform for Azure deployment
    docker buildx build `
        --platform linux/amd64 `
        -t $containerImage `
        -f examples/azure/quickstart/Dockerfile `
        --push `
        .

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
    }
} finally {
    Pop-Location
}

Write-Host "✓ Docker image built and pushed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 7: Deploy Container App (Phase 2)
# ============================================================================

Write-Host "→ Step 7/8: Deploying Container App (now that image exists)..." -ForegroundColor Yellow
Write-Host "  Phase 2: Creating Container App with the pushed image" -ForegroundColor Gray
Write-Host ""

$deploymentNamePhase2 = "orthanc-app-$environmentName-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$deploymentParamsPhase2 = @{
    environmentName = $environmentName
    location = $location
    resourceGroupName = $resourceGroup
    tenantId = $tenantId
    oauthClientId = $oauthClientId
    oauthClientSecret = $oauthClientSecret
    servicePrincipalObjectId = $servicePrincipalObjectId
    postgresAdminUsername = $postgresAdminUser
    postgresAdminPassword = $postgresAdminPassword
    orthancUsername = $orthancUsername
    orthancPassword = $orthancPassword
    deployContainerApp = $true
}

$paramsJsonPhase2 = $deploymentParamsPhase2 | ConvertTo-Json -Compress
$tempParamsFilePhase2 = Join-Path ([System.IO.Path]::GetTempPath()) "deploy-params-phase2-$([guid]::NewGuid()).json"
$paramsJsonPhase2 | Out-File -FilePath $tempParamsFilePhase2 -Encoding UTF8

try {
    az deployment sub create `
        --name $deploymentNamePhase2 `
        --location $location `
        --template-file (Join-Path $ScriptDir "main.bicep") `
        --parameters "@$tempParamsFilePhase2" `
        --query properties.outputs `
        -o json | Out-File -FilePath $OutputFile -Encoding UTF8

    if ($LASTEXITCODE -ne 0) {
        throw "Container App deployment failed"
    }
} finally {
    Remove-Item $tempParamsFilePhase2 -ErrorAction SilentlyContinue
}

Write-Host "✓ Container App deployed and running" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 8: Upload Sample DICOM Files (Optional)
# ============================================================================

$outputs = Get-Content $OutputFile | ConvertFrom-Json
$containerAppUrl = $outputs.containerAppUrl.value

Write-Host "→ Step 8/8: Upload sample DICOM test files? (Optional)" -ForegroundColor Yellow
Write-Host "  This will upload 3 sample CT images to your Orthanc instance" -ForegroundColor Gray
Write-Host ""
$uploadResponse = Read-Host "Upload test files? (Y/n)"

if ($uploadResponse -match '^[Yy]$' -or [string]::IsNullOrEmpty($uploadResponse)) {
    Write-Host ""
    Write-Host "Uploading sample DICOM files..." -ForegroundColor Yellow
    Write-Host ""

    # Wait for Container App to be fully ready
    Write-Host "  Waiting for Orthanc to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 10

    $sampleDir = Join-Path $ScriptDir ".." | Join-Path -ChildPath "test-data" | Join-Path -ChildPath "sample-study"
    $uploadCount = 0
    $uploadErrors = 0

    $dicomFiles = Get-ChildItem -Path $sampleDir -Filter "*.dcm" -File

    foreach ($dicomFile in $dicomFiles) {
        Write-Host "  Uploading $($dicomFile.Name)..." -ForegroundColor Gray

        $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${orthancUsername}:${orthancPassword}"))

        try {
            $response = Invoke-WebRequest `
                -Uri "https://$containerAppUrl/instances" `
                -Method POST `
                -Headers @{
                    "Authorization" = "Basic $auth"
                    "Content-Type" = "application/dicom"
                } `
                -InFile $dicomFile.FullName `
                -UseBasicParsing `
                -ErrorAction Stop

            if ($response.StatusCode -eq 200) {
                Write-Host "    ✓ $($dicomFile.Name) uploaded successfully" -ForegroundColor Green
                $uploadCount++
            }
        } catch {
            Write-Host "    ✗ Failed to upload $($dicomFile.Name): $($_.Exception.Message)" -ForegroundColor Red
            $uploadErrors++
        }
    }

    Write-Host ""
    if ($uploadCount -gt 0) {
        Write-Host "✓ Uploaded $uploadCount sample DICOM file(s)" -ForegroundColor Green
        if ($uploadErrors -gt 0) {
            Write-Host "⚠ Failed to upload $uploadErrors file(s)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ No DICOM files were uploaded" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping test file upload" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Display Results
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SUCCESSFUL" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$containerAppUrl = $outputs.containerAppUrl.value
$dicomServiceUrl = $outputs.dicomServiceUrl.value
$dicomScope = $outputs.dicomScope.value
$tokenEndpoint = $outputs.tokenEndpoint.value
$workspaceName = $outputs.healthcareWorkspaceName.value

Write-Host "Orthanc Instance:" -ForegroundColor Cyan
Write-Host "  URL: https://$containerAppUrl"
Write-Host "  Username: $orthancUsername"
Write-Host "  Password: $orthancPassword"
Write-Host ""

Write-Host "DICOM Service:" -ForegroundColor Cyan
Write-Host "  Workspace: $workspaceName"
Write-Host "  URL: $dicomServiceUrl"
Write-Host "  Scope: $dicomScope"
Write-Host ""

Write-Host "OAuth Configuration:" -ForegroundColor Cyan
Write-Host "  Client ID: $oauthClientId"
Write-Host "  Token Endpoint: $tokenEndpoint"
Write-Host "  Permissions: DICOM Data Owner (assigned)"
Write-Host ""

Write-Host "Container Registry:" -ForegroundColor Cyan
Write-Host "  Name: $containerRegistryName"
Write-Host "  Image: $containerImage"
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Wait 2-3 minutes for Container App to start"
Write-Host "  2. Open Orthanc: https://$containerAppUrl"
Write-Host "  3. Log in with the credentials above"
Write-Host "  4. Navigate to DICOMweb servers"
Write-Host "  5. Test connection to 'azure-dicom'"
Write-Host ""

Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  View logs: az containerapp logs show --name orthanc-$environmentName-app --resource-group $resourceGroup --follow"
Write-Host ""

Write-Host "Configuration saved to: $OutputFile"
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
