"""
Conda environment management for EnvHud.

Detects current environment and provides switching functionality.
"""

import subprocess
import os
from typing import List, Optional


class EnvManager:
    """Manages conda environment detection and switching."""

    def __init__(self):
        """Initialize environment manager."""
        pass

    def get_active_env(self) -> str:
        """
        Get the currently active conda environment.

        Returns:
            Name of active environment (e.g., 'base', 'trading')
        """
        # Check CONDA_DEFAULT_ENV environment variable
        env_name = os.environ.get('CONDA_DEFAULT_ENV')
        
        if env_name:
            return env_name
        
        # Fallback: try to detect from conda info
        try:
            result = subprocess.run(
                ['conda', 'info', '--envs'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                # Look for line with asterisk (active env)
                for line in result.stdout.split('\n'):
                    if '*' in line:
                        parts = line.split()
                        if parts:
                            return parts[0]
        except Exception:
            pass
        
        # Default to 'base' if can't detect
        return 'base'

    def list_environments(self) -> List[str]:
        """
        List all available conda environments.

        Returns:
            List of environment names
        """
        envs = []
        
        try:
            result = subprocess.run(
                ['conda', 'env', 'list'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # Skip comments and empty lines
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Extract environment name (first column)
                    parts = line.split()
                    if parts:
                        env_name = parts[0]
                        if env_name not in envs:
                            envs.append(env_name)
        
        except Exception:
            # Fallback to common environments
            envs = ['base', 'trading', 'chatbots']
        
        return sorted(envs)

    def switch_environment(self, env_name: str) -> bool:
        """
        Switch to a different conda environment.

        Opens a new terminal window with the environment activated.

        Args:
            env_name: Name of environment to switch to

        Returns:
            True if command executed successfully
        """
        if not env_name or env_name.strip() == '':
            return False
        
        try:
            # Windows: open new cmd window with conda environment activated
            cmd = f'start cmd /k "conda activate {env_name}"'
            
            # Use Popen with minimal flags to avoid loops
            subprocess.Popen(
                cmd,
                shell=True,
            )
            
            return True
            
        except Exception as e:
            print(f"Error switching environment: {e}")
            return False
