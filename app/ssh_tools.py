import subprocess

import yaml

from app.config import SERVERS_FILE, SSH_COMMAND_TIMEOUT, SSH_CONNECT_TIMEOUT

SERVERS_FILE_HEADER = (
    "# 실시간 서버 상태 조회(디스크 용량, 메모리 등)를 위한 SSH 접속 대상 목록입니다.\n"
    "# 비밀번호나 SSH 키는 절대 여기 넣지 마세요. ssh_target은 평소 터미널에서\n"
    "# `ssh <이 값>`이라고 입력할 때 쓰는 값과 동일해야 하며, 실제 인증은\n"
    "# ~/.ssh/config 에 설정된 Host 별칭 / SSH 에이전트 / 키가 담당합니다.\n\n"
)


def _load_raw_servers():
    """servers.yaml의 servers: 리스트를 그대로 반환합니다 (없으면 빈 리스트)."""
    if not SERVERS_FILE.exists():
        return []

    with open(SERVERS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("servers", [])


def _save_raw_servers(servers_list):
    with open(SERVERS_FILE, "w", encoding="utf-8") as f:
        f.write(SERVERS_FILE_HEADER)
        yaml.safe_dump({"servers": servers_list}, f, allow_unicode=True, sort_keys=False)


def load_servers():
    """servers.yaml을 읽어 {서버이름: {ssh_target, port}} 딕셔너리로 반환합니다."""
    servers = {}
    for entry in _load_raw_servers():
        name = entry.get("name")
        ssh_target = entry.get("ssh_target")
        if not name or not ssh_target:
            continue
        servers[name] = {
            "ssh_target": ssh_target,
            "port": entry.get("port", 22),
        }
    return servers


def register_server(name: str, ssh_target: str, port: int = 22) -> str:
    """새 서버의 SSH 접속 정보를 servers.yaml에 등록합니다. 이미 등록된 이름이면 접속 정보를 갱신합니다.

    Args:
        name: 서버 이름 (앞으로 질문에서 부를 이름)
        ssh_target: SSH 접속 대상. 평소 터미널에서 `ssh <값>`이라고 입력할 때 쓰는 값과 동일해야 합니다
            (예: user@host 또는 ~/.ssh/config의 Host 별칭). 비밀번호나 키는 절대 포함하지 않습니다.
        port: SSH 포트 번호 (기본값 22)
    """
    servers_list = _load_raw_servers()

    for entry in servers_list:
        if entry.get("name") == name:
            entry["ssh_target"] = ssh_target
            entry["port"] = port
            _save_raw_servers(servers_list)
            return f"'{name}' 서버의 접속 정보를 갱신했습니다."

    servers_list.append({"name": name, "ssh_target": ssh_target, "port": port})
    _save_raw_servers(servers_list)
    return f"'{name}' 서버를 새로 등록했습니다."


def _resolve_server(server_name):
    servers = load_servers()
    if server_name in servers:
        return servers[server_name], None

    if not servers:
        return None, "servers.yaml 파일이 없거나 등록된 서버가 없습니다. servers.yaml.example을 참고해서 설정하세요."

    known = ", ".join(servers.keys())
    return None, f"'{server_name}'은(는) 등록되지 않은 서버입니다. 등록된 서버: {known}"


def _run_ssh_command(server_name, command):
    server, error = _resolve_server(server_name)
    if error:
        return error

    ssh_command = [
        "ssh",
        "-p", str(server["port"]),
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}",
        server["ssh_target"],
        command,
    ]

    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=SSH_COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"오류: '{server_name}' 서버 접속이 시간 초과되었습니다. VPN 연결이나 서버 상태를 확인하세요."
    except FileNotFoundError:
        return "오류: 이 시스템에 ssh 명령을 찾을 수 없습니다."

    if result.returncode != 0:
        stderr = result.stderr.strip()
        return f"오류: '{server_name}' 서버 명령 실행에 실패했습니다 ({stderr})"

    output = result.stdout.strip()
    return output if output else "명령 실행 결과가 비어 있습니다."


# 이 목록에 있는 패턴이 포함된 명령은 상태를 변경/파괴할 수 있다고 보고 무조건 거부합니다.
# 완벽한 방어(샌드박스)는 아니지만, 정상적인 진단 목적의 명령을 걸러내는 1차 안전장치입니다.
DANGEROUS_PATTERNS = [
    "rm ", "rm-", "rmdir", "mv ", "dd ", "truncate", "shred", "mkfs",
    ">", "<(",
    "kill", "reboot", "shutdown", "halt", "poweroff",
    "systemctl stop", "systemctl restart", "systemctl disable", "systemctl kill",
    "service ", "docker stop", "docker rm", "docker kill", "docker restart", "docker rmi",
    "chmod", "chown", "chgrp", "useradd", "userdel", "usermod", "passwd", "visudo",
    "iptables", "ufw", "firewall-cmd",
    "sudo", "su ",
    "apt ", "apt-get", "yum ", "dnf ", "pip install", "npm install",
    "| sh", "| bash",
]


def _is_dangerous_command(command):
    lowered = command.lower()
    return any(pattern in lowered for pattern in DANGEROUS_PATTERNS)


def run_readonly_diagnostic(server_name: str, command: str) -> str:
    """지정한 서버에서 읽기 전용 진단 쉘 명령을 실행하고 결과를 확인합니다.
    디스크 용량, 메모리, 프로세스 목록, 도커 컨테이너 상태, 가동 시간 등 서버 상태를 확인할 때 사용하세요.
    파일을 수정/삭제하거나 프로세스·서비스를 재시작/중지/삭제하는 등 상태를 바꾸는 명령은 절대 실행하지 마세요 — 오직 조회만 하세요.

    Args:
        server_name: 서버 이름. servers.yaml에 등록된 이름과 일치해야 합니다.
        command: 실행할 읽기 전용 쉘 명령. 예: "df -h", "free -h", "docker ps", "uptime",
            "ps -ef | grep nginx", "cat /etc/os-release", "netstat -tlnp".
    """
    if _is_dangerous_command(command):
        return f"오류: 상태를 변경할 수 있는 위험한 명령으로 판단되어 실행을 거부했습니다: {command}"
    return _run_ssh_command(server_name, command)
