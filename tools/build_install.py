#!/usr/bin/env python3
"""~/.claude/skills/saju 를 tar.gz+base64로 묶어 설치 안내 페이지(saju_install.html)를 만든다."""
import base64, io, os, subprocess, sys, tarfile, gzip, datetime

SKILL = os.path.expanduser("~/.claude/skills/saju")
HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", "__pycache__", "tools"}  # tools/는 공유용 페이지를 만드는 도구라 설치본에 넣지 않는다
SKIP_FILES = {".gitignore", "saju.zip", ".DS_Store"}

files = []
for root, dirs, names in os.walk(SKILL):
    dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
    for n in sorted(names):
        if n in SKIP_FILES or n.endswith(".pyc"):
            continue
        files.append(os.path.join(root, n))

raw = io.BytesIO()
with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
    for f in files:
        arc = "saju/" + os.path.relpath(f, SKILL)
        ti = tar.gettarinfo(f, arc)
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = ""
        ti.mode = 0o755 if f.endswith(".py") else 0o644
        with open(f, "rb") as fh:
            tar.addfile(ti, fh)
gz = gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)
b64 = base64.b64encode(gz).decode()
assert "'" not in b64

listing = "\n".join("saju/%-34s %6.1f KB" % (os.path.relpath(f, SKILL), os.path.getsize(f) / 1024) for f in files)
ver = subprocess.run(["git", "-C", SKILL, "log", "-1", "--format=%h"], capture_output=True, text=True).stdout.strip() or "local"

def rd(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()

body = rd(os.path.join(HERE, "install_body.html"))
for k, v in (("__B64__", b64), ("__FILES__", listing), ("__COUNT__", str(len(files))),
             ("__KB__", str(round(len(b64) / 1024))), ("__VERSION__", datetime.date.today().isoformat() + " · " + ver)):
    assert k in body, k
    body = body.replace(k, v)
page = ("<title>사주 스킬 설치</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n"
        + rd(os.path.join(SKILL, "assets", "style.html")) + "\n" + rd(os.path.join(SKILL, "assets", "mascot_wood.html")) + "\n" + body)
out = os.path.join(HERE, "saju_install.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(page)
with open(os.path.join(HERE, "saju_install_cmd.sh"), "w", encoding="utf-8") as fh:
    fh.write("mkdir -p ~/.claude/skills && echo '%s' | base64 --decode | tar -xz -C ~/.claude/skills && echo '설치 완료: ~/.claude/skills/saju'\n" % b64)
print("files", len(files), "| tgz", len(gz), "| b64", len(b64), "| page", len(page.encode()), "| ver", ver)
