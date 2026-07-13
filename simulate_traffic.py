"""
Simulated Traffic Generator
Generates realistic NSL-KDD-style network traffic and feeds it directly
into the IDS database — bypassing the ML model so data is pre-labelled.

Used to demonstrate the system's dashboard, alert management, and log views
with lifelike network traffic patterns.

All generated records are tagged with is_simulated=1 so the UI can clearly
distinguish them from real inference results.
"""

import random
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from core.database import Database

# ── Traffic distribution (mirrors NSL-KDD class balance) ─────────────────────
CLASS_WEIGHTS = {
    'normal':  0.68,
    'dos':     0.16,
    'probing': 0.08,
    'r2l':     0.05,
    'u2r':     0.03,
}

CLASSES = list(CLASS_WEIGHTS.keys())
WEIGHTS = list(CLASS_WEIGHTS.values())

# ── Realistic source IP pools per class ──────────────────────────────────────
IP_POOLS = {
    'normal':  [f'10.0.{r}.{h}' for r in range(0, 5) for h in range(1, 30)],
    'dos':     [f'203.0.113.{i}' for i in range(1, 60)] +
               [f'198.51.100.{i}' for i in range(1, 40)],
    'probing': [f'172.16.{s}.{i}' for s in range(10, 20) for i in range(1, 15)],
    'r2l':     [f'192.0.2.{i}' for i in range(1, 50)],
    'u2r':     [f'100.64.{i}.1' for i in range(1, 20)],
}

PROTOCOLS = ['tcp', 'udp', 'icmp']
SERVICES   = ['http', 'ftp', 'smtp', 'ssh', 'telnet', 'dns', 'finger',
              'pop_3', 'imap4', 'ldap', 'netbios_ns', 'other']
FLAGS_NORMAL  = ['SF', 'SF', 'SF', 'SF', 'RSTO']          # mostly SF
FLAGS_ATTACK  = ['S0', 'S0', 'REJ', 'RSTR', 'SF', 'SH']   # mostly S0/REJ


# ─────────────────────────────────────────────────────────────────────────────
# Per-class realistic feature profiles
# ─────────────────────────────────────────────────────────────────────────────

def _make_normal() -> Dict[str, Any]:
    return {
        'protocol_type':           random.choice(['tcp', 'udp']),
        'service':                 random.choice(['http', 'smtp', 'ftp', 'ssh', 'dns']),
        'flag':                    random.choice(FLAGS_NORMAL),
        'duration':                random.randint(0, 300),
        'src_bytes':               random.randint(100, 8000),
        'dst_bytes':               random.randint(200, 15000),
        'logged_in':               1,
        'num_failed_logins':       0,
        'num_compromised':         0,
        'root_shell':              0,
        'num_root':                0,
        'num_outbound_cmds':       0,
        'is_host_login':           0,
        'count':                   random.randint(1, 30),
        'srv_count':               random.randint(1, 30),
        'srv_serror_rate':         round(random.uniform(0.0, 0.05), 3),
        'srv_rerror_rate':         round(random.uniform(0.0, 0.05), 3),
        'diff_srv_rate':           round(random.uniform(0.0, 0.1),  3),
        'srv_diff_host_rate':      round(random.uniform(0.0, 0.1),  3),
        'dst_host_count':          random.randint(10, 255),
        'dst_host_same_srv_rate':  round(random.uniform(0.7, 1.0),  3),
        'dst_host_diff_srv_rate':  round(random.uniform(0.0, 0.1),  3),
        'dst_host_srv_diff_host_rate': round(random.uniform(0.0, 0.05), 3),
        'dst_host_serror_rate':    round(random.uniform(0.0, 0.02), 3),
        'dst_host_srv_serror_rate':round(random.uniform(0.0, 0.02), 3),
        'dst_host_rerror_rate':    round(random.uniform(0.0, 0.02), 3),
        'dst_host_srv_rerror_rate':round(random.uniform(0.0, 0.02), 3),
    }


def _make_dos() -> Dict[str, Any]:
    """High packet rate, many connection errors, short duration."""
    return {
        'protocol_type':           random.choice(['tcp', 'icmp']),
        'service':                 random.choice(['http', 'private', 'ecr_i', 'other']),
        'flag':                    random.choice(['S0', 'S0', 'S0', 'REJ', 'RSTR']),
        'duration':                random.randint(0, 2),
        'src_bytes':               random.randint(0, 1000),
        'dst_bytes':               0,
        'logged_in':               0,
        'num_failed_logins':       0,
        'num_compromised':         0,
        'root_shell':              0,
        'num_root':                0,
        'num_outbound_cmds':       0,
        'is_host_login':           0,
        'count':                   random.randint(200, 511),
        'srv_count':               random.randint(200, 511),
        'srv_serror_rate':         round(random.uniform(0.8, 1.0),  3),
        'srv_rerror_rate':         round(random.uniform(0.0, 0.1),  3),
        'diff_srv_rate':           round(random.uniform(0.0, 0.06), 3),
        'srv_diff_host_rate':      round(random.uniform(0.0, 0.06), 3),
        'dst_host_count':          random.randint(150, 255),
        'dst_host_same_srv_rate':  round(random.uniform(0.9, 1.0),  3),
        'dst_host_diff_srv_rate':  round(random.uniform(0.0, 0.05), 3),
        'dst_host_srv_diff_host_rate': round(random.uniform(0.0, 0.02), 3),
        'dst_host_serror_rate':    round(random.uniform(0.8, 1.0),  3),
        'dst_host_srv_serror_rate':round(random.uniform(0.8, 1.0),  3),
        'dst_host_rerror_rate':    round(random.uniform(0.0, 0.1),  3),
        'dst_host_srv_rerror_rate':round(random.uniform(0.0, 0.1),  3),
    }


def _make_probing() -> Dict[str, Any]:
    """Port / host scanning — many different services, high diff_srv_rate."""
    return {
        'protocol_type':           random.choice(['tcp', 'udp', 'icmp']),
        'service':                 random.choice(['private', 'other', 'domain_u', 'ntp_u']),
        'flag':                    random.choice(['S0', 'REJ', 'RSTR', 'SF']),
        'duration':                random.randint(0, 5),
        'src_bytes':               random.randint(0, 400),
        'dst_bytes':               random.randint(0, 200),
        'logged_in':               0,
        'num_failed_logins':       0,
        'num_compromised':         0,
        'root_shell':              0,
        'num_root':                0,
        'num_outbound_cmds':       0,
        'is_host_login':           0,
        'count':                   random.randint(1, 30),
        'srv_count':               random.randint(1, 10),
        'srv_serror_rate':         round(random.uniform(0.0, 0.5),  3),
        'srv_rerror_rate':         round(random.uniform(0.0, 0.5),  3),
        'diff_srv_rate':           round(random.uniform(0.5, 1.0),  3),
        'srv_diff_host_rate':      round(random.uniform(0.4, 1.0),  3),
        'dst_host_count':          random.randint(1, 255),
        'dst_host_same_srv_rate':  round(random.uniform(0.0, 0.3),  3),
        'dst_host_diff_srv_rate':  round(random.uniform(0.3, 1.0),  3),
        'dst_host_srv_diff_host_rate': round(random.uniform(0.2, 1.0), 3),
        'dst_host_serror_rate':    round(random.uniform(0.0, 0.5),  3),
        'dst_host_srv_serror_rate':round(random.uniform(0.0, 0.5),  3),
        'dst_host_rerror_rate':    round(random.uniform(0.0, 0.5),  3),
        'dst_host_srv_rerror_rate':round(random.uniform(0.0, 0.5),  3),
    }


def _make_r2l() -> Dict[str, Any]:
    """Remote-to-local — targets login services, failed logins, longer sessions."""
    return {
        'protocol_type':           'tcp',
        'service':                 random.choice(['ftp', 'telnet', 'ssh', 'smtp', 'imap4']),
        'flag':                    random.choice(['SF', 'RSTR']),
        'duration':                random.randint(5, 1000),
        'src_bytes':               random.randint(1000, 20000),
        'dst_bytes':               random.randint(500, 5000),
        'logged_in':               random.choice([0, 0, 1]),
        'num_failed_logins':       random.randint(1, 5),
        'num_compromised':         random.randint(0, 5),
        'root_shell':              0,
        'num_root':                0,
        'num_outbound_cmds':       0,
        'is_host_login':           0,
        'count':                   random.randint(1, 15),
        'srv_count':               random.randint(1, 15),
        'srv_serror_rate':         round(random.uniform(0.0, 0.1),  3),
        'srv_rerror_rate':         round(random.uniform(0.0, 0.3),  3),
        'diff_srv_rate':           round(random.uniform(0.0, 0.2),  3),
        'srv_diff_host_rate':      round(random.uniform(0.0, 0.2),  3),
        'dst_host_count':          random.randint(1, 30),
        'dst_host_same_srv_rate':  round(random.uniform(0.5, 1.0),  3),
        'dst_host_diff_srv_rate':  round(random.uniform(0.0, 0.2),  3),
        'dst_host_srv_diff_host_rate': round(random.uniform(0.0, 0.1), 3),
        'dst_host_serror_rate':    round(random.uniform(0.0, 0.1),  3),
        'dst_host_srv_serror_rate':round(random.uniform(0.0, 0.1),  3),
        'dst_host_rerror_rate':    round(random.uniform(0.1, 0.5),  3),
        'dst_host_srv_rerror_rate':round(random.uniform(0.1, 0.5),  3),
    }


def _make_u2r() -> Dict[str, Any]:
    """User-to-root — privilege escalation, root shell, compromised files."""
    return {
        'protocol_type':           'tcp',
        'service':                 random.choice(['telnet', 'ssh', 'ftp']),
        'flag':                    'SF',
        'duration':                random.randint(100, 3000),
        'src_bytes':               random.randint(2000, 30000),
        'dst_bytes':               random.randint(1000, 10000),
        'logged_in':               1,
        'num_failed_logins':       random.randint(0, 2),
        'num_compromised':         random.randint(1, 20),
        'root_shell':              1,
        'num_root':                random.randint(1, 10),
        'num_outbound_cmds':       random.randint(0, 3),
        'is_host_login':           random.randint(0, 1),
        'count':                   random.randint(1, 10),
        'srv_count':               random.randint(1, 10),
        'srv_serror_rate':         round(random.uniform(0.0, 0.1),  3),
        'srv_rerror_rate':         round(random.uniform(0.0, 0.1),  3),
        'diff_srv_rate':           round(random.uniform(0.0, 0.1),  3),
        'srv_diff_host_rate':      round(random.uniform(0.0, 0.1),  3),
        'dst_host_count':          random.randint(1, 20),
        'dst_host_same_srv_rate':  round(random.uniform(0.5, 1.0),  3),
        'dst_host_diff_srv_rate':  round(random.uniform(0.0, 0.2),  3),
        'dst_host_srv_diff_host_rate': round(random.uniform(0.0, 0.1), 3),
        'dst_host_serror_rate':    round(random.uniform(0.0, 0.05), 3),
        'dst_host_srv_serror_rate':round(random.uniform(0.0, 0.05), 3),
        'dst_host_rerror_rate':    round(random.uniform(0.0, 0.1),  3),
        'dst_host_srv_rerror_rate':round(random.uniform(0.0, 0.1),  3),
    }


FEATURE_BUILDERS = {
    'normal':  _make_normal,
    'dos':     _make_dos,
    'probing': _make_probing,
    'r2l':     _make_r2l,
    'u2r':     _make_u2r,
}

# Confidence ranges that feel realistic per class
CONFIDENCE_RANGES = {
    'normal':  (0.72, 0.99),
    'dos':     (0.80, 0.99),
    'probing': (0.60, 0.92),
    'r2l':     (0.55, 0.88),
    'u2r':     (0.50, 0.85),
}


# ─────────────────────────────────────────────────────────────────────────────
# Core record builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_record(cls: str, timestamp: str = None) -> Dict[str, Any]:
    """Build one complete event record for the given class."""
    features = FEATURE_BUILDERS[cls]()
    source_ip = random.choice(IP_POOLS[cls])
    conf_lo, conf_hi = CONFIDENCE_RANGES[cls]
    confidence = round(random.uniform(conf_lo, conf_hi), 4)

    record = {
        'timestamp':       timestamp or datetime.utcnow().isoformat(),
        'predicted_class': cls,
        'confidence':      confidence,
        'source_ip':       f'[SIM]{source_ip}',
        'is_simulated':    1,
    }
    record.update(features)
    return record


# ─────────────────────────────────────────────────────────────────────────────
# Historical seed — spread N records over the past `hours` hours
# ─────────────────────────────────────────────────────────────────────────────

def generate_historical_data(n: int = 800, hours: int = 24) -> int:
    """
    Insert `n` simulated records with timestamps spread over the past `hours`.
    Returns number of records inserted.
    """
    db = Database()
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    inserted = 0

    # Build a timeline of timestamps in chronological order
    interval_seconds = (hours * 3600) / n
    timestamps = [
        (start + timedelta(seconds=i * interval_seconds +
                           random.uniform(-interval_seconds * 0.4,
                                          interval_seconds * 0.4)))
        .isoformat()
        for i in range(n)
    ]
    timestamps.sort()

    for ts in timestamps:
        cls = random.choices(CLASSES, weights=WEIGHTS, k=1)[0]
        record = _build_record(cls, timestamp=ts)
        try:
            event_id = db.create_event(record)
            if cls != 'normal':
                db.create_alert(event_id, cls, record['confidence'],
                                record['source_ip'])
            inserted += 1
        except Exception as e:
            print(f'[SIM] Error inserting record: {e}')

    print(f'[SIM] Inserted {inserted} historical records over the past {hours}h.')
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# Live simulation — runs in a background thread
# ─────────────────────────────────────────────────────────────────────────────

_sim_thread: threading.Thread = None
_sim_stop_event = threading.Event()


def _simulation_loop(interval_range=(2, 8)):
    """
    Continuously insert one simulated event every 2–8 seconds.
    Runs until _sim_stop_event is set.
    """
    db = Database()
    while not _sim_stop_event.is_set():
        cls = random.choices(CLASSES, weights=WEIGHTS, k=1)[0]
        record = _build_record(cls)
        try:
            event_id = db.create_event(record)
            if cls != 'normal':
                db.create_alert(event_id, cls, record['confidence'],
                                record['source_ip'])
        except Exception as e:
            print(f'[SIM] Live insert error: {e}')

        sleep_secs = random.uniform(*interval_range)
        _sim_stop_event.wait(timeout=sleep_secs)


def start_live_simulation():
    """Start the background simulation thread (idempotent)."""
    global _sim_thread
    if _sim_thread and _sim_thread.is_alive():
        print('[SIM] Live simulation already running.')
        return
    _sim_stop_event.clear()
    _sim_thread = threading.Thread(target=_simulation_loop,
                                   name='sim-traffic', daemon=True)
    _sim_thread.start()
    print('[SIM] Live simulation started.')


def stop_live_simulation():
    """Stop the background simulation thread."""
    _sim_stop_event.set()
    if _sim_thread:
        _sim_thread.join(timeout=15)
    print('[SIM] Live simulation stopped.')


# ─────────────────────────────────────────────────────────────────────────────
# Standalone entry-point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='IDS Traffic Simulator')
    parser.add_argument('--seed', type=int, default=800,
                        help='Number of historical records to seed (default: 800)')
    parser.add_argument('--hours', type=int, default=24,
                        help='Spread seed records over this many past hours (default: 24)')
    parser.add_argument('--live', action='store_true',
                        help='Keep running and insert live events until Ctrl-C')
    args = parser.parse_args()

    print(f'[SIM] Seeding {args.seed} historical records over {args.hours}h...')
    generate_historical_data(n=args.seed, hours=args.hours)

    if args.live:
        print('[SIM] Starting live simulation. Press Ctrl-C to stop.')
        start_live_simulation()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_live_simulation()
