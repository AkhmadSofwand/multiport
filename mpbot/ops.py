import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class OpsError(RuntimeError):
    pass


def _run(cmd: List[str], input_text: str = "", timeout: int = 120) -> Tuple[int, str]:
    p = subprocess.run(
        cmd,
        input=input_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    out = p.stdout.decode("utf-8", errors="ignore")
    return p.returncode, out


def create_ssh(username: str, password: str, days: int) -> str:
    script = "/usr/bin/add-ssh"
    if not Path(script).exists():
        # fallback if script not installed in /usr/bin yet
        script = "/root/add-ssh.sh"
    if not Path(script).exists():
        raise OpsError("Skrip add-ssh tidak dijumpai")
    code, out = _run(["bash", script], f"{username}\n{password}\n{days}\n")
    if code != 0:
        raise OpsError(out[-500:])
    return out


def create_vmess(username: str, bug: str, sni: str, days: int) -> str:
    # use xraay menu: option 1
    code, out = _run(["bash", "/usr/bin/xraay"], f"1\n{username}\n{bug}\n{sni}\n{days}\n")
    if code != 0:
        raise OpsError(out[-500:])
    return out


def create_vless(username: str, bug: str, sni: str, days: int) -> str:
    # xraay menu: option 6
    code, out = _run(["bash", "/usr/bin/xraay"], f"6\n{username}\n{bug}\n{sni}\n{days}\n")
    if code != 0:
        raise OpsError(out[-500:])
    return out


def create_trojan(username: str, password: str, bug: str, sni: str, days: int) -> str:
    # trojaan menu we provide: option 1 create trojan ws
    code, out = _run(["bash", "/usr/bin/trojaan"], f"1\n{username}\n{password}\n{bug}\n{sni}\n{days}\n")
    if code != 0:
        raise OpsError(out[-500:])
    return out


def renew_account(protocol: str, username: str, days: int) -> str:
    if protocol == "SSH":
        code, out = _run(["bash", "/usr/bin/ssh"], f"3\n{username}\n{days}\n")
    elif protocol == "VMESS":
        code, out = _run(["bash", "/usr/bin/xraay"], f"3\n{username}\n{days}\n")
    elif protocol == "VLESS":
        code, out = _run(["bash", "/usr/bin/xraay"], f"8\n{username}\n{days}\n")
    elif protocol == "TROJAN":
        code, out = _run(["bash", "/usr/bin/trojaan"], f"3\n{username}\n{days}\n")
    else:
        raise OpsError("Protokol tak disokong")
    if code != 0:
        raise OpsError(out[-500:])
    return out
