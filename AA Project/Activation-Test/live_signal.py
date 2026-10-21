#!/usr/bin/env python3
"""Local live Uno signal viewer. Real serial samples; standard library only."""
import argparse
from collections import deque
import csv
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import select
import signal
import termios
import threading
import time

FIELDS = 'ms,mode,gt,raw_mm,median_mm,range_status,tof_valid,tof_age_ms,pir_raw,pir_warm,state,command,feedback,adc,feedback_v,match,fault'.split(',')
DUBAI = timezone(timedelta(hours=4))

class SerialReader:
    def __init__(self, port, directory):
        self.port = port
        self.lock = threading.Lock()
        self.latest = None
        self.samples = deque(maxlen=1200)
        self.messages = deque(maxlen=8)
        self.count = 0
        self.recorded_count = 0
        self.recording = False
        self.sensor_stopped = None
        self.connected = False
        self.error = ''
        self.last_received = 0
        self.last_command = ''
        self.stop = threading.Event()
        self.fd = None
        stamp = datetime.now(DUBAI).strftime('%Y%m%d-%H%M%S')
        directory.mkdir(parents=True, exist_ok=True)
        self.csv_path = directory / f'live-signal-{stamp}.csv'
        self.file = self.csv_path.open('x', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['host_time_dubai'] + FIELDS)
        self.file.flush()
        self.meta = self.csv_path.with_suffix('.meta.txt').open('x')
        self.meta.write(f'port={port}\nbaud=115200\n')
        self.meta.flush()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            self.fd = os.open(self.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            cfg = termios.tcgetattr(self.fd)
            cfg[0] = cfg[1] = cfg[3] = 0
            cfg[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            cfg[4] = cfg[5] = termios.B115200
            cfg[6][termios.VMIN] = cfg[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, cfg)
            with self.lock:
                self.connected = True
            buffer = b''
            while not self.stop.is_set():
                if not select.select([self.fd], [], [], .2)[0]:
                    continue
                chunk = os.read(self.fd, 4096)
                if not chunk:
                    raise OSError('Serial device stopped sending')
                buffer += chunk
                if len(buffer) > 65536:
                    buffer = b''
                while b'\n' in buffer:
                    raw, buffer = buffer.split(b'\n', 1)
                    line = raw.decode('ascii', errors='replace').strip()
                    if line.startswith('#'):
                        with self.lock:
                            self.messages.append(line)
                            if line.startswith('# Complete stop;'):
                                self.sensor_stopped = 'confirmed=1' in line
                            self.meta.write(line + '\n'); self.meta.flush()
                        continue
                    row = line.split(',')
                    if row == FIELDS or len(row) != len(FIELDS):
                        continue
                    try:
                        sample = {k: (v if k == 'mode' else float(v) if k == 'feedback_v' else int(v)) for k, v in zip(FIELDS, row)}
                    except ValueError:
                        continue
                    sample['host_time_dubai'] = datetime.now(DUBAI).isoformat()
                    with self.lock:
                        self.count += 1
                        sample['seq'] = self.count
                        self.latest = sample
                        recording = sample['mode'] != 'S'
                        if recording or self.recording:
                            self.samples.append(sample) # Include final OFF edge, then freeze history.
                        if recording != self.recording:
                            self.meta.write(f"{sample['host_time_dubai']} recording={'resumed' if recording else 'paused'}\n")
                            self.meta.flush()
                        self.recording = recording
                        self.last_received = time.monotonic()
                        if recording:
                            self.writer.writerow([sample['host_time_dubai']] + row)
                            self.recorded_count += 1
                            self.file.flush()
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
                self.connected = False
        finally:
            if self.fd is not None:
                try:
                    # Deployment keeps running when the viewer closes.
                    os.write(self.fd, b'?')
                except OSError:
                    pass
                os.close(self.fd)
                self.fd = None
            with self.lock:
                self.file.close(); self.meta.close()

    def send(self, command):
        with self.lock:
            if self.fd is None or not self.connected:
                raise OSError('Uno is not connected')
            os.write(self.fd, command.encode('ascii'))
            self.last_command = command
            self.meta.write(f'{datetime.now(DUBAI).isoformat()} command={command}\n')
            self.meta.flush()

    def state(self):
        with self.lock:
            return dict(latest=self.latest, count=self.count, connected=self.connected,
                age_ms=round((time.monotonic()-self.last_received)*1000) if self.last_received else None,
                error=self.error, port=self.port, log=self.csv_path.name,
                last_command=self.last_command, messages=list(self.messages),
                recording=self.recording, recorded_count=self.recorded_count, sensor_stopped=self.sensor_stopped)

    def close(self):
        self.stop.set(); self.thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='/dev/cu.usbmodem11101')
    parser.add_argument('--http-port', type=int, default=8765)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    reader = SerialReader(args.port, base/'results')
    origin = f'http://127.0.0.1:{args.http_port}'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def reply(self, data, content_type='application/json', status=200):
            if not isinstance(data, bytes):
                data = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            if self.path == '/':
                self.reply((base/'live-signal.html').read_bytes(), 'text/html; charset=utf-8')
            elif self.path == '/api/state':
                self.reply(reader.state())
            elif self.path == '/api/history':
                with reader.lock:
                    data = list(reader.samples)
                self.reply(data)
            elif self.path == '/session.csv':
                self.reply(reader.csv_path.read_bytes(), 'text/csv; charset=utf-8')
            elif self.path == '/api/events':
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                sent = None
                heartbeat = 0
                try:
                    while not reader.stop.is_set():
                        state = reader.state()
                        marker = (state['count'], state['connected'], state['error'])
                        if marker != sent or time.monotonic()-heartbeat >= 1:
                            self.wfile.write(('data: '+json.dumps(state)+'\n\n').encode())
                            self.wfile.flush(); sent = marker; heartbeat = time.monotonic()
                        time.sleep(.025)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.reply({'error':'Not found'}, status=404)
        def do_POST(self):
            if self.path != '/api/command' or self.headers.get('Origin') != origin:
                self.reply({'error':'Invalid local request'}, status=403); return
            if self.headers.get('Content-Type') != 'application/json':
                self.reply({'error':'JSON required'}, status=415); return
            try:
                size = int(self.headers.get('Content-Length','0'))
                if not 0 < size <= 128:
                    raise ValueError('Invalid request size')
                command = json.loads(self.rfile.read(size)).get('command')
                if command not in ('B','P','T','S','X','R','0','1','?'):
                    raise ValueError('Invalid command')
                reader.send(command)
                self.reply({'sent':command})
            except (ValueError, OSError) as exc:
                self.reply({'error':str(exc)}, status=400)

    server = ThreadingHTTPServer(('127.0.0.1', args.http_port), Handler)
    print(f'LIVE_URL={origin}', flush=True)
    print(f'CSV={reader.csv_path}', flush=True)
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        reader.close(); server.server_close()

if __name__ == '__main__':
    main()
