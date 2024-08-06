#!/bin/bash

# Function to install Docker
install_docker() {
    # Update package list and install prerequisites
    echo "Updating package list and installing prerequisites..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

    # Add Docker's official GPG key
    echo "Adding Docker's official GPG key..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

    # Set up the Docker repository
    echo "Setting up the Docker repository..."
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

    # Update package list again to include Docker packages
    echo "Updating package list to include Docker packages..."
    sudo apt-get update

    # Install Docker
    echo "Installing Docker..."
    sudo apt-get install -y docker-ce

    # Enable Docker service to start on boot
    echo "Enabling Docker service..."
    sudo systemctl enable docker

    # Start Docker service
    echo "Starting Docker service..."
    sudo systemctl start docker
}

# Function to install Docker Compose
install_docker_compose() {
    # Install Docker Compose
    echo "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.16.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # Verify Docker Compose installation
    echo "Verifying Docker Compose installation..."
    docker-compose --version
}

# Function to wait for Docker service to be ready
wait_for_docker() {
    echo "Waiting for Docker daemon to be ready..."
    while ! sudo docker info > /dev/null 2>&1; do
        echo "Docker daemon is not ready yet. Waiting..."
        sleep 1
    done
    echo "Docker daemon is ready."
}

# Check if Docker is installed
if command -v docker > /dev/null 2>&1; then
    echo "Docker is already installed. Skipping Docker installation."
else
    echo "Installing Docker..."
    install_docker
fi

# Check if Docker Compose is installed
if command -v docker-compose > /dev/null 2>&1; then
    echo "Docker Compose is already installed. Skipping Docker Compose installation."
else
    echo "Installing Docker Compose..."
    install_docker_compose
fi


# Function to start Docker on Linux
start_docker_linux() {
    echo "Starting Docker on Linux..."
    sudo systemctl start docker
    if systemctl is-active --quiet docker; then
        echo "Docker is running."
    else
        echo "Docker failed to start."
    fi
}

# Function to start Docker on macOS
start_docker_macos() {
    echo "Starting Docker on macOS..."
    # Open Docker Desktop if not running
    open -a Docker
    # Check if Docker is running
    if pgrep -x "Docker" > /dev/null; then
        echo "Docker is running."
    else
        echo "Docker failed to start."
    fi
}

# Detect the operating system and start Docker
case "$(uname -s)" in
    Linux)
        start_docker_linux
        ;;
    Darwin)
        start_docker_macos
        ;;
    *)
        echo "Unsupported OS."
        exit 1
        ;;
esac

# Wait for Docker to be fully ready
wait_for_docker

# Start up the Docker containers
echo "Starting up Docker containers with docker-compose..."
docker-compose up -d

echo "Setup completed successfully!"
