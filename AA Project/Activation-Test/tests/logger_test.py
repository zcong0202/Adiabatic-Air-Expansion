"""Test logger against a virtual serial port; never opens the attached Uno."""
import csv
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time

logger = Path(__file__).resolve().parents[1] / 'log_signal.py'
with tempfile.TemporaryDirectory(prefix='aa-logger-test-') as temp:
    master, slave = pty.openpty()
    output = Path(temp) / 'trial.csv'
    child = subprocess.Popen([sys.executable, '-u', str(logger), '--port', os.ttyname(slave), '--out', str(output)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([child.stdout], [], [], 5)[0], 'logger startup timeout'
        assert 'Opening serial' in child.stdout.readline()
        os.write(master, b'# virtual UART test\n500,T,1,1000,1000,0,1,0,0,0,2,1,1,930,4.545,1,0\n')
        end = time.monotonic() + 3
        rows = []
        while time.monotonic() < end:
            if output.exists():
                with output.open() as f:
                    rows = list(csv.DictReader(f))
                if rows: break
            time.sleep(0.03)
        assert len(rows) == 1 and rows[0]['command'] == '1' and rows[0]['feedback_v'] == '4.545', rows
        assert rows[0]['host_time_dubai'].endswith('+04:00')
        child.send_signal(signal.SIGINT)
        _, err = child.communicate(timeout=3)
        assert child.returncode == 0, err
        assert select.select([master], [], [], 1)[0], 'missing stop command'
        assert b'X' in os.read(master, 4096)
        assert '# virtual UART test' in output.with_suffix('.meta.txt').read_text()
        print('PASS: virtual UART ingestion, CSV values, Dubai time, metadata, Ctrl-C OFF request. Live Uno not tested.')
    finally:
        if child.poll() is None:
            child.kill(); child.wait()
        os.close(master); os.close(slave)
