"""Build the Windows x64 Rainmeter installer from the packaged MR5 service."""

import argparse
import struct
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


def package_skin(output):
    root = Path(__file__).resolve().parent
    service = root / "@Resources" / "MR5Service"
    if not (service / "MR5Service.exe").is_file() or not (service / "_internal" / "python313.dll").is_file():
        raise FileNotFoundError("Build MR5Service.spec before packaging the skin")

    prefix = "Skins/EdifierMR5/"
    manifest = (
        "[rmskin]\r\nName=EdifierMR5\r\nAuthor=fms2014\r\n"
        "LoadType=Skin\r\nLoad=EdifierMR5\\MR5_Overlay.ini\r\n"
        "MinimumWindows=10.0\r\n"
    )
    # The distributed config is a template. The editor and the service both use this name.
    config = "[Device]\r\nMAC_ADDRESS = XX:XX:XX:XX:XX:XX\r\nVOLUME_UUID =\r\n\r\n[Variables]\r\nAUTO_CONNECT=Y\r\n"
    required = [root / "MR5_Overlay.ini", root / "LICENSE"]
    required.extend(sorted(path for path in service.rglob("*") if path.is_file()))

    with NamedTemporaryFile(dir=output.parent, delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        with temporary.open("wb") as stream:
            with ZipFile(stream, "w", ZIP_DEFLATED, compresslevel=9) as zip_file:
                zip_file.writestr("RMSKIN.ini", manifest.encode("utf-16"))
                zip_file.writestr(prefix + "@Resources/config.ini", config)
                for path in required:
                    zip_file.write(path, prefix + path.relative_to(root).as_posix())
            # Rainmeter validates the ZIP length and signature in its 16-byte package footer.
            stream.write(struct.pack("<QB7s", stream.tell(), 0, b"RMSKIN\0"))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_packager_folder(parent):
    """Refresh the clean EdifierMR5 folder selected by Rainmeter's Add custom skin dialog."""
    parent = parent.resolve()
    source = Path(__file__).resolve().parent
    target = parent / "EdifierMR5"
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError("Choose an output directory outside the working skin")
    parent.mkdir(parents=True, exist_ok=True)
    marker = parent / ".edifier-packager-source"
    if target.is_symlink() or target.is_junction() or (target.exists() and not marker.is_file()):
        raise ValueError(f"Existing folder is not a generated packager source: {target}")

    with TemporaryDirectory(dir=parent) as tmp:
        stage = Path(tmp)
        archive = stage / "skin.rmskin"
        package_skin(archive)
        with ZipFile(archive) as package:
            package.extractall(stage, (name for name in package.namelist() if name.startswith("Skins/EdifierMR5/")))
        previous = stage / "previous"
        if target.exists():
            target.rename(previous)
        try:
            (stage / "Skins" / "EdifierMR5").rename(target)
        except OSError:
            if previous.exists():
                previous.rename(target)
            raise
        marker.touch()
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="prepare a folder for the Rainmeter Skin Packager")
    parser.add_argument("output", type=Path, nargs="?",
                        help=".rmskin file, or the parent directory for --prepare (default: Deploy next to Skins)")
    args = parser.parse_args()
    if args.prepare:
        deploy_dir = Path(__file__).resolve().parents[2] / "Deploy"
        print(prepare_packager_folder(args.output or deploy_dir))
    elif args.output is None or args.output.suffix.lower() != ".rmskin":
        parser.error("Choose a .rmskin output file")
    else:
        package_skin(args.output.resolve())
