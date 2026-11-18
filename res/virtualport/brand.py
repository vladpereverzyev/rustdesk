#!/usr/bin/env python3
"""Turn a RustDesk checkout into VirtualPort: app name, Windows version info and icons.

Run it from the repository root before the build, after the submodules are checked out:

    pip install pillow
    python res/virtualport/brand.py

The changes are applied to the working tree only, so the upstream sources stay untouched
in git and the fork can follow RustDesk with a plain merge.
"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw

APP_NAME = "VirtualPort"

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

ICON_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
LOGO_MAX = (300, 60)  # loadLogo() in flutter/lib/common.dart shows at most 300 x 60


def replace_once(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    if new in text and old not in text:
        print(f"already branded: {path}")
        return
    if text.count(old) != 1:
        sys.exit(f"expected exactly one {old!r} in {path}, found {text.count(old)}")
    file.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched: {path}")


def square_icon(size):
    # The VP strokes in the source are transparent holes in a black disc, which vanish on a
    # dark taskbar. A white disc slightly smaller than the black one keeps them white.
    src = Image.open(HERE / "icon-source.png").convert("RGBA")
    inset = round(src.width * 0.01)
    under = Image.new("RGBA", src.size, (0, 0, 0, 0))
    ImageDraw.Draw(under).ellipse(
        (inset, inset, src.width - 1 - inset, src.height - 1 - inset), fill=(255, 255, 255, 255)
    )
    under.alpha_composite(src)
    return under.resize((size, size), Image.LANCZOS)


def save_ico(path):
    big = square_icon(256)
    big.save(ROOT / path, format="ICO", sizes=[(s, s) for s in ICON_SIZES])
    print(f"icon: {path}")


def save_png(path, size):
    square_icon(size).save(ROOT / path, format="PNG")
    print(f"icon: {path}")


def save_logo(source, path):
    logo = Image.open(HERE / source).convert("RGBA")
    logo.thumbnail((LOGO_MAX[0] * 2, LOGO_MAX[1] * 2), Image.LANCZOS)  # 2x for high-DPI screens
    logo.save(ROOT / path, format="PNG")
    print(f"logo: {path}")


def main():
    replace_once(
        "libs/hbb_common/src/config.rs",
        'APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
        f'APP_NAME: RwLock<String> = RwLock::new("{APP_NAME}".to_owned());',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"',
        f'VALUE "FileDescription", "{APP_NAME} Remote Desktop" "\\0"',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "ProductName", "RustDesk" "\\0"',
        f'VALUE "ProductName", "{APP_NAME}" "\\0"',
    )
    replace_once(
        "flutter/windows/runner/main.cpp",
        'std::wstring app_name = L"RustDesk";',
        f'std::wstring app_name = L"{APP_NAME}";',
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        '"RustDesk",\n                              style: TextStyle(fontSize: 13),',
        f'"{APP_NAME}",\n                              style: TextStyle(fontSize: 13),',
    )

    save_ico("res/icon.ico")
    save_ico("res/tray-icon.ico")
    save_ico("flutter/windows/runner/resources/app_icon.ico")
    save_png("res/icon.png", 512)
    save_png("res/32x32.png", 32)
    save_png("res/64x64.png", 64)
    save_png("res/128x128.png", 128)
    save_png("res/128x128@2x.png", 256)
    save_png("flutter/assets/icon.png", 512)
    save_logo("logo-light-source.png", "flutter/assets/logo_light.png")
    save_logo("logo-dark-source.png", "flutter/assets/logo_dark.png")


if __name__ == "__main__":
    main()
