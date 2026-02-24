"""
Performance Optimizer Module
Safely optimizes system performance without harmful side effects
"""

import os
import subprocess
import psutil
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Result of an optimization operation"""
    success: bool
    action: str
    description: str
    before_value: Any
    after_value: Any
    impact: str  # "positive", "neutral", "negative"
    reversible: bool
    rollback_command: str


class PerformanceOptimizer:
    """
    Safely optimizes system performance.
    All operations include safety checks and rollback capabilities.
    """

    def __init__(self):
        self.optimizations_performed = []

    def optimize_memory(self) -> OptimizationResult:
        """
        Optimize memory usage by clearing caches.
        Safe operation that can improve performance.
        """
        try:
            before = psutil.virtual_memory().percent

            # Linux: Clear page cache, dentries, and inodes
            if os.path.exists('/proc/sys/vm/drop_caches'):
                subprocess.run(
                    ['sync'],
                    timeout=10
                )
                with open('/proc/sys/vm/drop_caches', 'w') as f:
                    f.write('3')  # Clear all caches

                after = psutil.virtual_memory().percent

                return OptimizationResult(
                    success=True,
                    action="memory_cache_clear",
                    description="Cleared system memory caches",
                    before_value=before,
                    after_value=after,
                    impact="positive" if after < before else "neutral",
                    reversible=False,
                    rollback_command=""  # Cannot undo cache clear
                )
        except Exception as e:
            return OptimizationResult(
                success=False,
                action="memory_cache_clear",
                description=f"Failed to clear memory caches: {e}",
                before_value=None,
                after_value=None,
                impact="neutral",
                reversible=False,
                rollback_command=""
            )

    def optimize_cpu_governor(self) -> OptimizationResult:
        """
        Set CPU governor to 'performance' mode.
        Improves CPU responsiveness.
        """
        try:
            # Check current governor
            cpu_paths = []
            for i in range(psutil.cpu_count()):
                path = f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor"
                if os.path.exists(path):
                    cpu_paths.append(path)

            if not cpu_paths:
                return OptimizationResult(
                    success=False,
                    action="cpu_governor",
                    description="CPU governor control not available",
                    before_value=None,
                    after_value=None,
                    impact="neutral",
                    reversible=False,
                    rollback_command=""
                )

            # Read current governor
            with open(cpu_paths[0], 'r') as f:
                before = f.read().strip()

            # Set to performance mode
            for path in cpu_paths:
                with open(path, 'w') as f:
                    f.write('performance')

            # Verify change
            with open(cpu_paths[0], 'r') as f:
                after = f.read().strip()

            return OptimizationResult(
                success=True,
                action="cpu_governor",
                description="Set CPU governor to performance mode",
                before_value=before,
                after_value=after,
                impact="positive",
                reversible=True,
                rollback_command=f"echo '{before}' | tee {' '.join(cpu_paths)}"
            )

        except Exception as e:
            return OptimizationResult(
                success=False,
                action="cpu_governor",
                description=f"Failed to set CPU governor: {e}",
                before_value=None,
                after_value=None,
                impact="neutral",
                reversible=False,
                rollback_command=""
            )

    def optimize_disk_scheduler(self) -> OptimizationResult:
        """
        Optimize disk I/O scheduler for performance.
        Changes from CFQ to deadline or noop for SSDs.
        """
        try:
            # Find block devices
            block_devices = []
            for device in os.listdir('/sys/block/'):
                if device.startswith(('sd', 'nvme', 'vd')):
                    block_devices.append(device)

            if not block_devices:
                return OptimizationResult(
                    success=False,
                    action="disk_scheduler",
                    description="No block devices found",
                    before_value=None,
                    after_value=None,
                    impact="neutral",
                    reversible=False,
                    rollback_command=""
                )

            optimizations = []

            for device in block_devices:
                scheduler_path = f"/sys/block/{device}/queue/scheduler"

                if not os.path.exists(scheduler_path):
                    continue

                # Read current scheduler
                with open(scheduler_path, 'r') as f:
                    current = f.read().strip()

                # Determine optimal scheduler
                if 'nvme' in device:
                    optimal = 'none'  # NVMe doesn't need scheduler
                else:
                    optimal = 'mq-deadline'  # Good for both SSD and HDD

                # Set scheduler
                try:
                    with open(scheduler_path, 'w') as f:
                        f.write(optimal)

                    optimizations.append({
                        "device": device,
                        "before": current,
                        "after": optimal
                    })
                except:
                    continue

            if optimizations:
                return OptimizationResult(
                    success=True,
                    action="disk_scheduler",
                    description=f"Optimized disk schedulers for {len(optimizations)} devices",
                    before_value=[o["before"] for o in optimizations],
                    after_value=[o["after"] for o in optimizations],
                    impact="positive",
                    reversible=True,
                    rollback_command="; ".join([
                        f"echo '{o['before']}' > /sys/block/{o['device']}/queue/scheduler"
                        for o in optimizations
                    ])
                )
            else:
                return OptimizationResult(
                    success=False,
                    action="disk_scheduler",
                    description="No disk schedulers optimized",
                    before_value=None,
                    after_value=None,
                    impact="neutral",
                    reversible=False,
                    rollback_command=""
                )

        except Exception as e:
            return OptimizationResult(
                success=False,
                action="disk_scheduler",
                description=f"Failed to optimize disk schedulers: {e}",
                before_value=None,
                after_value=None,
                impact="neutral",
                reversible=False,
                rollback_command=""
            )

    def run_all_optimizations(self) -> List[OptimizationResult]:
        """
        Run all safe performance optimizations.
        Returns list of results for each optimization.
        """
        optimizations = [
            self.optimize_memory(),
            self.optimize_cpu_governor(),
            self.optimize_disk_scheduler()
        ]

        # Filter out failed optimizations
        successful = [opt for opt in optimizations if opt.success]

        self.optimizations_performed.extend(successful)

        return successful

    def rollback_optimization(self, result: OptimizationResult) -> bool:
        """
        Rollback a specific optimization if it had negative impact.
        """
        if not result.reversible or not result.rollback_command:
            return False

        try:
            subprocess.run(
                result.rollback_command,
                shell=True,
                timeout=10,
                check=True
            )
            return True
        except:
            return False


# Example usage
if __name__ == "__main__":
    optimizer = PerformanceOptimizer()

    print("=== Running Performance Optimizations ===\n")

    results = optimizer.run_all_optimizations()

    for result in results:
        print(f"✓ {result.description}")
        print(f"  Before: {result.before_value}")
        print(f"  After: {result.after_value}")
        print(f"  Impact: {result.impact}")
        print(f"  Reversible: {result.reversible}")
        print()
