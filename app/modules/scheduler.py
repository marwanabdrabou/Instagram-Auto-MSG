import time
import threading
from datetime import datetime, time as dt_time
from typing import Dict, List
import logging
from modules.browser import InstagramBrowser
from modules.file_Io import FileManager
import random

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.running = False
        self.tasks = []
        self.thread = None

    def add_task(self, task_config: Dict):
        """Add a new scheduled task"""
        self.tasks.append(task_config)
        logger.info(f"Added new scheduled task for {task_config['time']}")

    def remove_task(self, index: int):
        """Remove a scheduled task"""
        if 0 <= index < len(self.tasks):
            removed = self.tasks.pop(index)
            logger.info(f"Removed scheduled task for {removed['time']}")

    def start(self):
        """Start the scheduler thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            current_time = datetime.now().strftime("%H:%M")
            
            for task in self.tasks:
                if task['time'] == current_time:
                    self._execute_task(task)
                    # Sleep to prevent duplicate execution
                    time.sleep(60)
            
            # Check every 30 seconds
            time.sleep(30)

    def _execute_task(self, task: Dict):
        """Execute a scheduled task"""
        logger.info(f"Executing scheduled task for {task['time']}")
        
        try:
            profiles = FileManager.load_profiles(task['file'])
            if not profiles:
                logger.error("No valid profiles found in the file")
                return

            browser = InstagramBrowser()
            try:
                if not browser.login(task['username'], task['password']):
                    logger.error("Login failed - aborting task")
                    return

                FileManager.init_results_file()
                sent_profiles = FileManager.load_sent_profiles()
                messages_sent = 0

                for profile in profiles:
                    if messages_sent >= task['max_messages']:
                        logger.info(f"Reached message limit ({task['max_messages']})")
                        break

                    if profile not in sent_profiles:
                        success = browser.send_message(profile, task['message'])
                        status = "Success" if success else "Failed"
                        FileManager.record_result(
                            profile, 
                            status, 
                            task['message'],
                            "" if success else "Failed to send message"
                        )
                        
                        if success:
                            messages_sent += 1
                            sent_profiles.add(profile)
                        
                        # Random delay between messages
                        delay = random.uniform(*task['message_delay'])
                        time.sleep(delay)

            finally:
                browser.close()

        except Exception as e:
            logger.error(f"Error executing scheduled task: {str(e)}")