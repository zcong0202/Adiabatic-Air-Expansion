#!/usr/bin/env python3
"""macOS/Linux serial CSV logger. Standard library only. Does not upload code."""
import argparse
import csv
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path
import selectors
import sys
import termios
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='/dev/cu.usbmodem11101')
    parser.add_argument('--out', required=True, help='New CSV path; existing files are preserved')
    args = parser.parse_args()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Fail before opening serial if this trial already exists.
    output = path.open('x', newline='')
    device = None
    try:
        device = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        cfg = termios.tcgetattr(device)
        cfg[0] = cfg[1] = cfg[3] = 0
        cfg[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        cfg[4] = cfg[5] = termios.B115200
        cfg[6][termios.VMIN] = 0
        cfg[6][termios.VTIME] = 0
        termios.tcsetattr(device, termios.TCSANOW, cfg)
        writer = csv.writer(output)
        fields = 'ms,mode,gt,raw_mm,median_mm,range_status,tof_valid,tof_age_ms,pir_raw,pir_warm,state,command,feedback,adc,feedback_v,match,fault'.split(',')
        writer.writerow(['host_time_dubai'] + fields)
        mux = selectors.DefaultSelector()
        mux.register(device, selectors.EVENT_READ, 'serial')
        if sys.stdin.isatty():
            mux.register(sys.stdin, selectors.EVENT_READ, 'stdin')
        print('Opening serial may reset Uno. Outputs start OFF. Close other serial tools.')
        print('Type a command + Enter: B=loopback T=ToF P=PIR H=hybrid X=stop R=reset 0/1=ground-truth. Ctrl-C ends.')
        pending = b''
        reported = 0.0
        with path.with_suffix('.meta.txt').open('x') as meta:
            meta.write(f'port={args.port}\nbaud=115200\n')
            while True:
                for key, _ in mux.select(timeout=0.5):
                    if key.data == 'stdin':
                        line = sys.stdin.readline()
                        if not line:
                            mux.unregister(sys.stdin)
                        else:
                            allowed = ''.join(c.upper() for c in line if c.upper() in 'BTPHXR01?')
                            if allowed:
                                os.write(device, allowed.encode('ascii'))
                                meta.write('command=' + allowed + '\n')
                                meta.flush()
                        continue
                    chunk = os.read(device, 4096)
                    pending += chunk
                    while b'\n' in pending:
                        raw, pending = pending.split(b'\n', 1)
                        line = raw.decode('ascii', errors='replace').strip()
                        if line.startswith('#'):
                            meta.write(line + '\n'); meta.flush(); print(line)
                            continue
                        row = line.split(',')
                        if row == fields or len(row) != len(fields):
                            continue
                        try:
                            int(row[0])
                        except ValueError:
                            continue  # Ignore partial startup lines.
                        writer.writerow([datetime.now(timezone(timedelta(hours=4))).isoformat()] + row)
                        output.flush()
                        if time.monotonic() - reported >= 1:
                            reported = time.monotonic()
                            print(f'{row[0]}ms mode={row[1]} distance={row[4]} valid={row[6]} PIR={row[8]} cmd={row[11]} fb={row[12]} V={row[14]} fault={row[16]}')
    except KeyboardInterrupt:
        print('\nStopped. CSV saved.')
    finally:
        if device is not None:
            try:
                os.write(device, b'X')  # Request OFF before closing.
            except OSError:
                pass
            os.close(device)
        output.close()


if __name__ == '__main__':
    main()
