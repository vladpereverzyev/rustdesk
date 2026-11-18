# Contributing to VirtualPort

VirtualPort is RustDesk with its own name, icons and Windows build. This repository only adds
those parts, so most changes belong somewhere else.

## Where a change goes

- A bug or an idea for the remote desktop itself (connection, screen, keyboard, file transfer,
  settings): open it at [RustDesk](https://github.com/rustdesk/rustdesk). Once RustDesk ships
  it, VirtualPort gets it with the next merge from `master`.
- A problem with the VirtualPort name, icons, logo or build: open an
  [issue](https://github.com/vladpereverzyev/rustdesk/issues/new/choose) here.
- A security problem: follow the [security policy](SECURITY.md), not a public issue.

The guide of RustDesk for code changes is in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Before you open a pull request

- Open it against the `virtualport` branch, not `master`. `master` only follows RustDesk.
- Keep the RustDesk code as it is. The VirtualPort changes go in `res/virtualport/` and
  `.github/workflows/build.yml`, so new RustDesk versions merge without conflicts.
- Write everything in English: code, comments, commit messages and the pull request.
- Contributions are accepted under the [AGPL-3.0](LICENCE), the license of the project.
