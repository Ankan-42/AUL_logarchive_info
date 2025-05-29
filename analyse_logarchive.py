# analyse_logarchive_single.py
import subprocess
import argparse
import os
import tarfile
import tempfile
from datetime import datetime
from collections import defaultdict
from html import escape
import csv
import shutil

VERBOSE = True

def vprint(*args):
    if VERBOSE:
        print("[INFO]", *args)

# Recursively search for a valid .logarchive inside a directory
def find_logarchive_in_directory(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d.endswith(".logarchive"):
                full_path = os.path.join(root, d)
                if os.path.isdir(os.path.join(full_path, "Persist")):
                    return full_path
    return None

# Extract a .tar.gz sysdiagnose archive to a temporary directory
def extract_tar_gz(tar_path):
    temp_dir = tempfile.mkdtemp(prefix="sysdiag_extract_")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=temp_dir)
    vprint(f"✅ Extracted to temporary directory: {temp_dir}")
    return temp_dir

# Parse timestamp string into datetime object
def parse_time(t):
    try:
        from dateutil import parser
        return parser.parse(t)
    except ImportError:
        try:
            return datetime.strptime(t.split('+')[0], "%Y-%m-%d %H:%M:%S.%f")
        except Exception as e:
            print(f"[ERROR] Timestamp parsing failed: {t} → {e}")
            raise

# Extract first and last log line timestamps
def get_time_range(lines):
    valid_lines = [l for l in lines if l and l[0].isdigit()]
    if not valid_lines:
        vprint("⚠️ No valid log lines found.")
        return None, None

    return valid_lines[0], valid_lines[-1]

# Count total number of log lines
def count_lines(lines):
    return len([l for l in lines if l and l[0].isdigit()])

# Count frequency of subsystems in log
def count_subsystems(lines):
    counter = defaultdict(int)
    for line in lines:
        start = line.find("[")
        end = line.find("]", start)
        if start != -1 and end != -1:
            sub = line[start+1:end]
            counter[sub] += 1
    return counter

# Generate CSV file summarizing subsystem counts
def generate_csv(info, path):
    total_events = sum(info['subsystems'].values())
    size_mb = round(info['size'] / 1024, 2)
    size_gb = round(size_mb / 1024, 2)
    ttl_hours = round(info['ttl'] / 60, 2)
    ttl_days = round(ttl_hours / 24, 2)

    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Logarchive Path", info['path']])
        writer.writerow(["Size (KB)", info['size']])
        writer.writerow(["Size (MB)", size_mb])
        writer.writerow(["Size (GB)", size_gb])
        writer.writerow(["First Log Line", info['start']])
        writer.writerow(["Last Log Line", info['end']])
        writer.writerow(["TTL (min)", info['ttl']])
        writer.writerow(["TTL (hours)", ttl_hours])
        writer.writerow(["TTL (days)", ttl_days])
        writer.writerow(["Total Events", info['lines']])
        writer.writerow(["Unique Subsystems", len(info['subsystems'])])
        writer.writerow([])
        writer.writerow(["Subsystem", "Event Count"])
        for sub in sorted(info['subsystems'], key=info['subsystems'].get, reverse=True):
            count = info['subsystems'][sub]
            writer.writerow([sub, count])
    vprint(f"✅ CSV report generated: {path}")

# Extract log show output once for analysis
def extract_log_output(path):
    vprint(f"Extracting log show output from: {path}")
    try:
        result = subprocess.run([
            "log", "show", "--archive", path,
            "--style", "syslog", "--info", "--debug"
        ], capture_output=True, text=True, timeout=900)
        return result.stdout.splitlines()
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout while reading logarchive: {path}")
        return []

# Calculate size of directory in kilobytes
def get_dir_size_kb(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / 1024, 2)

# Main function
def main():
    parser = argparse.ArgumentParser(description="Analyze a logarchive or sysdiagnose archive.")
    parser.add_argument("input", help="Path to .logarchive or .tar.gz sysdiagnose archive")
    args = parser.parse_args()

    path = args.input
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = None

    if path.endswith(".tar.gz"):
        temp_dir = extract_tar_gz(path)
        path = find_logarchive_in_directory(temp_dir)
        if not path:
            print("[ERROR] No .logarchive found in sysdiagnose.")
            return

    elif path.endswith(".logarchive") and os.path.isdir(path):
        vprint(f"✅ Logarchive detected: {path}")

    elif os.path.isdir(path):
        detected = find_logarchive_in_directory(path)
        if detected:
            path = detected
        else:
            print("[ERROR] No .logarchive found in directory.")
            return

    else:
        print("[ERROR] Invalid input: must be .logarchive, directory, or .tar.gz")
        return

    size_kb = get_dir_size_kb(path)
    log_lines = extract_log_output(path)

    if not log_lines:
        print("[ERROR] No valid log output returned.")
        return

    start_line, end_line = get_time_range(log_lines)
    if not start_line or not end_line:
        print("[ERROR] No valid timestamps found.")
        return

    ttl = round((parse_time(end_line.split()[0]) - parse_time(start_line.split()[0])).total_seconds() / 60, 2)
    lines = count_lines(log_lines)
    subsystems = count_subsystems(log_lines)

    info = {
        "path": path,
        "size": size_kb,
        "start": start_line,
        "end": end_line,
        "ttl": ttl,
        "lines": lines,
        "subsystems": subsystems
    }

    csv_output = f"log_report_{timestamp}.csv"
    generate_csv(info, csv_output)

    if temp_dir:
        answer = input(f"❓ Do you want to delete the temporary extracted folder {temp_dir}? (y/n): ").strip().lower()
        if answer == 'y':
            shutil.rmtree(temp_dir)
            vprint(f"🧹 Temporary directory {temp_dir} deleted.")
        else:
            vprint(f"📁 Temporary directory {temp_dir} kept at {temp_dir}.")

if __name__ == "__main__":
    main()
