import time
import os
import subprocess
import json
import psutil # Assuming we can install this, or use subprocess to check

"""
finalize_downloads.py

Automates the completion of the F1 data download process.
1. Monitors the `download_all_seasons.py` process.
2. Waits for it to finish.
3. Runs `verify_integrity.py` to check for incomplete seasons.
4. Reads `logs/mismatched_years.json` and forcefully re-downloads those specific years.
"""

def is_download_running():
    # Simple check using pgrep
    try:
        # Check for python process running download_all_seasons.py
        # We use pgrep -f to match full command line
        result = subprocess.run(['pgrep', '-f', 'download_all_seasons.py'], stdout=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False

def main():
    print("--- Finalize Downloads Script Started ---")
    
    # 1. Wait for Download
    print("Monitoring 'download_all_seasons.py'...")
    while is_download_running():
        print("Download still running... Waiting 60s")
        time.sleep(60)
        
    print("Download process finished (or not found). Proceeding to verification.")
    time.sleep(5) # Give file system a moment
    
    # 2. Verify Integrity
    print("Running verify_integrity.py...")
    subprocess.run(['python', 'verify_integrity.py'])
    
    # 3. Check Mismatches
    mismatched_file = 'logs/mismatched_years.json'
    if os.path.exists(mismatched_file):
        with open(mismatched_file, 'r') as f:
            mismatched_years = json.load(f)
            
        if mismatched_years:
            print(f"Found {len(mismatched_years)} mismatched years: {mismatched_years}")
            print("Attempting to re-download mismatched years...")
            
            # 4. Re-download mismatches
            # We can use download_all_seasons.py logic or just call it directly
            # Since download_all_seasons.py takes start/end, calling it per year might be slow due to startup overhead
            # but it is safer. Or we can modify it to accept a list.
            # Simpler: Loop and call script with --force --start Y --end Y
            
            for year in mismatched_years:
                print(f"Re-downloading {year}...")
                subprocess.run([
                    'venv/bin/python', 'download_all_seasons.py', 
                    '--start', str(year), 
                    '--end', str(year), 
                    '--force'
                ])
                # We should probably sleep a bit between force downloads too, 
                # although module has internal rate limiting, the startup/shutdown might bypass strict 10m cycle check?
                # Actually download_all_seasons uses pacing loop. If we run it for 1 year, it might exit quickly.
                # Let's add a small sleep here to be safe.
                time.sleep(10)
                
            print("Re-download complete.")
            
            # Verify one last time
            print("Running final verification...")
            subprocess.run(['python', 'verify_integrity.py'])
            
        else:
            print("No mismatches found! Data is complete.")
    else:
        print("No mismatched_years.json found. Verification might have failed or everything is perfect.")

    print("--- Finalize Script Complete ---")

if __name__ == "__main__":
    main()
