# Security policy

## Supported versions

Security fixes go into the newest version only. Please update before you report.

| Part of the app | Supported version |
| --- | --- |
| The app for Windows | the [latest release](https://github.com/vladpereverzyev/rustdesk/releases/latest) |

## Reporting a vulnerability

Please do not open a public issue for a security problem. Report it privately instead:

- with Report a vulnerability in the
  [Security tab](https://github.com/vladpereverzyev/rustdesk/security) of this repository, or
- by email to info@vladpereverzyev.com, with "Remote desktop security" in the subject.

Tell what is affected (which version), how to reproduce it and what an attacker could do with
it. A proof of concept helps, but please do not access data that is not yours.

You get an answer within 7 days. Once the problem is confirmed, a fix is released as soon as
possible and you are credited in the release notes unless you prefer otherwise. Please keep the
details private until the fix is out.

## What is in scope

- The files of this app: `res/vladpereverzyev/`, including the updater, and the build and
  release workflow `.github/workflows/build.yml`.
- A problem that only this app has, for example because of how it is built.

A problem in the remote desktop code that RustDesk also has belongs to RustDesk: follow the
[RustDesk security policy](docs/SECURITY.md). This app gets the fix with the next merge
from `master`.

## How the code is checked

CodeQL checks the workflows and the Python scripts on every push and pull request. The Rust and
Dart code is the code of RustDesk, which checks it in its own repository.
