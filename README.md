# VirtualPort

[![Build & Release](https://github.com/vladpereverzyev/rustdesk/actions/workflows/build.yml/badge.svg)](https://github.com/vladpereverzyev/rustdesk/actions/workflows/build.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENCE)

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/vladpereverzyev/rustdesk/blob/virtualport/README.md)

Remote desktop for the labs and clinics that work with Vladyslav Pereverzyev, based on RustDesk.

VirtualPort is RustDesk with its own name and the VP logo. I use it to reach the computer of a
lab or a clinic when a case needs help and a customer can use it to reach mine. It works on the
same network as RustDesk, so it also connects to computers that run the original RustDesk, in
both directions.

## Install

| Where | How |
| --- | --- |
| Windows 10 and 11, 64 bit | `virtualport.exe` from the [latest release](https://github.com/vladpereverzyev/rustdesk/releases/latest) |

Until the first release, the exe of each build is attached to its run in
[Actions](https://github.com/vladpereverzyev/rustdesk/actions/workflows/build.yml).

## How to use it

- Open `virtualport.exe`. On the left you see the ID and a one-time password of this computer:
  give them to the person who helps you.
- To reach another computer, type its ID on the right and click Connect.
- To reach a computer when nobody sits in front of it, install VirtualPort on it (the button in
  the app) and set a permanent password in Settings, Security.

Allow a connection only to people you know. Somebody who has the ID and the password can see the
screen, use the mouse and open the files of that computer.

## What is in it

This branch keeps the RustDesk code as it is. The VirtualPort changes live in two places:

- `res/virtualport/brand.py` sets the app name and the Windows file details and makes the icons
  and logos from the images in `res/virtualport/`.
- `.github/workflows/build.yml` builds the Windows x64 exe on every push to this branch and
  publishes a release for every `v*` tag.

The `master` branch follows [rustdesk/rustdesk](https://github.com/rustdesk/rustdesk). New
RustDesk versions are merged from `master` into `virtualport`.

The build leaves out the usbmmidd virtual display driver that RustDesk ships, because it is a
third-party binary without a clear license to pass it on. Without it VirtualPort cannot add a
virtual screen to a computer that has no monitor.

To build it yourself, follow the [RustDesk build guide](https://rustdesk.com/docs/en/dev/build/)
and run `python res/virtualport/brand.py` before the build (it needs `pip install pillow`).

## Code signing

The exe is built from this branch by the [Build & Release](.github/workflows/build.yml)
workflow. It is not signed yet, so the first time Windows SmartScreen shows a blue warning: click
"More info", then "Run anyway".

## Contributing

This branch only holds the VirtualPort name, icons and build. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) first. Bugs and
ideas for the remote desktop itself belong to
[RustDesk](https://github.com/rustdesk/rustdesk/issues). Security problems go to the
[security policy](SECURITY.md), not to a public issue.

## Support

Questions about VirtualPort: see [SUPPORT.md](SUPPORT.md) or write to info@vladpereverzyev.com.

If you want to support the remote desktop itself, support
[RustDesk](https://github.com/sponsors/rustdesk), the people who write it.

## License

Copyright (C) 2026 Vladyslav Pereverzyev for the VirtualPort changes. RustDesk is Copyright (C)
Purslane Tech Pte. Ltd. and the RustDesk contributors.

VirtualPort is a modified version of RustDesk, changed from November 2026 on, and is released
under the [GNU Affero General Public License v3.0](LICENCE). You can use, study, modify and share
it for free. If you distribute a modified version or offer it to users over a network you must
publish your source code under the same license. The source code of every VirtualPort build is
this branch. Each release on GitHub also comes with the source code of the tag it was built from.

The name "VirtualPort", the VP logo and the Vladyslav Pereverzyev signature in
`res/virtualport/` are not covered by the AGPL-3.0 and may not be used for modified versions
without permission.

RustDesk is a trademark of its owners. VirtualPort is not affiliated with or endorsed by the
RustDesk project. Other product names and trademarks belong to their owners.

Third-party components keep their own licenses. See [NOTICE](NOTICE) and
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
