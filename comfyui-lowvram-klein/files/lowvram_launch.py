"""Starts the demo ComfyUI under LOW VRAM limits (tutorials/COMFYUI_LOWVRAM_PROMPT.md section 2):
  - VRAM: ComfyUI's --reserve-vram keeps (card - tier) GB away from models, so the 16 GB card behaves like the tier.
  - RAM: a Windows Job Object caps the committed memory of ComfyUI's process tree at the given GB.
Prints the PID and keeps running until ComfyUI exits (run it in the background; stop it by its command line).

    tutorials/venv/Scripts/python.exe tutorials/comfyui/lowvram_launch.py <vram tier GB> <ram GB> [extra ComfyUI args]
"""

import ctypes
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

PORTABLE = Path(r"E:\tutorial-work\klein-demo\ComfyUI_windows_portable")
CARD_GB = 16

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]


class BASIC(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]


class EXTENDED(ctypes.Structure):
    _fields_ = [("Basic", BASIC), ("Io", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


JOB_OBJECT_LIMIT_JOB_MEMORY = 0x200
JobObjectExtendedLimitInformation = 9


def main():
    tier, ram = float(sys.argv[1]), float(sys.argv[2])
    extra = sys.argv[3:]
    reserve = 0.0 if tier >= CARD_GB else CARD_GB - tier + 0.5  # +0.5 GB: ComfyUI's CUDA context sits on top of the models
    job = k32.CreateJobObjectW(None, None)
    info = EXTENDED()
    info.Basic.LimitFlags = JOB_OBJECT_LIMIT_JOB_MEMORY
    info.JobMemoryLimit = int(ram * 2**30)
    if not k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
        raise SystemExit(f"SetInformationJobObject failed: {ctypes.get_last_error()}")
    cmd = [str(PORTABLE / "python_embeded" / "python.exe"), "-s", "ComfyUI\\main.py", "--windows-standalone-build",
           "--reserve-vram", f"{reserve:g}", *extra]
    log = open(PORTABLE.parent / f"server-lowvram-{tier:g}gb.log", "w")
    proc = subprocess.Popen(cmd, cwd=PORTABLE, stdout=log, stderr=subprocess.STDOUT)
    handle = k32.OpenProcess(0x1F0FFF, False, proc.pid)
    if not k32.AssignProcessToJobObject(job, handle):
        raise SystemExit(f"AssignProcessToJobObject failed: {ctypes.get_last_error()}")
    (PORTABLE.parent / "comfy.pid").write_text(str(proc.pid))  # the recorder reads this to sample the process tree's RAM
    print(f"ComfyUI pid {proc.pid}: VRAM tier {tier:g} GB (reserve {reserve:g} GB), RAM cap {ram:g} GB", flush=True)
    proc.wait()
    q = EXTENDED()
    k32.QueryInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(q), ctypes.sizeof(q), None)
    print(f"exit {proc.returncode}; peak job memory {q.PeakJobMemoryUsed / 2**30:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
