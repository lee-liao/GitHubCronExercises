#!/usr/bin/env python3
import os, random, time

max_minutes = int(os.environ.get("WAIT_MAX_MINUTES", "10"))
minutes     = random.randint(0, max_minutes)
seconds     = random.randint(0, 59)
total       = minutes * 60 + seconds

print(f"Sleeping for {minutes} minute(s) and {seconds} second(s) (max {max_minutes}m)...")
time.sleep(total)
print("Wake up!")
