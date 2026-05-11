import os
import shutil
import time
import logging

logger = logging.getLogger(__name__)

def cleanup_runs_directory(runs_dir: str, max_age_days: int = 7, max_disk_usage_pct: float = 80.0) -> list[str]:
    """
    Cleans up old jobs from runs_dir based on age and disk usage.
    Returns a list of paths deleted.
    """
    if not os.path.exists(runs_dir):
        logger.warning(f"Runs directory {runs_dir} does not exist. Skipping cleanup.")
        return []
        
    deleted_paths = []
    
    # Calculate cutoff time for max age
    now = time.time()
    cutoff_time = now - (max_age_days * 86400)
    
    # Collect all job directories
    job_dirs = []
    try:
        for entry in os.listdir(runs_dir):
            full_path = os.path.join(runs_dir, entry)
            if os.path.isdir(full_path):
                stat = os.stat(full_path)
                job_dirs.append((full_path, stat.st_mtime))
    except Exception as e:
        logger.error(f"Failed to list directory {runs_dir}: {e}")
        return []
        
    # Phase 1: Age-based cleanup
    remaining_jobs = []
    for path, mtime in job_dirs:
        if mtime < cutoff_time:
            try:
                shutil.rmtree(path)
                deleted_paths.append(path)
                logger.info(f"Deleted old job directory: {path} (mtime: {mtime})")
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
                remaining_jobs.append((path, mtime))
        else:
            remaining_jobs.append((path, mtime))
            
    # Phase 2: Disk usage cleanup
    try:
        usage = shutil.disk_usage(runs_dir)
        disk_pct = (usage.used / usage.total) * 100.0
    except Exception as e:
        logger.error(f"Failed to get disk usage for {runs_dir}: {e}")
        return deleted_paths
        
    if disk_pct > max_disk_usage_pct:
        logger.warning(f"Disk usage ({disk_pct:.1f}%) exceeds threshold ({max_disk_usage_pct}%). Initiating disk space cleanup.")
        # Sort remaining jobs by mtime (oldest first)
        remaining_jobs.sort(key=lambda x: x[1])
        
        for path, mtime in remaining_jobs:
            try:
                usage = shutil.disk_usage(runs_dir)
                current_disk_pct = (usage.used / usage.total) * 100.0
                if current_disk_pct <= max_disk_usage_pct:
                    break
                    
                shutil.rmtree(path)
                deleted_paths.append(path)
                logger.info(f"Deleted job directory for space: {path} (mtime: {mtime})")
            except Exception as e:
                logger.error(f"Failed to delete {path} during space cleanup: {e}")
                
    return deleted_paths
