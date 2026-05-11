import os
import time
import subprocess
import logging
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkerAutoscaler:
    def __init__(self):
        self.redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        self.redis_client = redis.Redis.from_url(self.redis_url)
        
        self.max_workers = int(os.getenv("AUTOSCALER_MAX_WORKERS", "3"))
        self.min_workers = int(os.getenv("AUTOSCALER_MIN_WORKERS", "1"))
        self.scale_up_threshold = int(os.getenv("AUTOSCALER_QUEUE_THRESHOLD", "10"))
        
        self.queues_to_monitor = [
            "backtest.standard", "backtest.premium", 
            "rl_optimization.standard", "rl_optimization.premium"
        ]
        
        self.check_interval_seconds = int(os.getenv("AUTOSCALER_INTERVAL", "15"))
        self.scale_down_idle_checks = int(os.getenv("AUTOSCALER_IDLE_CHECKS", "12")) # 12 * 15s = 3 minutes
        
        self.current_workers = {} # pid -> process
        self.idle_count = 0

    def start_worker(self):
        if len(self.current_workers) >= self.max_workers:
            logger.info("Maximum workers reached. Cannot scale up further.")
            return
            
        worker_id = f"autoscale_{len(self.current_workers) + 1}"
        cmd = [
            "celery", "-A", "src.worker.celery_app", "worker", 
            "--loglevel=info", "-n", f"{worker_id}@%h", 
            "-Q", "backtest.standard,rl_optimization.standard,backtest.premium,rl_optimization.premium"
        ]
        
        process = subprocess.Popen(cmd)
        self.current_workers[process.pid] = process
        logger.info(f"Scaled up: Started new worker {worker_id} with PID {process.pid}")

    def stop_worker(self):
        if len(self.current_workers) <= self.min_workers:
            logger.info("Minimum workers reached. Cannot scale down further.")
            return
            
        # Stop the last started worker
        pid, process = list(self.current_workers.items())[-1]
        logger.info(f"Scaling down: Stopping worker with PID {pid}")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Worker PID {pid} did not terminate in 5s. Killing it.")
            process.kill()
            process.wait()
        del self.current_workers[pid]

    def get_max_queue_length(self):
        max_len = 0
        try:
            for queue in self.queues_to_monitor:
                q_len = self.redis_client.llen(queue)
                if q_len > max_len:
                    max_len = q_len
            return max_len
        except Exception as e:
            logger.error(f"Error checking Redis queues: {e}")
            return None

    def check_dead_workers(self):
        dead_pids = []
        for pid, process in self.current_workers.items():
            if process.poll() is not None:
                logger.warning(f"Worker PID {pid} died unexpectedly.")
                dead_pids.append(pid)
                
        for pid in dead_pids:
            del self.current_workers[pid]

    def check_and_scale(self):
        self.check_dead_workers()
        queue_length = self.get_max_queue_length()
        
        if queue_length is None:
            # Redis error, do not scale down or reset idle
            return
            
        logger.info(f"Current max queue length: {queue_length}, Active workers: {len(self.current_workers)}")
        
        if queue_length > self.scale_up_threshold:
            self.idle_count = 0
            if len(self.current_workers) < self.max_workers:
                logger.info(f"Queue length {queue_length} exceeds threshold {self.scale_up_threshold}. Scaling up.")
                self.start_worker()
        elif queue_length == 0:
            self.idle_count += 1
            if self.idle_count >= self.scale_down_idle_checks and len(self.current_workers) > self.min_workers:
                logger.info(f"Queue empty for {self.idle_count} checks. Scaling down.")
                self.stop_worker()
                self.idle_count = 0 # Reset to require another X checks to scale down again
        else:
            self.idle_count = 0

    def run(self):
        logger.info(f"Starting WorkerAutoscaler. Min: {self.min_workers}, Max: {self.max_workers}, Threshold: {self.scale_up_threshold}")
        
        # Start minimum workers
        while len(self.current_workers) < self.min_workers:
            self.start_worker()
            
        try:
            while True:
                self.check_and_scale()
                time.sleep(self.check_interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Autoscaler shutting down. Terminating all managed workers.")
            for pid, process in self.current_workers.items():
                process.terminate()
            for pid, process in self.current_workers.items():
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
if __name__ == "__main__":
    autoscaler = WorkerAutoscaler()
    autoscaler.run()