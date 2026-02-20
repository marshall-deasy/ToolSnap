"""
FolderSync Engine
Handles all file operations: copy, rename, delete.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from config import TIMESTAMP_FORMAT, OLD_FOLDER_SUFFIX
from models import ToolFolder, FolderInfo


class SyncOperation:
    """Base class for sync operations with progress tracking."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            progress_callback: Function to call with progress messages
        """
        self.progress_callback = progress_callback
        self.errors: list[str] = []
    
    def _report_progress(self, message: str) -> None:
        """Report progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(message)
    
    def _report_error(self, error: str) -> None:
        """Record an error."""
        self.errors.append(error)
        self._report_progress(f"ERROR: {error}")


class FolderCopier(SyncOperation):
    """Handles copying folders."""
    
    def copy_folder(self, source: Path, destination: Path) -> bool:
        """
        Copy a folder from source to destination.
        Source folder remains unchanged.
        
        Args:
            source: Source folder path (will NOT be modified)
            destination: Destination folder path (will be created/overwritten)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._report_progress(f"Copying {source.name} to {destination.parent.name}...")
            
            # Verify source exists
            if not source.exists():
                self._report_error(f"Source folder does not exist: {source}")
                return False
            
            # Ensure parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the folder (source remains unchanged)
            shutil.copytree(source, destination, dirs_exist_ok=True)
            
            # Verify source still exists after copy
            if not source.exists():
                self._report_error(f"WARNING: Source folder disappeared after copy: {source}")
                return False
            
            self._report_progress(f"✓ Copied {source.name}")
            return True
            
        except Exception as e:
            self._report_error(f"Failed to copy {source.name}: {e}")
            return False


class FolderRenamer(SyncOperation):
    """Handles renaming folders."""
    
    def rename_folder_old(self, folder: Path) -> Optional[Path]:
        """
        Rename a folder with .OLD_{timestamp} suffix.
        
        Args:
            folder: Folder to rename
            
        Returns:
            New path if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
            suffix = OLD_FOLDER_SUFFIX.format(timestamp=timestamp)
            new_path = folder.parent / (folder.name + suffix)
            
            self._report_progress(f"Renaming {folder.name} to {new_path.name}...")
            
            folder.rename(new_path)
            
            self._report_progress(f"✓ Renamed to {new_path.name}")
            return new_path
            
        except Exception as e:
            self._report_error(f"Failed to rename {folder.name}: {e}")
            return None


class FolderDeleter(SyncOperation):
    """Handles deleting folders."""
    
    def delete_folder(self, folder: Path) -> bool:
        """
        Delete a folder and all its contents.
        
        Args:
            folder: Folder to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._report_progress(f"Deleting {folder.name}...")
            
            shutil.rmtree(folder)
            
            self._report_progress(f"✓ Deleted {folder.name}")
            return True
            
        except Exception as e:
            self._report_error(f"Failed to delete {folder.name}: {e}")
            return False


class SyncEngine:
    """
    Main sync engine that coordinates folder operations.
    """
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            progress_callback: Function to call with progress messages
        """
        self.copier = FolderCopier(progress_callback)
        self.renamer = FolderRenamer(progress_callback)
        self.deleter = FolderDeleter(progress_callback)
        self.progress_callback = progress_callback
    
    def distribute_newest(
        self,
        tool: ToolFolder,
        source_location_idx: int,
        location_paths: list[Path],
        rename_old: bool = True
    ) -> dict[str, int]:
        """
        Distribute the newest version of a tool to all locations.
        
        Args:
            tool: ToolFolder object
            source_location_idx: Index of location with newest version
            location_paths: List of all location paths
            rename_old: If True, rename old folders; if False, delete them
            
        Returns:
            Dictionary with counts: {'renamed': N, 'deleted': N, 'copied': N, 'skipped': N}
        """
        stats = {'renamed': 0, 'deleted': 0, 'copied': 0, 'skipped': 0, 'errors': 0}
        
        if source_location_idx not in tool.locations:
            return stats
        
        source_folder = tool.locations[source_location_idx].path
        
        # Process each location
        for location_idx, location_path in enumerate(location_paths):
            # Skip source location
            if location_idx == source_location_idx:
                stats['skipped'] += 1
                continue
            
            destination = location_path / tool.name
            
            # Safety check: ensure we're not trying to copy to source location
            if destination.resolve() == source_folder.resolve():
                stats['skipped'] += 1
                continue
            
            # Check if destination exists
            if destination.exists():
                # Handle existing folder
                if rename_old:
                    renamed_path = self.renamer.rename_folder_old(destination)
                    if renamed_path:
                        stats['renamed'] += 1
                    else:
                        stats['errors'] += 1
                        continue
                else:
                    if self.deleter.delete_folder(destination):
                        stats['deleted'] += 1
                    else:
                        stats['errors'] += 1
                        continue
            
            # Copy newest version
            if self.copier.copy_folder(source_folder, destination):
                stats['copied'] += 1
            else:
                stats['errors'] += 1
        
        return stats
    
    def replace_single(
        self,
        source_folder: Path,
        destination_folder: Path,
        rename_old: bool = True
    ) -> bool:
        """
        Replace a single folder with another.
        
        Args:
            source_folder: Source folder to copy from
            destination_folder: Destination folder (will be replaced)
            rename_old: If True, rename old; if False, delete
            
        Returns:
            True if successful, False otherwise
        """
        # Safety check: don't copy folder to itself
        if source_folder.resolve() == destination_folder.resolve():
            self.copier._report_progress(f"Skipped - source and destination are the same")
            return True
        
        # Handle existing destination
        if destination_folder.exists():
            if rename_old:
                if not self.renamer.rename_folder_old(destination_folder):
                    return False
            else:
                if not self.deleter.delete_folder(destination_folder):
                    return False
        
        # Copy source to destination
        return self.copier.copy_folder(source_folder, destination_folder)
    
    def copy_to_missing(
        self,
        source_folder: Path,
        destination_location: Path,
        tool_name: str
    ) -> bool:
        """
        Copy a tool folder to a location where it's missing.
        
        Args:
            source_folder: Source folder to copy from
            destination_location: Destination location path
            tool_name: Name of the tool folder
            
        Returns:
            True if successful, False otherwise
        """
        destination = destination_location / tool_name
        return self.copier.copy_folder(source_folder, destination)
    
    def get_all_errors(self) -> list[str]:
        """Get all errors from all operations."""
        return (
            self.copier.errors +
            self.renamer.errors +
            self.deleter.errors
        )
