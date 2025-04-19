#!/usr/bin/env python3
"""
Monitoring utility for Crawl4AI system health and performance
"""

import os
import time
import logging
import psutil
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

logger = logging.getLogger('crawler_monitor')

class SystemMonitor:
    """Monitor system resources during crawling"""
    
    def __init__(self, 
                stats_dir: str = None,
                memory_threshold: float = 85.0,
                cpu_threshold: float = 90.0):
        """
        Initialize system monitor
        
        Args:
            stats_dir: Directory to store stats files
            memory_threshold: Memory usage threshold percentage
            cpu_threshold: CPU usage threshold percentage
        """
        # Set stats directory
        if stats_dir is None:
            self.stats_dir = os.path.join(os.getcwd(), "stats")
        else:
            self.stats_dir = stats_dir
            
        # Create stats directory if it doesn't exist
        os.makedirs(self.stats_dir, exist_ok=True)
        
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.stats_file = os.path.join(self.stats_dir, f"crawler_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Initialize stats
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "sources_processed": 0,
            "stories_found": 0,
            "errors": 0,
            "memory_usage": [],
            "cpu_usage": [],
            "status": "running"
        }
        
        # Start monitoring task
        self.stop_monitoring = False
        self.monitoring_task = None
        
    async def start_monitoring(self, interval: float = 5.0):
        """
        Start monitoring system resources
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.monitoring_task = asyncio.create_task(self._monitor_resources(interval))
        logger.info(f"System monitoring started, stats will be saved to {self.stats_file}")
        
    async def _monitor_resources(self, interval: float):
        """
        Monitor system resources at regular intervals
        
        Args:
            interval: Monitoring interval in seconds
        """
        while not self.stop_monitoring:
            try:
                # Get current memory usage
                memory_info = psutil.virtual_memory()
                memory_percent = memory_info.percent
                
                # Get current CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Record stats
                timestamp = datetime.now().isoformat()
                self.stats["memory_usage"].append({
                    "timestamp": timestamp,
                    "percent": memory_percent
                })
                
                self.stats["cpu_usage"].append({
                    "timestamp": timestamp,
                    "percent": cpu_percent
                })
                
                # Check thresholds
                if memory_percent > self.memory_threshold:
                    logger.warning(f"Memory usage high: {memory_percent:.1f}% (threshold: {self.memory_threshold:.1f}%)")
                    
                if cpu_percent > self.cpu_threshold:
                    logger.warning(f"CPU usage high: {cpu_percent:.1f}% (threshold: {self.cpu_threshold:.1f}%)")
                
                # Save stats periodically
                self._save_stats()
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring task: {str(e)}")
                await asyncio.sleep(interval)
    
    def update_stats(self, 
                    sources_processed: Optional[int] = None,
                    stories_found: Optional[int] = None,
                    errors: Optional[int] = None):
        """
        Update crawler stats
        
        Args:
            sources_processed: Number of sources processed
            stories_found: Number of stories found
            errors: Number of errors
        """
        if sources_processed is not None:
            self.stats["sources_processed"] = sources_processed
            
        if stories_found is not None:
            self.stats["stories_found"] = stories_found
            
        if errors is not None:
            self.stats["errors"] = errors
            
        # Update duration
        now = datetime.now()
        start_time = datetime.fromisoformat(self.stats["start_time"])
        self.stats["duration_seconds"] = (now - start_time).total_seconds()
    
    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {str(e)}")
    
    async def stop(self):
        """Stop monitoring and save final stats"""
        self.stop_monitoring = True
        
        if self.monitoring_task:
            # Wait for monitoring task to finish
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            
        # Update end time and status
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["status"] = "completed"
        
        # Save final stats
        self._save_stats()
        
        logger.info(f"Monitoring stopped, stats saved to {self.stats_file}")
        
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of stats
        
        Returns:
            Summary dictionary
        """
        if not self.stats["memory_usage"] or not self.stats["cpu_usage"]:
            return {
                "sources_processed": self.stats["sources_processed"],
                "stories_found": self.stats["stories_found"],
                "errors": self.stats["errors"],
                "duration_seconds": self.stats["duration_seconds"]
            }
            
        # Calculate memory and CPU averages
        memory_values = [entry["percent"] for entry in self.stats["memory_usage"]]
        cpu_values = [entry["percent"] for entry in self.stats["cpu_usage"]]
        
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        
        return {
            "sources_processed": self.stats["sources_processed"],
            "stories_found": self.stats["stories_found"],
            "errors": self.stats["errors"],
            "duration_seconds": self.stats["duration_seconds"],
            "avg_memory_usage": avg_memory,
            "max_memory_usage": max_memory,
            "avg_cpu_usage": avg_cpu,
            "max_cpu_usage": max_cpu
        }


class CrawlStats:
    """Track and analyze crawler statistics over time"""
    
    def __init__(self, stats_dir: str = None):
        """
        Initialize crawl stats tracker
        
        Args:
            stats_dir: Directory where stats files are stored
        """
        # Set stats directory
        if stats_dir is None:
            self.stats_dir = os.path.join(os.getcwd(), "stats")
        else:
            self.stats_dir = stats_dir
            
        self.latest_stats = None
    
    def get_latest_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get latest stats file
        
        Returns:
            Latest stats or None if no stats found
        """
        try:
            # Get all stats files
            stats_files = list(Path(self.stats_dir).glob("crawler_stats_*.json"))
            
            if not stats_files:
                return None
                
            # Sort by modification time (newest first)
            stats_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Read latest stats file
            with open(stats_files[0], 'r') as f:
                self.latest_stats = json.load(f)
                
            return self.latest_stats
        except Exception as e:
            logger.error(f"Error reading latest stats: {str(e)}")
            return None
    
    def get_stats_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get stats history for the past N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of stats dictionaries
        """
        try:
            # Get all stats files
            stats_files = list(Path(self.stats_dir).glob("crawler_stats_*.json"))
            
            if not stats_files:
                return []
                
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter files by modification time
            recent_files = [f for f in stats_files if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_date]
            
            # Sort by modification time (oldest first)
            recent_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Read stats from files
            stats_history = []
            for file_path in recent_files:
                try:
                    with open(file_path, 'r') as f:
                        stats = json.load(f)
                        stats_history.append(stats)
                except Exception as e:
                    logger.error(f"Error reading stats file {file_path}: {str(e)}")
                    continue
                    
            return stats_history
        except Exception as e:
            logger.error(f"Error reading stats history: {str(e)}")
            return []
    
    def analyze_performance(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze crawler performance over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance metrics
        """
        stats_history = self.get_stats_history(days)
        
        if not stats_history:
            return {
                "data_available": False,
                "message": "No historical data available for analysis"
            }
            
        # Calculate metrics
        total_runs = len(stats_history)
        
        # Stories found
        total_stories = sum(stats.get("stories_found", 0) for stats in stats_history)
        avg_stories_per_run = total_stories / total_runs if total_runs > 0 else 0
        
        # Errors
        total_errors = sum(stats.get("errors", 0) for stats in stats_history)
        avg_errors_per_run = total_errors / total_runs if total_runs > 0 else 0
        error_rate = total_errors / (total_errors + total_stories) if (total_errors + total_stories) > 0 else 0
        
        # Duration
        durations = [stats.get("duration_seconds", 0) for stats in stats_history]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Memory usage
        memory_peaks = []
        for stats in stats_history:
            memory_usage = stats.get("memory_usage", [])
            if memory_usage:
                peak = max(entry.get("percent", 0) for entry in memory_usage)
                memory_peaks.append(peak)
                
        avg_memory_peak = sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0
        
        # Success rate
        success_rate = 1.0 - error_rate
        
        return {
            "data_available": True,
            "total_runs": total_runs,
            "total_stories": total_stories,
            "avg_stories_per_run": avg_stories_per_run,
            "total_errors": total_errors,
            "avg_errors_per_run": avg_errors_per_run,
            "error_rate": error_rate,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
            "avg_memory_peak": avg_memory_peak,
            "time_period_days": days
        }


# Create singleton instances
system_monitor = None
crawl_stats = CrawlStats()

def get_system_monitor() -> SystemMonitor:
    """
    Get the system monitor instance, creating it if necessary
    
    Returns:
        SystemMonitor instance
    """
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitor()
    return system_monitor

def get_crawl_stats() -> CrawlStats:
    """
    Get the crawl stats instance
    
    Returns:
        CrawlStats instance
    """
    return crawl_stats
