import subprocess
import sys

def main():
    start_year = 2021
    end_year = 2025
    
    print(f"Starting bulk animation generation from {start_year} to {end_year}...")
    
    for year in range(start_year, end_year + 1):
        print(f"\n[Bulk Animate] Processing {year}...")
        cmd = [sys.executable, "animate_standings.py", "--year", str(year)]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"[Bulk Animate] Successfully generated {year}.")
        except subprocess.CalledProcessError as e:
            print(f"[Bulk Animate] Error generating {year}: {e}")
            # Decide whether to stop or continue. Continuing often best for bulk jobs.
            continue
        except KeyboardInterrupt:
            print("\n[Bulk Animate] Interrupted by user. Exiting.")
            sys.exit(1)

    print("\n[Bulk Animate] All done!")

if __name__ == "__main__":
    main()
