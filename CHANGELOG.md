# Changelog

What changed in each version of the Vladyslav Pereverzyev remote desktop. The downloads of every
version are on the [releases page](https://github.com/vladpereverzyev/rustdesk/releases). The
changes to the remote desktop itself are in the
[RustDesk releases](https://github.com/rustdesk/rustdesk/releases).

## 1.0.4 (2026-11-19)

- The home window no longer shows the Quit button: the window closes from the title bar.
- The Unlock Settings button in the Security and Network pages lines up with the cards below it.
- The Install printer button fits inside its card instead of running off the right edge, and the printer button and messages drop the app name from their text.

## 1.0.3 (2026-11-19)

- The online status line stays centred in its band at the bottom of the window.
- The install window drops the Cancel button: the title bar already has a button to close it.
- Windows shows the app in Installed apps as "Vladyslav Pereverzyev", both the name and the author, instead of the technical "vladpereverzyev".
- The downloaded exe is "VladyslavPereverzyev.exe". The name inside the app, the service and the install folder stays "vladpereverzyev".

## 1.0.2 (2026-11-19)

- The window that asks to let a session in is built like the home window: same size, the app
  icon and name in the title bar, the logo, a title, the ID and the permissions on the azure
  line, grey icons, round buttons and the status line at the bottom. It shows the ID of the
  other side instead of its account name or e-mail address.
- The update window says only that a new version is available, without the name of the app,
  and shows Later and Download as two buttons of the same size side by side. The home window
  no longer repeats the update in a card at the bottom.
- About: a line says that the app comes as it is, without warranty, and points to the README
  and the licence for the details. It is translated into every language of the app.
- The app is always dark: the Theme card is gone from the General page and a light or system
  theme saved before is ignored.

## 1.0.1 (2026-11-19)

- Settings: the Stop button of the Service card and the Change ID button sit on the same line
  as the card title, at the right.
- About: the links start at the left edge of the card text, like every other text.
- The window keeps its size: no maximize button, and neither a double click on the title bar
  nor Win+Up or snapping to the screen edge enlarges it.
- The install puts the shortcuts on the Desktop and in the Start menu as "Vladyslav
  Pereverzyev" and removes the old "vladpereverzyev" one.

## 1.0.0 (2026-11-19)

- First build for Windows x64, based on RustDesk 1.5.3, with my name, the VP icon and my
  signature in the app. The exe is `vladpereverzyev.exe`.
- Dark theme in the colours of vladpereverzyev.com with the Jost font: light titles, small
  capital labels, pill buttons, icons of one size and colour, the signature as a link to the
  site.
- The taskbar, the install window and the settings show "Vladyslav Pereverzyev". The status
  line says only whether the computer is online, without the tip to set up a server.
- One type scale in every window: 13 for text, buttons, fields and menus, 11 for small notes,
  20 light for titles, all in Jost.
- Drop-down menus in the panel colour, with round corners and the width of their field.
- Cards with corners of 10 and a thin light line, text in the soft white of the site and
  more spaced capital labels, as on vladpereverzyev.com.
- The app updates itself from the releases of this repository, after checking the size and the
  SHA-256 checksum of the download.
- A window asks before every update: nothing is downloaded or installed until the user
  presses Update. The "Auto update" setting is gone.
- The Address book and Accessible devices tabs are hidden: they need a RustDesk Pro server and
  on the public server they only showed an error.
- The app only lets its computer be reached: a small window with the ID, the password and the
  online status. The field to reach another computer, the recent sessions, the favourites, the
  Display settings and the options for outgoing sessions are gone and the app refuses to open
  an outgoing connection.
- No sign-in: the Account page and the sign-in window are gone.
- The licence link of the install window opens the licence of this app instead of the privacy
  policy of rustdesk.com.
- No Home and Settings tabs: the menu button opens the settings in the same small window, as a
  list of pages with a back arrow, with the same margins and type as the rest of the app.
- One click on the ID or the password copies it.
- The About page shows the version of this app next to the RustDesk one and explains what the
  app is for, how to use it, how a session is protected, how updates work and which servers it
  uses, with links to the site, the source code, the privacy notes and the licence. The RustDesk
  copyright and the licence notice stay, without the RustDesk slogan.
- The About page and the Later button are translated into every language of the app.
- "Powered by RustDesk" moves from the main screen to the About page, next to the RustDesk
  copyright, with a line on what this app changes and where its source code is.
- The downloaded exe unpacks to its own folder, apart from a portable RustDesk.
- The usbmmidd virtual display driver of RustDesk is left out.
