import sys
from importlib.metadata import distribution
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, copy_metadata

sources = Path(SPECPATH) / "dev"
python_license = Path(sys.base_prefix) / "LICENSE.txt"
bootloader_license = next(f.locate() for f in distribution("pyinstaller").files if f.name == "COPYING.txt")

analysis = Analysis(
    [str(sources / "run_mr5.py")],
    pathex=[str(sources)],
    hiddenimports=collect_submodules("winrt"),
    binaries=collect_dynamic_libs("winrt"),
    # The Windows BLE client uses WinRT. asyncio's TLS and process-pool backends are optional.
    excludes=["ssl", "_ssl", "_hashlib", "multiprocessing", "unittest", "pydoc", "doctest"],
    datas=copy_metadata("bleak") + [
        (str(python_license), "licenses/python"),
        (str(bootloader_license), "licenses/pyinstaller"),
        (str(sources / "licenses" / "PyWinRT-LICENSE.txt"), "licenses/winrt"),
    ],
)
# The supported Windows 10/11 systems provide the Universal CRT.
analysis.binaries = [
    entry for entry in analysis.binaries
    if entry[0].lower() != "ucrtbase.dll" and not entry[0].lower().startswith("api-ms-win-")
]
# The volume overlay uses Tk timers and labels, but never converts time zones.
analysis.datas = [
    entry for entry in analysis.datas
    if not Path(entry[0]).as_posix().startswith("_tcl_data/tzdata/")
]
archive = PYZ(analysis.pure)
service = EXE(
    archive, analysis.scripts, [],
    name="MR5Service",
    exclude_binaries=True,
    console=False,
    upx=False,
)
bundle = COLLECT(
    service, analysis.binaries, analysis.datas,
    name="MR5Service",
    upx=False,
)
