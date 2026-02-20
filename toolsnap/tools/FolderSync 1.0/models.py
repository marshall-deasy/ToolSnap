"""
FolderSync Data Models
Data structures for folder scanning and comparison.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    """Metadata for a single file."""
    path: Path
    size: int
    modified: datetime
    
    def format_size(self) -> str:
        """Format file size in human-readable format."""
        if self.size < 1024:
            return f"{self.size}B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f}KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f}MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f}GB"
    
    def format_date(self) -> str:
        """Format modification date."""
        return self.modified.strftime('%Y-%m-%d %H:%M')


@dataclass
class FolderInfo:
    """Metadata for a tool folder (e.g., CodeGrep, FileTagger)."""
    path: Path
    newest_file_date: datetime
    total_size: int
    file_count: int
    
    def format_size(self) -> str:
        """Format total folder size."""
        if self.total_size < 1024:
            return f"{self.total_size}B"
        elif self.total_size < 1024 * 1024:
            return f"{self.total_size / 1024:.1f}KB"
        elif self.total_size < 1024 * 1024 * 1024:
            return f"{self.total_size / (1024 * 1024):.1f}MB"
        else:
            return f"{self.total_size / (1024 * 1024 * 1024):.2f}GB"
    
    def format_date(self) -> str:
        """Format newest file date."""
        return self.newest_file_date.strftime('%Y-%m-%d %H:%M')


@dataclass
class ToolFolder:
    """
    Represents a single tool (e.g., CodeGrep) across multiple locations.
    Tracks which location has the newest version.
    """
    name: str
    locations: dict[int, FolderInfo] = field(default_factory=dict)
    
    def add_location(self, location_idx: int, folder_info: FolderInfo) -> None:
        """Add a folder location for this tool."""
        self.locations[location_idx] = folder_info
    
    def get_newest_location(self) -> Optional[int]:
        """
        Find which location has the newest file.
        Returns location index, or None if no locations exist.
        """
        if not self.locations:
            return None
        
        return max(
            self.locations.keys(),
            key=lambda idx: self.locations[idx].newest_file_date
        )
    
    def get_status(self, location_idx: int) -> str:
        """
        Get status for a specific location.
        Returns: 'newest', 'older', 'same', or 'missing'
        """
        if location_idx not in self.locations:
            return 'missing'
        
        newest_idx = self.get_newest_location()
        if newest_idx is None:
            return 'missing'
        
        newest_date = self.locations[newest_idx].newest_file_date
        this_date = self.locations[location_idx].newest_file_date
        
        # Compare timestamps with 1-second tolerance
        time_diff = abs((newest_date - this_date).total_seconds())
        
        if time_diff < 1.0:
            return 'same' if location_idx != newest_idx else 'newest'
        else:
            return 'newest' if location_idx == newest_idx else 'older'
    
    def has_conflicts(self, total_locations: int) -> bool:
        """
        Check if this tool has any conflicts (different versions across locations).
        Returns True if there are older or missing versions.
        
        Args:
            total_locations: Total number of locations being compared
        """
        if len(self.locations) <= 1 and len(self.locations) == total_locations:
            # Only one location and it's the only one = no conflict
            return False
        
        # Check all possible location indices
        for idx in range(total_locations):
            status = self.get_status(idx)
            if status in ('older', 'missing'):
                return True
        
        return False


@dataclass
class ScanResult:
    """
    Complete scan result across all locations.
    Maps tool name to ToolFolder object.
    """
    location_paths: list[Path] = field(default_factory=list)
    tools: dict[str, ToolFolder] = field(default_factory=dict)
    
    def add_tool_location(
        self,
        tool_name: str,
        location_idx: int,
        folder_info: FolderInfo
    ) -> None:
        """Add a tool folder at a specific location."""
        if tool_name not in self.tools:
            self.tools[tool_name] = ToolFolder(name=tool_name)
        
        self.tools[tool_name].add_location(location_idx, folder_info)
    
    def get_conflict_count(self) -> int:
        """Count how many tools have conflicts."""
        total_locations = len(self.location_paths)
        return sum(1 for tool in self.tools.values() if tool.has_conflicts(total_locations))
    
    def get_tools_with_conflicts(self) -> list[ToolFolder]:
        """Get list of tools that have conflicts."""
        total_locations = len(self.location_paths)
        return [tool for tool in self.tools.values() if tool.has_conflicts(total_locations)]
    
    def get_all_tools_sorted(self) -> list[ToolFolder]:
        """Get all tools sorted by name."""
        return sorted(self.tools.values(), key=lambda t: t.name.lower())
