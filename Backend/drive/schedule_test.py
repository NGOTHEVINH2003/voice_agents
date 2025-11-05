import schedule, time
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from Backend.drive.watcher import detect_file_changes

schedule.every(1).minutes.do(detect_file_changes)

while True:
    schedule.run_pending()
    time.sleep(60)