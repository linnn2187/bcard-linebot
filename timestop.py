from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from threading import Timer
import time
import os

def main():
		print("timestop.py START - "+datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		time.sleep(3600)
		print("timestop.py END - "+datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":  
  main() 
pass