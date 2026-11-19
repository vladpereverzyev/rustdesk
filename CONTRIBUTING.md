# Contributing

The Vladyslav Pereverzyev remote desktop is RustDesk with my name, theme, updates and Windows
build. This repository only adds those parts, so most changes belong somewhere else.

## Where a change goes

- A bug or an idea for the remote desktop itself (connection, screen, keyboard, file transfer,
  settings): open it at [RustDesk](https://github.com/rustdesk/rustdesk). Once RustDesk ships
  it, this app gets it with the next merge from `master`.
- A problem with the name, icons, theme, updates or build of this app: open an
  [issue](https://github.com/vladpereverzyev/rustdesk/issues/new/choose) here.
- A security problem: follow the [security policy](SECURITY.md), not a public issue.

The guide of RustDesk for code changes is in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Before you open a pull request

- Open it against the `vladpereverzyev` branch, not `master`. `master` only follows RustDesk.
- Keep the RustDesk code as it is. The changes of this app go in `res/vladpereverzyev/` and
  `.github/workflows/build.yml`, so new RustDesk versions merge without conflicts.
- Write everything in English: code, comments, commit messages and the pull request.
- Contributions are accepted under the [AGPL-3.0](LICENCE), the license of the project.
