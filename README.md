# 📘 README: analyse_logarchive.py

## 🔍 Description

This script analyzes a single Apple `.logarchive` or compressed `.tar.gz` sysdiagnose archive and generates a forensic summary.

It automatically extracts, parses, and counts:

* Archive size (in KB, MB, GB)
* Start and end of log timeline (based on log events)
* TTL (Time To Live) in minutes, hours, and days
* Total event count
* Unique subsystems and their frequencies
* CSV report with all metrics and subsystem breakdown

---

## ▶️ Usage

Analyze a direct `.logarchive`:

```bash
python3 analyse_logarchive_single.py /path/to/logarchive.logarchive
```

Analyze a `.tar.gz` sysdiagnose:

```bash
python3 analyse_logarchive_single.py /path/to/sysdiagnose.tar.gz
```

The script will:

* Automatically detect `.logarchive` inside a sysdiagnose archive
* Prompt whether to delete temporary extracted files after processing
* Generate a timestamped CSV report (e.g. `log_report_20250529_153000.csv`)

---

## 📄 Output Example (CSV)

```
Field,Value
Logarchive Path,/path/to/logarchive
Size (KB),314572
Size (MB),307.38
Size (GB),0.3
First Log Line,2025-05-28 17:32:41.899 [subsystem] message
Last Log Line,2025-05-28 18:45:02.012 [subsystem] message
TTL (min),72.35
TTL (hours),1.21
TTL (days),0.05
Total Events,285678
Unique Subsystems,154

Subsystem,Event Count
com.apple.someprocess,8456
com.apple.other,2213
...
```

---

## 📦 Requirements

Install dependencies:

```bash
pip install python-dateutil
```

**Optional:** Use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### requirements.txt

```
python-dateutil
```

---

## 🧼 Cleanup Prompt

If you analyze a `.tar.gz`, the script will extract it temporarily and ask:

```
❓ Do you want to delete the temporary extracted folder /tmp/sysdiag_extract_xyz? (y/n):
```

---

## 🛡️ Tip

Keep a consistent folder structure for input archives. This improves automatic detection when running batch comparisons or generating reports.
