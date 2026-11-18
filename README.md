# VirtualPort

[![Build](https://img.shields.io/github/actions/workflow/status/vladpereverzyev/rustdesk/virtualport-windows.yml?branch=virtualport&label=build)](https://github.com/vladpereverzyev/rustdesk/actions/workflows/virtualport-windows.yml)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENCE)

[![en](https://img.shields.io/badge/lang-en-lightgrey)](README.md)

Remote desktop for the customers of Vladyslav Pereverzyev, based on RustDesk.

VirtualPort is RustDesk with its own name and the VP logo. I use it to reach the computer of a
lab or a clinic when a case needs help and a customer can use it to reach mine. It works on the
same network as RustDesk, so it also connects to computers that run the original RustDesk, in
both directions.

## Download

VirtualPort runs on Windows 10 and 11, 64 bit. Download `virtualport.exe` from the
[releases](https://github.com/vladpereverzyev/rustdesk/releases). Until the first release, the
exe of each build is attached to its run in
[Actions](https://github.com/vladpereverzyev/rustdesk/actions/workflows/virtualport-windows.yml).

The exe has no code signing certificate, so the first time Windows SmartScreen shows a blue
warning. Click "More info", then "Run anyway".

## How to use it

- Open `virtualport.exe`. On the left you see the ID and a one-time password of this computer:
  give them to the person who helps you.
- To reach another computer, type its ID on the right and click Connect.
- To reach a computer when nobody sits in front of it, install VirtualPort on it (the button in
  the app) and set a permanent password in Settings, Security.

## How it is built

This branch keeps the RustDesk code as it is. The changes live in two places:

- `res/virtualport/brand.py` sets the app name and the Windows file details and makes the icons
  and logos from the images in `res/virtualport/`.
- `.github/workflows/virtualport-windows.yml` builds the Windows x64 exe on every push to this
  branch and publishes a release for every `v*` tag.

The `master` branch follows [rustdesk/rustdesk](https://github.com/rustdesk/rustdesk). New
RustDesk versions are merged from `master` into `virtualport`.

To build it yourself, follow the [RustDesk build guide](https://rustdesk.com/docs/en/dev/build/)
and run `python res/virtualport/brand.py` before the build (it needs `pip install pillow`).

## Contributing

This branch only holds the VirtualPort name, icons and build. Bugs and ideas for the remote
desktop itself belong to [RustDesk](https://github.com/rustdesk/rustdesk/issues). For anything
about VirtualPort, write to info@vladpereverzyev.com.

## Support

Questions about VirtualPort: info@vladpereverzyev.com or
[vladpereverzyev.com](https://www.vladpereverzyev.com).

## License

VirtualPort is a modified version of RustDesk, changed from November 2026 on, and is released
under the GNU Affero General Public License v3.0 (AGPL-3.0), see [LICENCE](LICENCE). The source
code of every VirtualPort build is this branch. Each release on GitHub also comes with the source
code of the tag it was built from.

Copyright (C) 2026 Vladyslav Pereverzyev for the VirtualPort changes. RustDesk is Copyright (C)
Purslane Tech Pte. Ltd. and the RustDesk contributors.

RustDesk is a trademark of its owners. VirtualPort is not affiliated with or endorsed by the
RustDesk project. The VP logo and the Vladyslav Pereverzyev signature in `res/virtualport/` are
not covered by the AGPL: a fork of VirtualPort must use its own name and logo.
