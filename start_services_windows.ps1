# Function to install Docker
function Install-Docker {
    Write-Output "Downloading Docker Desktop for Windows..."
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    # Use System.Net.WebClient for faster downloads
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($dockerUrl, $dockerInstaller)
    
    Write-Output "Installing Docker Desktop..."
    Start-Process -FilePath $dockerInstaller -Wait
    
    Write-Output "Docker Desktop installation completed."
}

# Function to wait for Docker service to be ready
function Wait-ForDocker {
    Write-Output "Waiting for Docker daemon to be ready..."
    while (-not (Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 1
    }
    
    while (-not (docker info | Out-Null -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 1
    }
    
    Write-Output "Docker daemon is ready."
}

# Function to start Docker service
function Start-Docker {
    Write-Output "Starting Docker Desktop..."
    # Start Docker Desktop executable without arguments
    Start-Process -FilePath "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -Wait
    
    # Check if Docker service is running
    if ((Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue).Status -eq "Running") {
        Write-Output "Docker service is running."
    } else {
        Write-Output "Docker service failed to start."
    }
}

# Check if Docker is installed
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Output "Docker is already installed. Skipping Docker installation."
} else {
    Write-Output "Docker is not installed. Installing Docker..."
    Install-Docker
}

# Start Docker service
Start-Docker

# Wait for Docker to be fully ready
Wait-ForDocker

# Determine the directory of the current script
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent

# Ensure docker-compose is present in the same directory as the script
$dockerComposePath = Join-Path -Path $scriptDir -ChildPath "docker-compose.yml"

if (-Not (Test-Path -Path $dockerComposePath)) {
    Write-Output "docker-compose.yml not found in the script directory."
    exit 1
}

# Start Docker containers using docker-compose
Write-Output "Starting up Docker containers with docker-compose..."
& "docker-compose" -f $dockerComposePath up -d

Write-Output "Setup completed successfully!"
