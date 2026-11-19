# Third-party notices

The Vladyslav Pereverzyev remote desktop is licensed under the AGPL-3.0 (see [LICENCE](LICENCE)).
It is built from RustDesk and ships the following third-party components. Each one keeps its own
license.

| Component | Version | License | Files in this repository |
| --- | --- | --- | --- |
| [RustDesk](https://github.com/rustdesk/rustdesk) | 1.5.3 | AGPL-3.0 | everything outside `res/vladpereverzyev/` and the files of this app listed in `README.md` |
| [hbb_common](https://github.com/rustdesk/hbb_common) | the commit pinned in `libs/hbb_common` | AGPL-3.0 | `libs/hbb_common/` (git submodule) |
| [Flutter](https://github.com/flutter/flutter) with the [RustDesk engine build](https://github.com/rustdesk/engine) | 3.24.5 | BSD-3-Clause | downloaded at build time |
| [FFmpeg](https://ffmpeg.org) | 7.1.1 | LGPL-2.1-or-later | port in `res/vcpkg/ffmpeg/`, built at build time |
| [libvpx](https://chromium.googlesource.com/webm/libvpx) | 1.15.2 | BSD-3-Clause | port in `res/vcpkg/libvpx/`, built at build time |
| [aom](https://aomedia.googlesource.com/aom) | 3.14.1 | BSD-2-Clause | port in `res/vcpkg/aom/`, built at build time |
| [libyuv](https://chromium.googlesource.com/libyuv/libyuv) | 1857 | BSD-3-Clause | port in `res/vcpkg/libyuv/`, built at build time |
| [Opus](https://opus-codec.org) | 1.5.2 | BSD-3-Clause | port in `res/vcpkg/opus/`, built at build time |
| [Intel Media SDK dispatcher](https://github.com/lu-zero/mfx_dispatch) | 1.35.1 | BSD-3-Clause | port in `res/vcpkg/mfx-dispatch/`, built at build time |
| [libjpeg-turbo](https://libjpeg-turbo.org) | from vcpkg | IJG, BSD-3-Clause and Zlib | `vcpkg.json`, built at build time |
| [Jost](https://github.com/indestructible-type/Jost) | 3.5 (Light, Book, Medium, Semi) | OFL-1.1 | `res/vladpereverzyev/fonts/` |
| [libsodium](https://libsodium.org) | from the `sodiumoxide` crate | ISC | downloaded at build time |

The Rust crates and the Dart packages keep their own licenses. Their versions are pinned in
`Cargo.lock` and `flutter/pubspec.lock`.

RustDesk ships the usbmmidd virtual display driver with its Windows builds. This app leaves
it out (see `README.md`).
