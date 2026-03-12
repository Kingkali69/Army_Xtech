#!/usr/bin/env python3
"""
GhostHUD Cross-Platform Skill
Main orchestrator for deploying mesh nodes across different platforms
"""

import os
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrossPlatformSkill:
    """
    Cross-platform deployment orchestrator for GhostHUD mesh networking system.
    Generates platform-specific templates and deployment configurations.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the cross-platform skill

        Args:
            base_dir: Base directory for the project (defaults to current directory)
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.templates_dir = self.base_dir / "templates"
        self.supported_platforms = ['linux', 'windows', 'android']

        # Platform detection
        self.current_platform = self._detect_platform()

        logger.info(f"CrossPlatformSkill initialized on {self.current_platform}")

    def _detect_platform(self) -> str:
        """Detect the current platform"""
        system = platform.system().lower()

        if system == 'linux':
            # Check if running in Termux (Android)
            if os.path.exists('/data/data/com.termux'):
                return 'android'
            return 'linux'
        elif system == 'windows':
            return 'windows'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'unknown'

    def generate_template(self, target_platform: str, output_dir: Optional[str] = None) -> Path:
        """
        Generate platform-specific deployment template

        Args:
            target_platform: Target platform (linux, windows, android)
            output_dir: Output directory for the template (defaults to templates/<platform>)

        Returns:
            Path to the generated template directory

        Raises:
            ValueError: If the target platform is not supported
        """
        if target_platform not in self.supported_platforms:
            raise ValueError(
                f"Unsupported platform: {target_platform}. "
                f"Supported: {', '.join(self.supported_platforms)}"
            )

        # Determine output directory
        if output_dir:
            template_dir = Path(output_dir)
        else:
            template_dir = self.templates_dir / target_platform

        # Create template directory
        template_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {target_platform} template at {template_dir}")

        # Generate platform-specific files
        if target_platform == 'linux':
            self._generate_linux_template(template_dir)
        elif target_platform == 'windows':
            self._generate_windows_template(template_dir)
        elif target_platform == 'android':
            self._generate_android_template(template_dir)

        logger.info(f"Template generated successfully at {template_dir}")
        return template_dir

    def _generate_linux_template(self, output_dir: Path):
        """Generate Linux deployment template"""
        logger.info("Generating Linux template...")

        # Copy Docker files
        docker_src = self.base_dir / "docker"
        docker_dst = output_dir / "docker"
        shutil.copytree(docker_src, docker_dst, dirs_exist_ok=True)

        # Copy mesh node
        node_src = self.base_dir / "node"
        node_dst = output_dir / "node"
        shutil.copytree(node_src, node_dst, dirs_exist_ok=True)

        # Create deployment script
        deploy_script = output_dir / "deploy_linux.sh"
        deploy_script.write_text('''#!/bin/bash

# GhostHUD Mesh Node - Linux Deployment Script

set -e

echo "GhostHUD Mesh Node - Linux Deployment"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -f docker/mesh_node.Dockerfile -t ghosthud-mesh-node:latest .

echo ""
echo "Docker image built successfully!"
echo ""
echo "To run the mesh node:"
echo "  docker run -d -p 5000:5000 --name mesh-node ghosthud-mesh-node:latest"
echo ""
echo "Or use docker-compose:"
echo "  cd docker && docker-compose up -d"
echo ""
''')
        deploy_script.chmod(0o755)

        # Create systemd service file
        service_file = output_dir / "ghosthud-mesh.service"
        service_file.write_text('''[Unit]
Description=GhostHUD Mesh Node
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/bin/docker run --rm --name ghosthud-mesh-node -p 5000:5000 ghosthud-mesh-node:latest
ExecStop=/usr/bin/docker stop ghosthud-mesh-node

[Install]
WantedBy=multi-user.target
''')

        # Create README
        readme = output_dir / "README.md"
        readme.write_text('''# GhostHUD Mesh Node - Linux Deployment

## Prerequisites
- Docker and Docker Compose
- Linux system (Ubuntu, Debian, CentOS, etc.)

## Quick Start

### Using Docker
1. Build the image:
   ```bash
   ./deploy_linux.sh
   ```

2. Run the container:
   ```bash
   docker run -d -p 5000:5000 --name mesh-node ghosthud-mesh-node:latest
   ```

### Using Docker Compose
```bash
cd docker
docker-compose up -d
```

### Using Systemd
1. Copy service file:
   ```bash
   sudo cp ghosthud-mesh.service /etc/systemd/system/
   ```

2. Enable and start:
   ```bash
   sudo systemctl enable ghosthud-mesh
   sudo systemctl start ghosthud-mesh
   ```

## Configuration
Edit `docker/.env` for configuration options.

## Accessing the Node
- Health check: http://localhost:5000/health
- API: http://localhost:5000/node/info
''')

        logger.info("Linux template generated")

    def _generate_windows_template(self, output_dir: Path):
        """Generate Windows deployment template"""
        logger.info("Generating Windows template...")

        # Copy Docker files
        docker_src = self.base_dir / "docker"
        docker_dst = output_dir / "docker"
        shutil.copytree(docker_src, docker_dst, dirs_exist_ok=True)

        # Copy mesh node
        node_src = self.base_dir / "node"
        node_dst = output_dir / "node"
        shutil.copytree(node_src, node_dst, dirs_exist_ok=True)

        # Create deployment script (PowerShell)
        deploy_script = output_dir / "deploy_windows.ps1"
        deploy_script.write_text('''# GhostHUD Mesh Node - Windows Deployment Script

Write-Host "GhostHUD Mesh Node - Windows Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Green
docker build -f docker/mesh_node.Dockerfile -t ghosthud-mesh-node:latest .

Write-Host ""
Write-Host "Docker image built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the mesh node:" -ForegroundColor Yellow
Write-Host "  docker run -d -p 5000:5000 --name mesh-node ghosthud-mesh-node:latest" -ForegroundColor White
Write-Host ""
Write-Host "Or use docker-compose:" -ForegroundColor Yellow
Write-Host "  cd docker" -ForegroundColor White
Write-Host "  docker-compose up -d" -ForegroundColor White
Write-Host ""
''')

        # Create batch file wrapper
        batch_script = output_dir / "deploy_windows.bat"
        batch_script.write_text('''@echo off
REM GhostHUD Mesh Node - Windows Deployment Batch Script

echo GhostHUD Mesh Node - Windows Deployment
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Build Docker image
echo Building Docker image...
docker build -f docker\\mesh_node.Dockerfile -t ghosthud-mesh-node:latest .

echo.
echo Docker image built successfully!
echo.
echo To run the mesh node:
echo   docker run -d -p 5000:5000 --name mesh-node ghosthud-mesh-node:latest
echo.
pause
''')

        # Create README
        readme = output_dir / "README.md"
        readme.write_text('''# GhostHUD Mesh Node - Windows Deployment

## Prerequisites
- Docker Desktop for Windows
- Windows 10/11 with WSL2

## Quick Start

### Using PowerShell
1. Run deployment script:
   ```powershell
   .\\deploy_windows.ps1
   ```

### Using Command Prompt
1. Run batch file:
   ```cmd
   deploy_windows.bat
   ```

### Using Docker Compose
```powershell
cd docker
docker-compose up -d
```

## Configuration
Edit `docker\\.env` for configuration options.

## Accessing the Node
- Health check: http://localhost:5000/health
- API: http://localhost:5000/node/info

## Troubleshooting
- Ensure Docker Desktop is running
- Check WSL2 is enabled
- Verify port 5000 is not in use
''')

        logger.info("Windows template generated")

    def _generate_android_template(self, output_dir: Path):
        """Generate Android (Termux) deployment template"""
        logger.info("Generating Android template...")

        # Copy Termux setup script
        termux_src = self.base_dir / "termux"
        termux_dst = output_dir / "termux"
        shutil.copytree(termux_src, termux_dst, dirs_exist_ok=True)

        # Copy mesh node
        node_src = self.base_dir / "node" / "mesh_node.py"
        node_dst = output_dir / "mesh_node.py"
        shutil.copy(node_src, node_dst)

        # Create quick start script
        quick_start = output_dir / "INSTALL.txt"
        quick_start.write_text('''GhostHUD Mesh Node - Android (Termux) Installation
==================================================

Prerequisites:
--------------
1. Install Termux from F-Droid or Google Play Store
2. Grant storage permissions to Termux

Installation Steps:
------------------
1. Open Termux

2. Copy this folder to Termux storage:
   Copy the entire android template folder to:
   /storage/emulated/0/Download/

3. In Termux, navigate to the folder:
   cd ~/storage/downloads/android

4. Run the setup script:
   bash termux/termux_mesh_setup.sh

5. Wait for installation to complete (may take 10-15 minutes)

6. Start the mesh node:
   cd ~/ghosthud-mesh
   ./start_mesh_node.sh

Quick Start:
-----------
After installation:
- Start: ./service.sh start
- Stop: ./service.sh stop
- Status: ./service.sh status
- Logs: ./service.sh logs

For detailed instructions, see README.md
''')

        # Create README
        readme = output_dir / "README.md"
        readme.write_text('''# GhostHUD Mesh Node - Android (Termux) Deployment

## Prerequisites
- Android device (Android 7.0+)
- Termux app (install from F-Droid)
- ~500MB free storage

## Installation

### Method 1: Automatic Setup
1. Copy this folder to your Android device
2. Open Termux
3. Navigate to the folder
4. Run: `bash termux/termux_mesh_setup.sh`

### Method 2: Manual Setup
See INSTALL.txt for detailed instructions

## Usage

### Start the mesh node
```bash
cd ~/ghosthud-mesh
./start_mesh_node.sh
```

### Service management
```bash
./service.sh start    # Start in background
./service.sh stop     # Stop service
./service.sh restart  # Restart service
./service.sh status   # Check status
./service.sh logs     # View logs
```

## Configuration
Edit `config.env` in the installation directory

## Accessing the Node
Find your device's IP address:
```bash
ifconfig wlan0 | grep inet
```

Access the node:
- Health check: http://<device-ip>:5000/health
- API: http://<device-ip>:5000/node/info

## Troubleshooting
- Ensure Termux has storage permissions
- Check if Python is installed: `python --version`
- View logs: `./service.sh logs`

## Auto-start on Boot
The node is configured to auto-start on device boot.
To disable, remove: `~/.termux/boot/ghosthud-mesh.sh`
''')

        logger.info("Android template generated")

    def deploy(self, platform: Optional[str] = None, **kwargs):
        """
        Deploy mesh node on the specified platform

        Args:
            platform: Target platform (defaults to current platform)
            **kwargs: Platform-specific deployment options
        """
        target_platform = platform or self.current_platform

        if target_platform not in self.supported_platforms:
            raise ValueError(f"Cannot deploy on unsupported platform: {target_platform}")

        logger.info(f"Deploying mesh node on {target_platform}...")

        # Generate template first
        template_dir = self.generate_template(target_platform)

        # Platform-specific deployment
        if target_platform == 'linux':
            self._deploy_linux(template_dir, **kwargs)
        elif target_platform == 'windows':
            self._deploy_windows(template_dir, **kwargs)
        elif target_platform == 'android':
            self._deploy_android(template_dir, **kwargs)

        logger.info("Deployment complete!")

    def _deploy_linux(self, template_dir: Path, **kwargs):
        """Deploy on Linux"""
        logger.info("Deploying on Linux...")
        # Run deployment script
        script = template_dir / "deploy_linux.sh"
        if script.exists():
            subprocess.run([str(script)], cwd=template_dir, check=True)

    def _deploy_windows(self, template_dir: Path, **kwargs):
        """Deploy on Windows"""
        logger.info("Deploying on Windows...")
        # Run PowerShell script
        script = template_dir / "deploy_windows.ps1"
        if script.exists():
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                cwd=template_dir,
                check=True
            )

    def _deploy_android(self, template_dir: Path, **kwargs):
        """Deploy on Android"""
        logger.info("Deploying on Android...")
        # Run setup script
        script = template_dir / "termux" / "termux_mesh_setup.sh"
        if script.exists():
            subprocess.run(["bash", str(script)], cwd=template_dir, check=True)

    def list_platforms(self) -> List[str]:
        """List all supported platforms"""
        return self.supported_platforms.copy()

    def get_platform_info(self) -> Dict[str, str]:
        """Get information about the current platform"""
        return {
            'current': self.current_platform,
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'supported': self.supported_platforms
        }


def main():
    """CLI interface for the cross-platform skill"""
    import argparse

    parser = argparse.ArgumentParser(
        description='GhostHUD Cross-Platform Mesh Deployment Tool'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate platform template')
    gen_parser.add_argument(
        'platform',
        choices=['linux', 'windows', 'android'],
        help='Target platform'
    )
    gen_parser.add_argument(
        '-o', '--output',
        help='Output directory'
    )

    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy mesh node')
    deploy_parser.add_argument(
        'platform',
        nargs='?',
        choices=['linux', 'windows', 'android'],
        help='Target platform (defaults to current)'
    )

    # Info command
    subparsers.add_parser('info', help='Show platform information')

    # List command
    subparsers.add_parser('list', help='List supported platforms')

    args = parser.parse_args()

    skill = CrossPlatformSkill()

    if args.command == 'generate':
        template_dir = skill.generate_template(args.platform, args.output)
        print(f"Template generated at: {template_dir}")

    elif args.command == 'deploy':
        skill.deploy(args.platform)

    elif args.command == 'info':
        info = skill.get_platform_info()
        print("Platform Information:")
        print(f"  Current: {info['current']}")
        print(f"  System: {info['system']}")
        print(f"  Release: {info['release']}")
        print(f"  Machine: {info['machine']}")
        print(f"  Supported: {', '.join(info['supported'])}")

    elif args.command == 'list':
        platforms = skill.list_platforms()
        print("Supported Platforms:")
        for platform in platforms:
            print(f"  - {platform}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
