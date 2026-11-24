#!/usr/bin/env python3
"""Turn a RustDesk checkout into the Vladyslav Pereverzyev remote desktop: name, theme, icons.

Run it from the repository root before the build, after the submodules are checked out:

    pip install pillow
    python res/vladpereverzyev/brand.py

The changes are applied to the working tree only, so the upstream sources stay untouched
in git and the fork can follow RustDesk with a plain merge.

Maintenance after a RustDesk update:

Every patch matches an exact piece of RustDesk source. When a patch no longer finds its
match the script stops, naming the file and the text it looked for, so a broken patch fails
the build instead of producing a wrong app. The script runs as the first step of the build,
so a break shows in about a minute, not after the whole compile. After merging a new RustDesk
into this branch, run the script, fix what it reports one patch at a time, then run it again.

The patches most likely to break, to check first:
- about_page() rewrites the whole _AboutState class, up to the //#endregion marker.
- connection_window() rewrites whole blocks of server_page.dart: buildConnectionCard up to
  class _AppIcon, the connection manager header build and the button builder. A refactor of
  that page breaks these.
- theme(), updates() and polish() insert whole blocks into desktop_home_page.dart and
  desktop_setting_page.dart: the help cards and the narrow settings menu.
- replace_all() calls carry an exact count (DARK_COLOURS, the icon sizes). When RustDesk adds
  or removes one use the count stops matching: update the number.
- about-translations.json keeps one entry per text of ABOUT_TEXTS, for every language.
"""

from pathlib import Path
import json
import os
import re
import shutil
import sys

from PIL import Image, ImageDraw

# APP_NAME is the technical name RustDesk makes the exe, the service, the install folder and
# the vladpereverzyev:// links from (letters only). DISPLAY_NAME is what people read.
APP_NAME = "vladpereverzyev"
EXE_NAME = "vladpereverzyev"
DISPLAY_NAME = "Vladyslav Pereverzyev"

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

ICON_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
ICON_MARGIN = 0.06

# Colours of vladpereverzyev.com: azure for links, accents and buttons, its lighter shade for
# the small capital labels and midnight for the install banner.
AZURE = "2791CB"
AZURE_STRONG = "1D76A8"
AZURE_LIGHT = "57ABD8"
BUTTON_TEXT = "04121C"
ICON = "7D90A0"  # the dim grey of the site, for every icon at rest
MIDNIGHT = (1, 30, 46)
PANEL = (6, 48, 73)

# RustDesk dark theme colour -> site colour, and how many times RustDesk uses it in common.dart.
DARK_COLOURS = [
    ("18191E", "011E2E", 2),  # window background -> midnight
    ("24252B", "04263A", 5),  # side panel, cards and fields -> panel
    ("121212", "01151F", 1),
    ("3F3F3F", "063049", 1),  # highlight -> panel 2
    ("555555", "2F5872", 1),  # border
]

JOST = [("Jost-300-Light", 300), ("Jost-400-Book", 400), ("Jost-500-Medium", 500), ("Jost-600-Semi", 600)]
LOGO_MAX = (300, 60)  # loadLogo() in flutter/lib/common.dart shows at most 300 x 60


def replace_once(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    # A non-empty replacement already in place means the patch ran before (idempotent re-run).
    # A removal (empty new) has no such marker, so it must always find its target or fail loudly,
    # never skip in silence.
    if new and new in text and old not in text:
        print(f"already branded: {path}")
        return
    if text.count(old) != 1:
        sys.exit(f"expected exactly one {old!r} in {path}, found {text.count(old)}")
    file.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched: {path}")


def replace_all(path, old, new, count):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    if new in text and old not in text:
        print(f"already branded: {path}")
        return
    if text.count(old) != count:
        sys.exit(f"expected {count} of {old!r} in {path}, found {text.count(old)}")
    file.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched: {path}")


def sub_once(path, pattern, repl):
    # For code where only the indentation between the tokens may change upstream.
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    new_text, n = re.subn(pattern, repl, text, flags=re.DOTALL)
    if n != 1:
        sys.exit(f"expected one match in {path}, found {n} (run on a clean checkout): {pattern!r}")
    file.write_text(new_text, encoding="utf-8")
    print(f"patched: {path}")


def theme():
    common = "flutter/lib/common.dart"
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"

    # Always dark, in the colours of vladpereverzyev.com: a saved light or system theme is
    # ignored, no other window can switch the theme and the Theme card of the General page is
    # gone.
    replace_once(
        common,
        "return themeModeFromString(bind.mainGetLocalOption(key: kCommConfKeyTheme));",
        "return ThemeMode.dark;",
    )
    replace_once(common, "    Get.changeThemeMode(mode);",
                 "    mode = ThemeMode.dark;\n    Get.changeThemeMode(mode);")
    replace_once("flutter/lib/desktop/pages/desktop_setting_page.dart",
                 "        if (!isWeb) service(),\n        theme(),\n", "        if (!isWeb) service(),\n")
    for old, new, count in DARK_COLOURS:
        replace_all(common, f"Color(0xFF{old})", f"Color(0xFF{new})", count)
    replace_once(
        common,
        "brightness: Brightness.dark,\n    hoverColor: Color.fromARGB(255, 45, 46, 53),",
        "brightness: Brightness.dark,\n    hoverColor: Color.fromARGB(255, {}, {}, {}),".format(*PANEL),
    )

    # Type as on vladpereverzyev.com: Jost everywhere, titles light (300) with tight spacing,
    # text regular (400), small labels in spaced capitals, buttons regular on a pill. Sizes:
    # 11 for labels, 13 for text and buttons, 20 for titles, the ID and the password.
    replace_once(
        common,
        "useMaterial3: false,\n    brightness: Brightness.light,",
        "useMaterial3: false,\n    fontFamily: 'Jost',\n    brightness: Brightness.light,",
    )
    replace_once(
        common,
        "useMaterial3: false,\n    brightness: Brightness.dark,",
        "useMaterial3: false,\n    fontFamily: 'Jost',\n    brightness: Brightness.dark,",
    )
    title = "fontSize: 20, fontWeight: FontWeight.w300, letterSpacing: -0.4"
    replace_once(
        common,
        "titleLarge: TextStyle(fontSize: 19, color: Colors.black87),",
        f"titleLarge: TextStyle({title}, color: Colors.black87),",
    )
    replace_once(common, "titleLarge: TextStyle(fontSize: 19),", f"titleLarge: TextStyle({title}),")
    replace_once(
        common,
        "bodySmall: TextStyle(fontSize: 12, color: Colors.black87, height: 1.25),",
        "bodySmall: TextStyle(fontSize: 13, color: Colors.black87, height: 1.4),",
    )
    replace_once(
        common,
        "bodySmall: TextStyle(fontSize: 12, height: 1.25),",
        "bodySmall: TextStyle(fontSize: 13, height: 1.4),",
    )
    # The site spaces its capitals by 0.24 em; 2.2 (0.2 em) still fits "PASSWORD MONOUSO" in
    # the side panel.
    label = f"fontSize: 11, letterSpacing: 2.2, color: Color(0xFF{AZURE_LIGHT})"
    sub_once(
        home,
        r'translate\("ID"\),(\s*)style: TextStyle\(\s*fontSize: 14,\s*color: Theme\.of\(context\)\s*'
        r'\.textTheme\s*\.titleLarge\s*\?\.color\s*\?\.withOpacity\(0\.5\)\),',
        r'translate("ID").toUpperCase(),\1style: TextStyle(' + label + "),",
    )
    sub_once(
        home,
        r'translate\("One-time Password"\),(\s*)style: TextStyle\(\s*fontSize: 14, color: textColor\?\.withOpacity\(0\.5\)\),',
        r'translate("One-time Password").toUpperCase(),\1style: TextStyle(' + label + "),",
    )
    sub_once(
        home,
        r'(contentPadding: EdgeInsets\.only\(top: 10, bottom: 10\),\s*\),\s*style: TextStyle\(\s*)fontSize: 22,',
        r"\1fontSize: 20, fontWeight: FontWeight.w300,",
    )
    sub_once(
        home,
        r'(controller: model\.serverPasswd,.*?)style: TextStyle\(fontSize: 15\),',
        r"\1style: TextStyle(fontSize: 20, fontWeight: FontWeight.w300),",
    )
    sub_once(
        home,
        r'fontWeight: FontWeight\.bold,(\s*)fontSize: 15\),',
        r"fontWeight: FontWeight.w400,\1fontSize: 13),",
    )
    sub_once(
        home,
        r'(decoration:\s*TextDecoration\.underline,\s*color: Colors\.white,\s*)fontSize: 12\),',
        r"\1fontSize: 13),",
    )
    sub_once(
        "flutter/lib/desktop/pages/connection_page.dart",
        r"fontFamily: 'WorkSans',(\s*)fontSize: 22,",
        r"fontFamily: 'Jost',\1fontSize: 20,\1fontWeight: FontWeight.w300,",
    )
    replace_once(
        common,
        "?.copyWith(fontSize: 9, decoration: TextDecoration.underline),",
        "?.copyWith(fontSize: 11, decoration: TextDecoration.underline),",
    )
    pill = (
        f"        foregroundColor: Color(0xFF{BUTTON_TEXT}),\n"
        "        textStyle: TextStyle(fontFamily: 'Jost', fontSize: 13, fontWeight: FontWeight.w400),\n"
        "        shape: StadiumBorder(),\n"
    )
    rounded = "        shape: RoundedRectangleBorder(\n          borderRadius: BorderRadius.circular(8.0),\n        ),\n"
    replace_once(
        common,
        "        backgroundColor: MyTheme.accent,\n" + rounded + "      ),\n    ),\n    outlinedButtonTheme",
        "        backgroundColor: MyTheme.accent,\n" + pill + "      ),\n    ),\n    outlinedButtonTheme",
    )
    disabled = "        disabledForegroundColor: Colors.white70,\n        disabledBackgroundColor: Colors.white10,\n"
    replace_once(
        common,
        "        backgroundColor: MyTheme.accent,\n        foregroundColor: Colors.white,\n" + disabled + rounded,
        "        backgroundColor: MyTheme.accent,\n" + disabled + pill,
    )

    # The peer tabs on the left were 24 and the tools on the right 18: all 20. The star glyph
    # fills less of its box than the others, so it gets 23 to look the same size.
    peers = "flutter/lib/common/widgets/peer_tab_page.dart"
    replace_all(peers, "size: 18,", "size: 20,", 6)
    replace_once(
        peers,
        "child: Icon(model.tabIcon(t), color: color)",
        "child: Icon(model.tabIcon(t), color: color, size: model.tabIcon(t) == Icons.star ? 23 : 20)",
    )
    replace_all(
        peers,
        "Icons.search_rounded,\n",
        "Icons.search_rounded,\n              size: 20,\n",
        2,
    )

    # The refresh and edit icons of the password were 22 in a fixed light grey, the menu of the
    # ID 20 in half the text colour: all the same colour, the pencil as a thinner outline.
    sub_once(
        home,
        r"Icons\.refresh,(\s*color: refreshHover\.value\s*\? textColor\s*: )Color\(0xFFDDDDDD\),(\s*)size: 22,",
        r"Icons.refresh_rounded,\1Color(0xFF" + ICON + r"),\2size: 20,",
    )
    sub_once(
        home,
        r"Icons\.edit,(\s*color: editHover\.value\s*\? textColor\s*: )Color\(0xFFDDDDDD\),(\s*)size: 22,",
        r"Icons.edit_outlined,\1Color(0xFF" + ICON + r"),\2size: 18,",
    )
    replace_once(
        home,
        "color: hover.value ? textColor : textColor?.withOpacity(0.5),",
        f"color: hover.value ? textColor : Color(0xFF{ICON}),",
    )

    # The help icon sat about 1.5 below the middle of the light title: lifted and in the icon grey.
    replace_once(
        "flutter/lib/common/widgets/connection_page_title.dart",
        "              color: Theme.of(context)\n"
        "                  .textTheme\n"
        "                  .titleLarge\n"
        "                  ?.color\n"
        "                  ?.withOpacity(0.5),\n"
        "            ),\n"
        "          ),\n",
        f"              color: Color(0xFF{ICON}),\n"
        "            ),\n"
        "          ).marginOnly(bottom: 3),\n",
    )

    # The search button had the pale hint colour while its neighbours have the normal icon colour.
    replace_once(
        peers,
        "              size: 20,\n              color: Theme.of(context).hintColor,\n            ));",
        "              size: 20,\n            ));",
    )
    # The arrow glyph next to Connect sits off centre in its circle: a centred arrow instead.
    replace_all(
        "flutter/lib/desktop/pages/connection_page.dart",
        "Icon(IconFont.more, size: 14)",
        "Icon(Icons.keyboard_arrow_down_rounded, size: 20)",
        2,
    )

    # At 12 the lines of the settings menu glyph come out thinner and paler than minimise,
    # maximise and close next to it; at 14 they match. All four get the icon grey.
    replace_once(
        "flutter/lib/desktop/pages/desktop_tab_page.dart",
        "                  icon: IconFont.menu,\n",
        "                  icon: IconFont.menu,\n                  iconSize: 14,\n",
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        "unSelectedIconColor: Color.fromARGB(255, 255, 255, 255),",
        f"unSelectedIconColor: Color(0xFF{ICON}),",
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        "unSelectedTextColor: Color.fromARGB(255, 192, 192, 192),",
        f"unSelectedTextColor: Color(0xFF{ICON}),",
    )

    # "Powered by RustDesk" leaves the main screen. The About page keeps the RustDesk copyright
    # and license and says what the app is and where its source is (AGPL-3.0 sections 5
    # and 13). The line is not passed through translate(), which would swap "RustDesk" for
    # the app name.
    replace_once(
        home,
        "      if (bind.isCustomClient())\n"
        "        Align(\n"
        "          alignment: Alignment.center,\n"
        "          child: loadPowered(context),\n"
        "        ),\n",
        "",
    )
    settings = "flutter/lib/desktop/pages/desktop_setting_page.dart"
    replace_once(
        settings,
        "Purslane Tech Pte. Ltd.\\n$license',\n"
        "                            style: const TextStyle(color: Colors.white),\n"
        "                          ),\n",
        "Purslane Tech Pte. Ltd.\\n$license',\n"
        "                            style: const TextStyle(color: Colors.white),\n"
        "                          ),\n"
        "                          Text(\n"
        "                            'This remote desktop is based on RustDesk (github.com/rustdesk/rustdesk) and '\n"
        "                            'changed by Vladyslav Pereverzyev from November 2026 on. Source code: '\n"
        "                            'github.com/vladpereverzyev/rustdesk',\n"
        "                            style: const TextStyle(color: Colors.white),\n"
        "                          ).marginOnly(top: 8),\n",
    )
    replace_once(settings, "BoxDecoration(color: Color(0xFF2c8cff))", f"BoxDecoration(color: Color(0xFF{AZURE_STRONG}))")
    replace_once(settings, "fontWeight: FontWeight.w800,\n                                color: Colors.white),",
                 "fontWeight: FontWeight.w500,\n                                color: Colors.white),")

    # The signature is a link to vladpereverzyev.com and lines up with the text of the side
    # panel (20), with some air above and below it.
    replace_once(
        common,
        "          return Container(\n"
        "            constraints: BoxConstraints(maxWidth: 300, maxHeight: 60),\n"
        "            child: image,\n"
        "          ).marginOnly(left: 12, right: 12, top: 12);",
        "          return MouseRegion(\n"
        "            cursor: SystemMouseCursors.click,\n"
        "            child: GestureDetector(\n"
        "              onTap: () => launchUrl(Uri.parse('https://vladpereverzyev.com')),\n"
        "              child: Container(\n"
        "                width: double.infinity,\n"
        "                alignment: Alignment.center,\n"
        "                constraints: BoxConstraints(maxWidth: 300, maxHeight: 60),\n"
        "                child: image,\n"
        "              ),\n"
        "            ),\n"
        "          ).marginOnly(left: 34, right: 34, top: 40, bottom: 30);",
    )

    # The title bar takes the midnight background of the site, with a thin slate line below it.
    replace_once(
        common,
        "    scaffoldBackgroundColor: Color(0xFF011E2E),\n",
        "    scaffoldBackgroundColor: Color(0xFF011E2E),\n    dividerColor: Color(0xFF2F5872),\n"
        f"    iconTheme: IconThemeData(color: Color(0xFF{ICON})),\n",
    )
    replace_once(
        "flutter/lib/desktop/pages/desktop_tab_page.dart",
        "            backgroundColor: Theme.of(context).colorScheme.background,\n            body: DesktopTab(",
        "            backgroundColor: Theme.of(context).scaffoldBackgroundColor,\n            body: DesktopTab(",
    )
    sub_once(
        home,
        r"borderColor: Colors\.white,(\s*)textSize: 20,(\s*)radius: 10,",
        r"borderColor: Colors.white30,\1textSize: 13,\2radius: 16,",
    )
    sub_once(
        home,
        r"height: 1\.5,(\s*color: Colors\.white,\s*fontWeight: FontWeight\.normal,\s*fontSize: 13\),\s*\)\.marginOnly\(bottom: )20\)",
        r"height: 1.4,\g<1>14)",
    )
    connection = "flutter/lib/desktop/pages/connection_page.dart"
    sub_once(connection, r"(SizedBox\(\s*)height: 28\.0,(\s*child: ElevatedButton\()", r"\1height: 32.0,\2")
    sub_once(connection, r"height: 28\.0,(\s*)width: 28\.0,", r"height: 32.0,\1width: 32.0,")
    sub_once(
        connection,
        r"(width: 32\.0,\s*decoration: BoxDecoration\(\s*border: Border\.all\(color: Theme\.of\(context\)\.dividerColor\),\s*"
        r"borderRadius: BorderRadius\.circular\()8\)",
        r"\g<1>16)",
    )
    sub_once(connection, r"(ClipRRect\(\s*borderRadius: BorderRadius\.circular\()5\)", r"\g<1>8)")

    # The connect card spans the whole width, with the 20 margin of the side panel all round.
    replace_once(connection, "      width: 320 + 20 * 2,\n", "")
    sub_once(
        connection,
        r"Flexible\(child: _buildRemoteIDTextField\(context\)\),(\s*\],\s*\))\.marginOnly\(top: 22\),",
        r"Expanded(child: _buildRemoteIDTextField(context)),\1.marginOnly(top: 20, right: 20),",
    )
    sub_once(
        connection,
        r"Divider\(\)\.paddingOnly\(right: 12\),(\s*Expanded\(child: PeerTabPage\(\)\),\s*\],\s*\))\.paddingOnly\(left: 12\.0\)\),",
        r"Divider().paddingOnly(right: 20),\1.paddingOnly(left: 20.0)),",
    )

    # The install card sits at the bottom of the side panel instead of right under the password.
    file = ROOT / home
    text = file.read_text(encoding="utf-8")
    m = re.search(r"\n(      FutureBuilder<Widget>\(\n        future: Future\.value\(\n.*?\n      \),\n)    \];", text, re.DOTALL)
    if m is None:
        sys.exit(f"help cards not found in {home}")
    cards = m.group(1).strip().rstrip(",")
    text = text.replace(m.group(0), "\n      if (isIncomingOnly) helpCards,\n    ];", 1)
    text = text.replace(
        "    final children = <Widget>[\n      if (!isOutgoingOnly) buildPresetPasswordWarning(),",
        f"    final helpCards = {cards};\n"
        "    final children = <Widget>[\n      if (!isOutgoingOnly) buildPresetPasswordWarning(),",
        1,
    )
    old = "                Expanded(child: Container())\n              ],"
    if text.count(old) != 1 or "final helpCards" not in text:
        sys.exit(f"side panel layout not found in {home}")
    text = text.replace(old, "                Expanded(child: Container()),\n                if (!isIncomingOnly) helpCards,\n              ],", 1)
    file.write_text(text, encoding="utf-8")
    print(f"patched: {home}")

    # The install card stays (without installing, the helper sees a black screen at every
    # Windows permission prompt and cannot reach the computer when nobody is there), in two
    # short lines instead of four long ones.
    replace_once(
        "src/lang/it.rs",
        '("install_tip", "A causa del Controllo Account Utente (UAC), RustDesk potrebbe non funzionare correttamente come desktop remoto.\\nPer evitare questo problema, fai clic sul tasto qui sotto per installare RustDesk a livello di sistema."),',
        '("install_tip", "Installa il programma per l\'accesso senza nessuno al PC e per le richieste di permesso di Windows."),',
    )
    replace_once(
        "src/lang/en.rs",
        '("install_tip", "Due to UAC, RustDesk can not work properly as the remote side in some cases. To avoid UAC, please click the button below to install RustDesk to the system."),',
        '("install_tip", "Install the program for access when nobody is at the computer and for the permission prompts of Windows."),',
    )

    fonts = ROOT / "flutter/assets/fonts"
    fonts.mkdir(exist_ok=True)
    for name, _ in JOST:
        shutil.copyfile(HERE / "fonts" / f"{name}.ttf", fonts / f"{name}.ttf")
    entries = "".join(
        f"        - asset: assets/fonts/{name}.ttf\n          weight: {weight}\n" for name, weight in JOST
    )
    replace_once(
        "flutter/pubspec.yaml",
        "  fonts:\n    - family: GestureIcons\n",
        f"  fonts:\n    - family: Jost\n      fonts:\n{entries}    - family: GestureIcons\n",
    )


def polish():
    grey = f"Color(0xFF{ICON})"
    title = "fontSize: 20, fontWeight: FontWeight.w300, letterSpacing: -0.4"

    # The window title is what the taskbar shows and how a second start finds the open window
    # (main.cpp looks for the display name).
    replace_once(
        "flutter/lib/common.dart",
        "String getWindowName({WindowType? overrideType}) {\n  final name = bind.mainGetAppNameSync();",
        f"String getWindowName({{WindowType? overrideType}}) {{\n  const name = '{DISPLAY_NAME}';",
    )

    # Home and Settings tabs: 13 like the name next to them, icons 16 like the logo, white when
    # selected and the icon grey otherwise.
    tabs = "flutter/lib/desktop/widgets/tabbar_widget.dart"
    replace_once(
        tabs,
        "selectedTabIconColor: MyTheme.accent,\n      unSelectedTabIconColor: Color.fromARGB(255, 30, 65, 98),",
        f"selectedTabIconColor: Colors.white,\n      unSelectedTabIconColor: {grey},",
    )
    replace_once(
        tabs,
        "          isSelected ? widget.selectedIcon : widget.unselectedIcon,\n          size: _kIconSize,",
        "          isSelected ? widget.selectedIcon : widget.unselectedIcon,\n"
        "          size: widget.selectedIcon == Icons.build_sharp ||\n"
        "                  widget.selectedIcon == Icons.desktop_windows_sharp\n"
        "              ? 14\n"
        "              : 16,",
    )
    # Home and Settings use the filled glyph in both states, so they have the same shape and
    # only the colour tells the open tab. The wrench is diagonal and fills its whole box and the
    # monitor of a remote session is wide: at 14 they look as big as the house at 16. The Settings tab stays open, without a close mark.
    tab_page = "flutter/lib/desktop/pages/desktop_tab_page.dart"
    replace_once(
        tab_page,
        "          selectedIcon: Icons.build_sharp,\n          unselectedIcon: Icons.build_outlined,\n",
        "          selectedIcon: Icons.build_sharp,\n          unselectedIcon: Icons.build_sharp,\n"
        "          closable: false,\n",
    )
    replace_once(tab_page, "unselectedIcon: Icons.home_outlined,", "unselectedIcon: Icons.home_sharp,")
    replace_once(
        tabs,
        "              style: TextStyle(\n                  color: isSelected\n"
        "                      ? MyTheme.tabbar(context).selectedTextColor",
        "              style: TextStyle(\n                  fontSize: 13,\n                  color: isSelected\n"
        "                      ? MyTheme.tabbar(context).selectedTextColor",
    )
    # The same 5 between the logo and the name as between a tab icon and its label.
    replace_once(
        tabs,
        "style: TextStyle(fontSize: 13),\n                            ).marginOnly(left: 2))",
        "style: TextStyle(fontSize: 13),\n                            ).marginOnly(left: 5))",
    )
    # The close mark of a tab: the thin glyph, size and grey of the window's own close button.
    replace_once(
        tabs,
        "                  child: Icon(\n"
        "                    Icons.close,\n"
        "                    size: _kIconSize,\n"
        "                    color: tabSelected\n"
        "                        ? MyTheme.tabbar(context).selectedIconColor\n"
        "                        : MyTheme.tabbar(context).unSelectedIconColor,\n"
        "                  ),\n",
        "                  child: Icon(\n"
        "                    IconFont.close,\n"
        "                    size: _kActionIconSize,\n"
        "                    color: MyTheme.tabbar(context).unSelectedIconColor,\n"
        "                  ),\n",
    )
    replace_once(
        tabs,
        "                  hoverColor: MyTheme.tabbar(context).closeHoverColor,\n"
        "                  customBorder: const CircleBorder(),",
        "                  hoverColor: MyTheme.tabbar(context).hoverColor,\n"
        "                  customBorder: const CircleBorder(),",
    )

    # Status line: only whether the computer is online, without the tip to set up a server.
    replace_once(
        "flutter/lib/desktop/pages/connection_page.dart",
        "            if (!isIncomingOnly) setupServerWidget(),\n",
        "",
    )
    replace_once("src/lang/it.rs", '("Ready", "Pronto"),', '("Ready", "Online, pronto per la connessione"),')
    replace_once(
        "src/lang/en.rs",
        '("setup_server_tip", "For faster connection, please set up your own server"),',
        '("setup_server_tip", "For faster connection, please set up your own server"),\n'
        '        ("Ready", "Online, ready to connect"),',
    )

    # Install window: the name in the title bar, text 13, pill buttons, the info box in the
    # panel colours.
    install = "flutter/lib/desktop/pages/install_page.dart"
    # The install window has a close button in its title bar, so the Cancel button in the
    # button row is redundant.
    replace_once(
        install,
        "                  Obx(\n"
        "                    () => OutlinedButton.icon(\n"
        "                      icon: Icon(Icons.close_rounded, size: 16),\n"
        "                      label: Text(translate('Cancel')),\n"
        "                      onPressed: cancelEnabled.value\n"
        "                          ? () => windowManager.close()\n"
        "                          : null,\n"
        "                      style: buttonStyle,\n"
        "                    ).marginOnly(right: 10),\n"
        "                  ),\n",
        "",
    )
    replace_once(
        install,
        "            backgroundColor: Theme.of(context).colorScheme.background,\n"
        "            body: DesktopTab(controller: tabController)),",
        "            backgroundColor: Theme.of(context).scaffoldBackgroundColor,\n"
        "            body: DesktopTab(controller: tabController, showTitle: true)),",
    )
    replace_once(
        install,
        "    textStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.normal),\n"
        "    padding: EdgeInsets.symmetric(vertical: 15, horizontal: 12),\n",
        "    textStyle: TextStyle(fontFamily: 'Jost', fontSize: 13, fontWeight: FontWeight.w400),\n"
        "    padding: EdgeInsets.symmetric(vertical: 15, horizontal: 18),\n"
        "    shape: StadiumBorder(),\n",
    )
    replace_once(
        install,
        "        body: SingleChildScrollView(\n",
        "        body: DefaultTextStyle.merge(\n          style: TextStyle(fontSize: 13),\n"
        "          child: SingleChildScrollView(\n",
    )
    replace_once(
        install,
        "          ).paddingSymmetric(horizontal: 4 * em, vertical: 3 * em),\n        ));",
        "          ).paddingSymmetric(horizontal: 4 * em, vertical: 3 * em),\n        )));",
    )
    replace_once(
        install,
        "Text(translate('Installation'),\n                  style: Theme.of(context).textTheme.headlineMedium),",
        "Text(translate('Installation'),\n                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.w300, letterSpacing: -0.4)),",
    )
    replace_once(install, "? Color.fromARGB(135, 87, 87, 90)", "? Color(0xFF04263A)")
    replace_once(install, "border: Border.all(color: Colors.grey),", "border: Border.all(color: Color(0xFF2F5872)),")
    replace_once(
        install,
        "Icon(Icons.info_outline_rounded, size: 32)",
        f"Icon(Icons.info_outline_rounded, size: 24, color: {grey})",
    )

    # Settings: text 13 like the home page, titles light 20, the menu and the network icons in
    # the icon grey (white when selected), all the same size.
    settings = "flutter/lib/desktop/pages/desktop_setting_page.dart"
    replace_once(settings, "const double _kContentFontSize = 15;", "const double _kContentFontSize = 13;")
    replace_once(
        settings,
        "        color: _accentColor,\n        fontSize: _kTitleFontSize,\n        fontWeight: FontWeight.w400,\n",
        f"        {title},\n",
    )
    replace_once(
        settings,
        "                      style: const TextStyle(\n                        fontSize: _kTitleFontSize,\n                      ),",
        f"                      style: const TextStyle(\n                        {title},\n                      ),",
    )
    replace_once(
        settings,
        "              color: selected ? _accentColor : null,\n              size: 20,\n",
        # The monitor of Display is wider than the other glyphs: at 16 it looks as big as they do at 18.
        f"              color: selected ? Colors.white : {grey},\n"
        "              size: tab.unselected == Icons.desktop_windows_outlined ? 16 : 18,\n",
    )
    replace_once(
        settings,
        "                  color: selected ? _accentColor : null,\n                  fontWeight: FontWeight.w400,",
        "                  color: selected ? Colors.white : null,\n                  fontWeight: FontWeight.w400,",
    )
    replace_once(settings, "leading: Icon(icon, color: _accentColor),", f"leading: Icon(icon, color: {grey}, size: 20),")
    replace_once(settings, "icon: Icons.network_ping_outlined,", "icon: Icons.route_outlined,")
    replace_once(settings, "                    Icons.web_asset_outlined,\n", "                    Icons.language_outlined,\n")
    replace_once(
        settings,
        "                        Icons.help_outline,\n                        size: 14,\n"
        "                        color: Theme.of(context)\n                            .textTheme\n"
        "                            .titleLarge\n                            ?.color\n                            ?.withOpacity(0.7),",
        f"                        Icons.help_outline,\n                        size: 14,\n                        color: {grey},",
    )

    # Sign-in window: the Google, GitHub and Microsoft buttons in the panel colours instead of
    # their brand colours, the eye of the password in the icon grey.
    replace_once(
        "flutter/lib/common/widgets/login.dart",
        "              backgroundColor: primaryColor,\n            ).copyWith(",
        "              backgroundColor: Color(0xFF063049),\n"
        "              foregroundColor: Colors.white,\n"
        "              side: BorderSide(color: Color(0xFF2F5872)),\n"
        "            ).copyWith(",
    )
    # The GitHub mark is black and disappears on the dark button: white there, the others as they are.
    replace_once(
        "flutter/lib/common/widgets/login.dart",
        "                  child: _IconOP(\n"
        "                    op: branding.iconKey,\n"
        "                    icon: icon,\n"
        "                    margin: EdgeInsets.only(right: 5),\n"
        "                  ),\n",
        "                  child: ColorFiltered(\n"
        "                    colorFilter: ColorFilter.mode(\n"
        "                        branding.iconKey == 'github' ? Colors.white : Colors.transparent,\n"
        "                        BlendMode.srcATop),\n"
        "                    child: _IconOP(\n"
        "                      op: branding.iconKey,\n"
        "                      icon: icon,\n"
        "                      margin: EdgeInsets.only(right: 5),\n"
        "                    ),\n"
        "                  ),\n",
    )
    replace_once(
        "flutter/lib/common/widgets/dialog.dart",
        "            _passwordVisible ? Icons.visibility : Icons.visibility_off,\n"
        "            color: MyTheme.lightTheme.primaryColor),",
        "            _passwordVisible ? Icons.visibility : Icons.visibility_off,\n"
        f"            color: {grey}, size: 20),",
    )


# One type scale for the windows not designed one by one: 11 for small notes, 13 for text,
# 20 light for titles. The number inside the monitor icon (9), the unread badge (8) and the
# initial of the caller (55) are glyphs in a fixed box and keep their size.
SCALE = {"8": "11", "10": "11", "12": "13", "14": "13", "14.0": "13", "15": "13", "16": "13",
         "18": "20", "21": "20", "22": "20"}
SCALED = [
    "flutter/lib/common/widgets/address_book.dart",
    "flutter/lib/common/widgets/chat_page.dart",
    "flutter/lib/common/widgets/dialog.dart",
    "flutter/lib/common/widgets/login.dart",
    "flutter/lib/common/widgets/my_group.dart",
    "flutter/lib/common/widgets/peer_card.dart",
    "flutter/lib/common/widgets/peer_tab_page.dart",
    "flutter/lib/common/widgets/setting_widgets.dart",
    "flutter/lib/common/widgets/keyboard_shortcuts/recording_dialog.dart",
    "flutter/lib/desktop/pages/desktop_setting_page.dart",
    "flutter/lib/desktop/pages/file_manager_page.dart",
    "flutter/lib/desktop/pages/port_forward_page.dart",
    "flutter/lib/desktop/pages/server_page.dart",
    "flutter/lib/desktop/widgets/remote_toolbar.dart",
]


def scale_sizes(path, extra=None):
    table = dict(SCALE, **(extra or {}))
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r"fontSize: (\d+(?:\.0)?)(?=[,)\s])", lambda m: f"fontSize: {table.get(m.group(1), m.group(1))}", text
    )
    if new_text == text:
        sys.exit(f"no font size to scale in {path}")
    file.write_text(new_text, encoding="utf-8")
    print(f"scaled: {path}")


def type_scale():
    common = "flutter/lib/common.dart"
    # Text without its own size takes these: 13 for text, buttons and fields.
    replace_once(common, "titleSmall: TextStyle(fontSize: 14, color: Colors.black87),",
                 "titleSmall: TextStyle(fontSize: 13, color: Colors.black87),\n"
                 "        titleMedium: TextStyle(fontSize: 13, color: Colors.black87),")
    replace_once(common, "titleSmall: TextStyle(fontSize: 14),",
                 "titleSmall: TextStyle(fontSize: 13),\n      titleMedium: TextStyle(fontSize: 13),")
    replace_once(common, "bodyMedium:\n            TextStyle(fontSize: 14, color: Colors.black87, height: 1.25),",
                 "bodyMedium:\n            TextStyle(fontSize: 13, color: Colors.black87, height: 1.4),")
    replace_once(common, "bodyMedium: TextStyle(fontSize: 14, height: 1.25),",
                 "bodyMedium: TextStyle(fontSize: 13, height: 1.4),")
    replace_once(common, "labelLarge: TextStyle(fontSize: 16.0, color: MyTheme.accent80)),",
                 "labelLarge: TextStyle(fontSize: 13.0, color: MyTheme.accent80)),")
    replace_once(common, "labelLarge: TextStyle(\n        fontSize: 16.0,\n        fontWeight: FontWeight.bold,",
                 "labelLarge: TextStyle(\n        fontSize: 13.0,\n        fontWeight: FontWeight.w400,")
    title = "fontSize: 20, fontWeight: FontWeight.w300, letterSpacing: -0.4"
    replace_all(common, "style: TextStyle(fontSize: 21),", f"style: TextStyle({title}),", 2)
    replace_all(common, "style: const TextStyle(fontSize: 15)", "style: const TextStyle(fontSize: 13)", 4)
    replace_once(common, "fontWeight: FontWeight.w300,\n                    fontSize: 18,",
                 "fontWeight: FontWeight.w300,\n                    fontSize: 20,")

    # The menu of a drop-down (language, permissions...) was the grey of Flutter, square and
    # 16 wider on the left and 24 on the right than its field, so it ran past the card. Now it
    # has the panel colour, round corners and the width of the field, its text in line.
    replace_once(
        common,
        "child: Obx(() => DropdownButton<String>(\n            isExpanded: true,\n",
        "child: Obx(() => ButtonTheme(\n          alignedDropdown: true,\n          child: DropdownButton<String>(\n"
        "            isExpanded: true,\n"
        "            dropdownColor: Theme.of(context).brightness == Brightness.dark\n"
        "                ? Color(0xFF063049)\n"
        "                : null,\n"
        "            borderRadius: BorderRadius.circular(8),\n",
    )
    replace_once(
        common,
        "            }).toList(),\n          )),\n    ).marginOnly(bottom: 5);",
        "            }).toList(),\n          ))),\n    ).marginOnly(bottom: 5);",
    )
    replace_once(
        common,
        "                  overflow: TextOverflow.ellipsis,\n                ).marginOnly(left: 15),",
        "                  overflow: TextOverflow.ellipsis,\n                ),",
    )

    # Text in the soft white of the site (#F1F4F6) and cards as on the site: corners of 10 and
    # a thin light line (white at 18 %) around them.
    soft = "color: Color(0xFFF1F4F6)"
    replace_once(
        common,
        "      titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w300, letterSpacing: -0.4),\n"
        "      titleSmall: TextStyle(fontSize: 13),\n"
        "      titleMedium: TextStyle(fontSize: 13),\n"
        "      bodySmall: TextStyle(fontSize: 13, height: 1.4),\n"
        "      bodyMedium: TextStyle(fontSize: 13, height: 1.4),\n",
        f"      titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w300, letterSpacing: -0.4, {soft}),\n"
        f"      titleSmall: TextStyle(fontSize: 13, {soft}),\n"
        f"      titleMedium: TextStyle(fontSize: 13, {soft}),\n"
        f"      bodySmall: TextStyle(fontSize: 13, height: 1.4, {soft}),\n"
        f"      bodyMedium: TextStyle(fontSize: 13, height: 1.4, {soft}),\n",
    )
    replace_once(
        common,
        "    cardColor: Color(0xFF04263A),\n    visualDensity: VisualDensity.adaptivePlatformDensity,\n",
        "    cardColor: Color(0xFF04263A),\n"
        "    cardTheme: CardTheme(\n"
        "      elevation: 0,\n"
        "      shape: RoundedRectangleBorder(\n"
        "        borderRadius: BorderRadius.circular(10),\n"
        "        side: BorderSide(color: Color(0x2EFFFFFF)),\n"
        "      ),\n"
        "    ),\n"
        "    visualDensity: VisualDensity.adaptivePlatformDensity,\n",
    )

    # Titles in light 20 instead of bold.
    replace_once("flutter/lib/common/widgets/dialog.dart", "style: TextStyle(fontSize: 21),", f"style: TextStyle({title}),")
    server = "flutter/lib/desktop/pages/server_page.dart"
    replace_once(server, "fontWeight: FontWeight.bold,\n                    fontSize: 20,",
                 "fontWeight: FontWeight.w300,\n                    fontSize: 20,")
    replace_once(server, "style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),",
                 "style: TextStyle(fontSize: 20, fontWeight: FontWeight.w300),")
    replace_once("flutter/lib/common/widgets/overlay.dart",
                 "fontFamily: 'WorkSans',\n                    fontWeight: FontWeight.bold,\n                    fontSize: 20),",
                 "fontWeight: FontWeight.w300,\n                    fontSize: 20),")

    # Sizes kept in a variable: menus, the group search, the sign-in status and the status line.
    replace_once("flutter/lib/desktop/widgets/popup_menu.dart", "static const fontSize = 14.0;", "static const fontSize = 13.0;")
    replace_once("flutter/lib/common/widgets/my_group.dart", "final fontSize = 14.0;", "final fontSize = 13.0;")
    replace_once("flutter/lib/common/widgets/oidc_auth_status.dart", "const _statusFontSize = 12.0;",
                 "const _statusFontSize = 13.0;")
    replace_once("flutter/lib/desktop/pages/connection_page.dart", "double get em => 14.0;", "double get em => 13.0;")

    for path in SCALED:
        # The port forwarding table writes its rows at 20: they are text, not titles.
        scale_sizes(path, {"20": "13"} if path.endswith("port_forward_page.dart") else None)


def updates():
    # RustDesk turns its updater off for custom clients. the app turns it back on, with
    # res/vladpereverzyev/update.rs as the source: the releases of its own repository on GitHub.
    shutil.copyfile(HERE / "update.rs", ROOT / "src/vladpereverzyev_update.rs")
    print("copied: src/vladpereverzyev_update.rs")
    replace_once(
        "src/lib.rs",
        "mod updater;\n",
        'mod updater;\n#[cfg(target_os = "windows")]\nmod vladpereverzyev_update;\n',
    )
    replace_once(
        "src/common.rs",
        "pub fn check_software_update() {\n    if is_custom_client() {\n        return;\n    }\n",
        "pub fn check_software_update() {\n",
    )
    replace_once(
        "src/common.rs",
        "pub async fn do_check_software_update() -> hbb_common::ResultType<()> {\n",
        "pub async fn do_check_software_update() -> hbb_common::ResultType<()> {\n"
        '    #[cfg(target_os = "windows")]\n'
        "    if !is_rustdesk() {\n"
        "        return crate::vladpereverzyev_update::check().await;\n"
        "    }\n",
    )
    artifact = "src/updater/artifact.rs"
    replace_once(
        artifact,
        "    query: UpdateArtifactQuery<'_>,\n) -> ResultType<VerifiedUpdateArtifact> {\n",
        "    query: UpdateArtifactQuery<'_>,\n) -> ResultType<VerifiedUpdateArtifact> {\n"
        '    #[cfg(target_os = "windows")]\n'
        "    if !crate::is_rustdesk() {\n"
        "        let artifact = crate::vladpereverzyev_update::artifact(release_page_url)?;\n"
        "        *VERIFIED_UPDATE_ARTIFACT.lock().unwrap() = Some(artifact.clone());\n"
        "        return Ok(artifact);\n"
        "    }\n",
    )
    replace_once(
        artifact,
        '    if owner != "rustdesk"\n        || repo != "rustdesk"\n',
        '    if !(owner == "rustdesk" || owner == "vladpereverzyev")\n        || repo != "rustdesk"\n',
    )

    # An update is installed only when the user presses Update: no "Auto update" box in the
    # settings. The background check never installs, even with the option set some other way.
    replace_once(
        "flutter/lib/desktop/pages/desktop_setting_page.dart",
        "      if (showAutoUpdate)\n        _OptionCheckBox(\n          context,\n          'Auto update',\n"
        "          kOptionAllowAutoUpdate,\n          isServer: true,\n        ),\n",
        "",
    )
    replace_once(
        "src/updater.rs",
        "    if !(manually || config::Config::get_bool_option(keys::OPTION_ALLOW_AUTO_UPDATE)) {\n",
        "    if !manually {\n",
    )

    # The licence link of the install window opened the privacy policy of rustdesk.com, a
    # RustDesk document. It opens the licence of this app instead.
    replace_all(
        "flutter/lib/desktop/pages/install_page.dart",
        "'https://rustdesk.com/privacy.html'",
        "'https://github.com/vladpereverzyev/rustdesk/blob/vladpereverzyev/LICENCE'",
        2,
    )

    # The app only lets a lab or a clinic be reached; it never takes control of another computer.
    # RustDesk's incoming-only mode (the "host" client) drops the right pane with the ID field,
    # the recent sessions and the favourites, the Display settings and every option for outgoing
    # sessions. The Rust client refuses to open an outgoing connection.
    replace_once(
        "libs/hbb_common/src/config.rs",
        "pub fn is_incoming_only() -> bool {\n    HARD_SETTINGS\n        .read()\n        .unwrap()\n"
        "        .get(\"conn-type\")\n        .map_or(false, |x| x == (\"incoming\"))\n}",
        "pub fn is_incoming_only() -> bool {\n    true\n}",
    )
    # Every block of the small window keeps 20 on the left and 20 on the right, like the
    # signature, which spans the whole width between them.
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    replace_once(home, "const EdgeInsets.only(left: 20.0, right: 16, top: 16.0, bottom: 5)",
                 "const EdgeInsets.only(left: 20.0, right: 20, top: 16.0, bottom: 5)")
    replace_once(home, "margin: const EdgeInsets.only(left: 20, right: 11),",
                 "margin: const EdgeInsets.only(left: 20, right: 20),")
    replace_once(home, "margin: EdgeInsets.only(left: 20.0, right: 16, top: 13, bottom: 13),",
                 "margin: EdgeInsets.only(left: 20.0, right: 20, top: 13, bottom: 13),")
    # The install card sits lower, with more air above it. Its dark band runs on to the
    # bottom of the window, around the online status, with a thin line above the status.
    replace_once(home, "              0, marginTop, 0, bind.isIncomingOnly() ? marginTop : 0),",
                 "              0, bind.isIncomingOnly() ? 36 : marginTop, 0, 0),")
    band = ("BoxDecoration(gradient: LinearGradient(begin: Alignment.centerLeft, "
            "end: Alignment.centerRight, colors: [Color.fromARGB(255, 1, 30, 46), "
            "Color.fromARGB(255, 6, 48, 73)]))")
    replace_once(home, "        Divider(),\n        OnlineStatusWidget(",
                 "        SizedBox(height: 40),\n"
                 "        Divider(height: 1, thickness: 1),\n"
                 f"        Container(\n          decoration: {band},\n"
                 "          padding: EdgeInsets.only(left: 7, top: 11, bottom: 11, right: 20),\n"
                 "          child: OnlineStatusWidget(")
    replace_once(home, "        ).marginOnly(bottom: 6, right: 6)\n      ]);",
                 "        ),\n        ),\n      ]);")
    # 300 instead of 280, so the name in the title bar keeps some air before the buttons.
    replace_once(home, "width: isIncomingOnly ? 280.0 : 200.0,", "width: isIncomingOnly ? 300.0 : 200.0,")
    # RustDesk adds 11 to the width for the window border; Windows 10 takes 14, so the last 3
    # of the pane were cut off and the right margins looked smaller than the left ones.
    replace_once("flutter/lib/common.dart", "  final magicWidth = isWindows ? 11.0 : 2.0;",
                 "  final magicWidth = isWindows ? 14.0 : 2.0;")

    # The small window has no Home and Settings tabs: the menu button opens the settings in the
    # same window, at the same size, as a list of pages; each page has a back arrow to the list
    # and the list has one back to the home.
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        "    return state.value.tabs.length == 1 &&\n            controller.tabType == DesktopTabType.main ||\n"
        "        controller.tabType == DesktopTabType.install;",
        "    return (bind.isIncomingOnly() && controller.tabType == DesktopTabType.main) ||\n"
        "        state.value.tabs.length == 1 &&\n            controller.tabType == DesktopTabType.main ||\n"
        "        controller.tabType == DesktopTabType.install;",
    )
    replace_once(
        "flutter/lib/desktop/pages/desktop_tab_page.dart",
        "          windowManager.setSize(getIncomingOnlySettingsSize());\n          setResizable(true);",
        "          windowManager.setSize(getIncomingOnlyHomeSize());\n          setResizable(false);",
    )
    settings = "flutter/lib/desktop/pages/desktop_setting_page.dart"
    replace_once(
        settings,
        "import 'package:flutter_hbb/desktop/pages/desktop_tab_page.dart';\n",
        "import 'package:flutter_hbb/desktop/pages/desktop_tab_page.dart';\n"
        "import 'package:flutter_hbb/desktop/widgets/tabbar_widget.dart';\n",
    )
    replace_once(
        settings,
        "    super.build(context);\n    return Scaffold(\n"
        "      backgroundColor: Theme.of(context).colorScheme.background,\n      body: _buildBlock(\n",
        "    super.build(context);\n    if (bind.isIncomingOnly()) return _buildNarrow(context);\n"
        "    return Scaffold(\n"
        "      backgroundColor: Theme.of(context).colorScheme.background,\n      body: _buildBlock(\n",
    )
    replace_once(
        settings,
        "  Widget _header(BuildContext context) {\n",
        """  final RxBool _narrowOpen = false.obs;

  Widget _buildNarrow(BuildContext context) {
    final tabs = _settingTabs();
    const grey = Color(0xFF7D90A0);
    Widget header(String title, VoidCallback onBack) => SizedBox(
          height: 48,
          child: Row(children: [
            MouseRegion(
              cursor: SystemMouseCursors.click,
              child: GestureDetector(
                onTap: onBack,
                child: const Icon(Icons.chevron_left, size: 22, color: grey),
              ),
            ),
            const SizedBox(width: 16),
            Text(title,
                style:
                    const TextStyle(fontSize: 20, fontWeight: FontWeight.w300)),
          ]),
        ).marginOnly(left: 20, top: 10, bottom: 6);
    Widget item(int index, _TabInfo tab) => InkWell(
          onTap: () {
            controller.jumpToPage(index);
            selectedTab.value = tab.key;
            _narrowOpen.value = true;
          },
          child: SizedBox(
            height: 50,
            child: Row(children: [
              Icon(tab.unselected, size: 22, color: grey),
              const SizedBox(width: 16),
              Expanded(
                  child: Text(translate(tab.label),
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w300))),
              const Icon(Icons.chevron_right, size: 22, color: grey),
            ]).paddingSymmetric(horizontal: 20),
          ),
        );
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.background,
      body: _buildBlock(children: [
        Expanded(
          child: Obx(() {
            final open = _narrowOpen.value;
            final index =
                tabs.indexWhere((tab) => tab.key == selectedTab.value);
            return Column(children: [
              open
                  ? header(translate(tabs[index < 0 ? 0 : index].label),
                      () => _narrowOpen.value = false)
                  : header(translate('Settings'), () {
                      Get.find<DesktopTabController>()
                          .jumpToByKey(kTabLabelHomePage);
                    }),
              Expanded(
                child: Container(
                  color: Theme.of(context).scaffoldBackgroundColor,
                  child: Stack(children: [
                  Offstage(
                    offstage: !open,
                    child: PageView(
                      controller: controller,
                      physics: NeverScrollableScrollPhysics(),
                      children: _children(),
                    ),
                  ),
                  Offstage(
                    offstage: open,
                    child: ListView(
                      children: tabs
                          .asMap()
                          .entries
                          .map((e) => item(e.key, e.value))
                          .toList(),
                    ).marginOnly(top: 8),
                  ),
                ]),
                ),
              ),
            ]);
          }),
        ),
      ]),
    );
  }

  Widget _header(BuildContext context) {
""",
    )

    # In that mode RustDesk hides the settings button; the settings stay, for the permanent
    # password, the permissions and the language.
    replace_once(
        "flutter/lib/desktop/pages/desktop_tab_page.dart",
        "offstage: bind.isIncomingOnly() || bind.isDisableSettings(),",
        "offstage: bind.isDisableSettings(),",
    )

    # No sign-in at all: no Account page, no sign-in window, no account option or note in a
    # session. RustDesk's own "disable-account" switch hides every one of them.
    replace_once(
        "src/flutter_ffi.rs",
        "pub fn is_disable_account() -> SyncReturn<bool> {\n    SyncReturn(config::is_disable_account())\n}",
        "pub fn is_disable_account() -> SyncReturn<bool> {\n    SyncReturn(true)\n}",
    )

    # Address book and group need a RustDesk Pro server: on the public one they only show the
    # error "This feature is disabled on this public server". Both tabs are hidden.
    replace_once(
        "flutter/lib/models/peer_tab_model.dart",
        "    !(bind.isDisableAb() || bind.isDisableAccount()),\n"
        "    !(bind.isDisableGroupPanel() || bind.isDisableAccount()),\n",
        "    false,\n    false,\n",
    )

    # When the check at start finds a newer release, a window asks the user; nothing is
    # downloaded or installed unless they press Update (Download for the portable exe).
    common = "flutter/lib/common.dart"
    replace_once(
        common,
        "        if (evt['url'] is String) {\n          stateGlobal.updateUrl.value = evt['url'];\n        }\n",
        "        if (evt['url'] is String) {\n          stateGlobal.updateUrl.value = evt['url'];\n"
        "          if (isWindows && (evt['url'] as String).isNotEmpty) {\n"
        "            askForUpdate(evt['url'] as String);\n"
        "          }\n        }\n",
    )
    replace_once(
        common,
        "import 'package:flutter_hbb/desktop/widgets/tabbar_widget.dart';\n",
        "import 'package:flutter_hbb/desktop/widgets/tabbar_widget.dart';\n"
        "import 'package:flutter_hbb/desktop/widgets/update_progress.dart';\n",
    )
    file = ROOT / common
    file.write_text(
        file.read_text(encoding="utf-8")
        + "\nvoid askForUpdate(String releasePageUrl) {\n"
        "  final installed = bind.mainIsInstalled();\n"
        "  final version = releasePageUrl.split('/').last;\n"
        "  gFFI.dialogManager.show((setState, close, context) {\n"
        "    return CustomAlertDialog(\n"
        "      title: Text(translate('Update')),\n"
        "      content: Column(\n"
        "        mainAxisSize: MainAxisSize.min,\n"
        "        crossAxisAlignment: CrossAxisAlignment.start,\n"
        "        children: [\n"
        "          Text('${translate(\"A new version is available\")} $version.'),\n"
        "          const SizedBox(height: 22),\n"
        # Two pills of the same size side by side: as dialog actions the narrow window stacked them.
        "          Row(children: [\n"
        "            Expanded(\n"
        "              child: OutlinedButton(\n"
        "                style: OutlinedButton.styleFrom(\n"
        "                  shape: const StadiumBorder(),\n"
        "                  minimumSize: const Size(0, 34),\n"
        "                  padding: EdgeInsets.zero,\n"
        "                  foregroundColor: const Color(0xFFF1F4F6),\n"
        "                  side: const BorderSide(color: Color(0x59FFFFFF)),\n"
        "                  textStyle: const TextStyle(fontFamily: 'Jost', fontSize: 13, fontWeight: FontWeight.w400),\n"
        "                ),\n"
        "                onPressed: close,\n"
        "                child: Text(translate('Later'), maxLines: 1),\n"
        "              ),\n"
        "            ),\n"
        "            const SizedBox(width: 10),\n"
        "            Expanded(\n"
        "              child: ElevatedButton(\n"
        "                style: ElevatedButton.styleFrom(\n"
        "                  elevation: 0,\n"
        "                  shape: const StadiumBorder(),\n"
        "                  minimumSize: const Size(0, 34),\n"
        "                  padding: EdgeInsets.zero,\n"
        "                ),\n"
        "                onPressed: () {\n"
        "                  close();\n"
        "                  if (installed) {\n"
        "                    handleUpdate(releasePageUrl);\n"
        "                  } else {\n"
        "                    launchUrl(Uri.parse(releasePageUrl));\n"
        "                  }\n"
        "                },\n"
        "                child: Text(translate(installed ? 'Update' : 'Download'), maxLines: 1),\n"
        "              ),\n"
        "            ),\n"
        "          ]),\n"
        "        ],\n"
        "      ),\n"
        "      onCancel: close,\n"
        "    );\n"
        "  });\n"
        "}\n",
        encoding="utf-8",
    )
    print(f"patched: {common}")
    replace_once("src/lang/it.rs", '("Update", "Aggiorna"),', '("Update", "Aggiorna"),\n        ("Later", "Più tardi"),')

    replace_once(
        common,
        "  if (!isWeb) {\n    if (!bind.isCustomClient()) {\n      platformFFI.registerEventHandler(\n"
        "          kCheckSoftwareUpdateFinish,",
        "  if (!isWeb) {\n    {\n      platformFFI.registerEventHandler(\n"
        "          kCheckSoftwareUpdateFinish,",
    )
    replace_once(
        "flutter/lib/desktop/pages/desktop_setting_page.dart",
        "      if (!isWeb && !bind.isCustomClient())\n        _OptionCheckBox(\n          context,\n"
        "          'Check for software update on startup',",
        "      if (!isWeb)\n        _OptionCheckBox(\n          context,\n"
        "          'Check for software update on startup',",
    )
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    replace_once(
        home,
        "    if (!bind.isCustomClient() &&\n        updateUrl.isNotEmpty &&\n        !isCardClosed &&\n"
        "        bind.mainUriPrefixSync().contains('rustdesk')) {",
        "    if (updateUrl.isNotEmpty && !isCardClosed) {",
    )
    replace_once(
        home,
        "        final Uri url = Uri.parse('https://rustdesk.com/download');",
        "        final Uri url = Uri.parse(updateUrl);",
    )
    replace_once(
        home,
        "              ? 'https://github.com/rustdesk/rustdesk/releases/tag/${bind.mainGetNewVersion()}'",
        "              ? updateUrl",
    )


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
    # The disc touches the edges of the source, which looks cut off in the title bar and the
    # taskbar. A small transparent margin keeps the whole circle visible.
    margin = round(src.width * ICON_MARGIN)
    canvas = Image.new("RGBA", (src.width + 2 * margin, src.height + 2 * margin), (0, 0, 0, 0))
    canvas.alpha_composite(under, (margin, margin))
    return canvas.resize((size, size), Image.LANCZOS)


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


def narrow_settings():
    # In the small window a settings page is about 260 wide. Rows that RustDesk lays out in one
    # line for its 540 card wrap instead of running out of the card. The network rows keep
    # the same inset on both sides as the card title (15).
    settings = "flutter/lib/desktop/pages/desktop_setting_page.dart"
    replace_once(
        settings,
        "Widget _SubLabeledWidget(BuildContext context, String label, Widget child,\n"
        "    {bool enabled = true}) {\n  return Row(\n    children: [\n",
        "Widget _SubLabeledWidget(BuildContext context, String label, Widget child,\n"
        "    {bool enabled = true}) {\n  return Wrap(\n    crossAxisAlignment: WrapCrossAlignment.center,\n"
        "    children: [\n",
    )
    replace_once(
        settings,
        "  return Row(\n    children: [\n      ElevatedButton(\n        onPressed: enabled ? onPressed : null,\n"
        "        child: Text(\n          translate(label),\n        ).marginSymmetric(horizontal: 15),\n"
        "      ),\n    ],\n  ).marginOnly(left: _kContentHSubMargin);",
        "  return Row(\n    children: [\n      Flexible(\n        child: ElevatedButton(\n"
        "        onPressed: enabled ? onPressed : null,\n"
        "        child: Text(\n          translate(label),\n          textAlign: TextAlign.center,\n"
        "        ).marginSymmetric(horizontal: 15),\n"
        "      ),\n      ),\n    ],\n  ).marginOnly(left: _kContentHSubMargin);",
    )
    replace_once(
        settings,
        "                    child: Row(\n                      children: [\n                        Radio(\n"
        "                            value: value,\n                            groupValue: model.temporaryPasswordLength,",
        "                    child: Row(\n                      mainAxisSize: MainAxisSize.min,\n                      children: [\n"
        "                        Radio(\n"
        "                            value: value,\n                            groupValue: model.temporaryPasswordLength,",
    )
    replace_once(
        settings,
        "                  Row(\n                    children: [\n                      ...lengthRadios,",
        "                  Wrap(\n                    children: [\n                      ...lengthRadios,",
    )
    # A card keeps 4 of its own margin, so 16 around it puts its edge at 20 on both sides, like
    # the icons and the arrows of the list. The scroll bar runs in the right margin, beside the
    # cards.
    replace_once(settings, "          ).marginOnly(left: _kCardLeftMargin, top: 15),",
                 "          ).marginOnly(left: 16, right: 16, top: 15),")
    replace_once(settings, "        contentPadding: EdgeInsets.symmetric(horizontal: 16),\n        minLeadingWidth: 0,",
                 "        contentPadding: EdgeInsets.only(left: 15, right: 0),\n        minLeadingWidth: 0,")
    replace_once(settings, "const Divider(height: 1, indent: 16, endIndent: 16);",
                 "const Divider(height: 1, indent: 15, endIndent: 0);")
    # The Unlock Security/Network Settings button had only a left margin, so it ran wider than
    # the cards below it. Give it the same left and right margins and let the pill fill its card.
    replace_once(settings, "              ).marginOnly(left: _kCardLeftMargin),\n",
                 "              ).marginOnly(left: 16, right: 16),\n")
    replace_once(settings, "                ).marginSymmetric(horizontal: 2, vertical: 4),\n",
                 "                ).marginSymmetric(vertical: 4),\n")
    # _Button put its button in a Row at its intrinsic width, so a long label (Install the
    # printer) ran past the card. Let it fill the width between the margins and centre the text.
    replace_once(
        settings,
        "    child: Text(\n"
        "      translate(label),\n"
        "    ).marginSymmetric(horizontal: 15),\n"
        "    style: style,",
        "    child: Text(\n"
        "      translate(label),\n"
        "      textAlign: TextAlign.center,\n"
        "    ).marginSymmetric(horizontal: 15),\n"
        "    style: style,",
    )
    replace_once(
        settings,
        "  return Row(children: [\n"
        "    child,\n"
        "  ]).marginOnly(left: _kContentHMargin);",
        "  return Row(children: [\n"
        "    Expanded(child: child),\n"
        "  ]).marginOnly(left: _kContentHMargin, right: _kContentHMargin);",
    )
    # The printer the app installs is its own virtual printer; the button label drops the app
    # name and reads just "Installa stampante".
    replace_once("src/lang/it.rs",
                 '        ("Install {} Printer", "Installa la stampante {}"),',
                 '        ("Install {} Printer", "Installa stampante"),')
    # The printer messages drop the app name too, to match the button.
    replace_once("src/lang/it.rs",
                 '        ("printer-{}-not-installed-tip", "La stampante {} non è installata."),',
                 '        ("printer-{}-not-installed-tip", "La stampante non è installata."),')
    replace_once("src/lang/it.rs",
                 '        ("printer-{}-ready-tip", "La stampante {} è installata e pronta all\'uso."),',
                 '        ("printer-{}-ready-tip", "La stampante è installata e pronta all\'uso."),')
    replace_once("src/lang/it.rs",
                 '        ("printer-requires-installed-{}-client-tip", "Per usare la stampa remota, {} è necessario installare il programma nel dispositivo."),',
                 '        ("printer-requires-installed-{}-client-tip", "Per usare la stampa remota è necessario installare il programma nel dispositivo."),')
    # The update dialogs say "programma" instead of the app name.
    replace_once("src/lang/it.rs",
                 '        ("Downloading {}", "Download {}"),',
                 '        ("Downloading {}", "Download programma"),')
    replace_once("src/lang/it.rs",
                 '        ("{} Update", "Aggiorna {}"),',
                 '        ("{} Update", "Aggiorna programma"),')
    replace_once("src/lang/it.rs",
                 '        ("{}-to-update-tip", "{} si chiuderà e installerà la nuova versione"),',
                 '        ("{}-to-update-tip", "Il programma si chiuderà e installerà la nuova versione"),')


def title_buttons():
    # The Stop button of the Service card and the Change ID button sit at the right of their card
    # title, on the same line, with the inset of the card text. A card with no rows below its
    # title keeps the same space above and below the title.
    settings = "flutter/lib/desktop/pages/desktop_setting_page.dart"
    replace_once(
        settings,
        "      return _Card(title: 'Service', children: [\n        _Button(serviceStop.value ? 'Start' : 'Stop', () {",
        "      return _Card(title: 'Service', children: [], title_suffix: [\n"
        "        _TitleButton(serviceStop.value ? 'Start' : 'Stop', () {",
    )
    replace_once(settings, "_Card(title: 'ID', children: [changeId()]),",
                 "_Card(title: 'ID', children: [], title_suffix: [changeId()]),")
    replace_once(settings, "          return _Button('Change ID', changeIdDialog,",
                 "          return _TitleButton('Change ID', changeIdDialog,")
    replace_once(settings, "            ).marginOnly(bottom: 10),\n          ).marginOnly(left: 16, right: 16, top: 15),",
                 "            ).marginOnly(bottom: children.isEmpty ? 0 : 10),\n"
                 "          ).marginOnly(left: 16, right: 16, top: 15),")
    replace_once(
        settings,
        "// ignore: non_constant_identifier_names\nWidget _SubButton(",
        "// ignore: non_constant_identifier_names\n"
        "Widget _TitleButton(String label, Function() onPressed, {bool enabled = true}) {\n"
        "  return ElevatedButton(\n"
        "    onPressed: enabled ? onPressed : null,\n"
        "    child: Text(\n      translate(label),\n    ).marginSymmetric(horizontal: 15),\n"
        "  ).marginOnly(right: _kContentHMargin);\n}\n\n"
        "// ignore: non_constant_identifier_names\nWidget _SubButton(",
    )


def fixed_size_window():
    # The small window always keeps its size: Windows gets no maximize box (so neither Win+Up nor
    # snapping to the screen edge enlarges it), the title bar shows no maximize button and a
    # double click on the title bar does nothing, on the home and on the settings pages alike.
    replace_once(
        "flutter/lib/main.dart",
        "    setResizable(!bind.isIncomingOnly());\n",
        "    setResizable(!bind.isIncomingOnly());\n"
        "    if (bind.isIncomingOnly()) windowManager.setMaximizable(false);\n",
    )
    tabbar = "flutter/lib/desktop/widgets/tabbar_widget.dart"
    replace_once(tabbar, "    final isIncomingHomePage = bind.isIncomingOnly() && isInHomePage();",
                 "    final isIncomingHomePage = bind.isIncomingOnly();")
    replace_once(tabbar, "              if (widget.showMaximize && !isMacOS)",
                 "              if (widget.showMaximize && !isMacOS && !bind.isIncomingOnly())")


def shortcut_names():
    # The shortcuts on the Desktop and in the Start menu carry the display name, so the icon
    # reads "Vladyslav Pereverzyev". An install over an older one removes the shortcut with the
    # technical name; the uninstall removes both.
    win = "src/platform/windows.rs"
    old = APP_NAME
    replace_once(win, '        &format!("{app_name}.lnk"),', f'        &format!("{DISPLAY_NAME}.lnk"),')
    replace_once(win, '        &format!("Uninstall {app_name}.lnk"),',
                 f'        &format!("Uninstall {DISPLAY_NAME}.lnk"),')
    replace_once(
        win,
        '            "copy /Y \\"{}\\\\{}.lnk\\" \\"%PUBLIC%\\\\Desktop\\\\\\"",\n'
        '            tmp_path,\n            crate::get_app_name()\n        );',
        f'            "if exist \\"%PUBLIC%\\\\Desktop\\\\{old}.lnk\\" del /f /q \\"%PUBLIC%\\\\Desktop\\\\{old}.lnk\\"\\n'
        'copy /Y \\"{}\\\\{}.lnk\\" \\"%PUBLIC%\\\\Desktop\\\\\\"",\n'
        f'            tmp_path,\n            "{DISPLAY_NAME}"\n        );',
    )
    for line in [
        'copy /Y \\"{tmp_path}\\\\{app_name}.lnk\\" \\"{start_menu}\\\\\\"',
        'copy /Y \\"{tmp_path}\\\\Uninstall {app_name}.lnk\\" \\"{start_menu}\\\\\\"',
        'if exist \\"{tmp_path}\\\\{app_name}.lnk\\" del /f /q \\"{tmp_path}\\\\{app_name}.lnk\\"',
        'if exist \\"{tmp_path}\\\\Uninstall {app_name}.lnk\\" del /f /q \\"{tmp_path}\\\\Uninstall {app_name}.lnk\\"',
        'copy /Y \\"{tmp_path}\\\\Uninstall {app_name}.lnk\\" \\"{path}\\\\\\"',
    ]:
        replace_once(win, line, line.replace("{app_name}.lnk", f"{DISPLAY_NAME}.lnk"))
    desktop = ('    if exist \\"%PUBLIC%\\\\Desktop\\\\{app_name}.lnk\\" '
               'del /f /q \\"%PUBLIC%\\\\Desktop\\\\{app_name}.lnk\\"\n')
    replace_once(win, desktop, desktop + desktop.replace("{app_name}", DISPLAY_NAME))
    # The author in the Windows "Installed apps" list is the display name, not the technical
    # app name used for the exe, the service and the install folder.
    replace_once(
        win,
        'reg add {subkey} /f /v Publisher /t REG_SZ /d \\"{app_name}\\"',
        f'reg add {{subkey}} /f /v Publisher /t REG_SZ /d \\"{DISPLAY_NAME}\\"',
    )
    replace_once(
        win,
        'reg add {subkey} /f /v DisplayName /t REG_SZ /d \\"{app_name}\\"',
        f'reg add {{subkey}} /f /v DisplayName /t REG_SZ /d \\"{DISPLAY_NAME}\\"',
    )


def copy_on_click():
    # One click on the ID or the password copies it. The text field would take the click for
    # itself, so it ignores the pointer and the area around it takes the click.
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    replace_once(
        home,
        "                    child: GestureDetector(\n                      onDoubleTap: () {\n"
        "                        Clipboard.setData(\n                            ClipboardData(text: model.serverId.text));\n"
        "                        showToast(translate(\"Copied\"));\n                      },\n"
        "                      child: TextFormField(\n",
        "                    child: GestureDetector(\n                      behavior: HitTestBehavior.opaque,\n"
        "                      onTap: () {\n"
        "                        Clipboard.setData(\n                            ClipboardData(text: model.serverId.text));\n"
        "                        showToast(translate(\"Copied\"));\n                      },\n"
        "                      child: MouseRegion(cursor: SystemMouseCursors.click, child: IgnorePointer(child: TextFormField(\n",
    )
    replace_once(
        home,
        "                      ).workaroundFreezeLinuxMint(),\n                    ),\n                  )\n",
        "                      ).workaroundFreezeLinuxMint())),\n                    ),\n                  )\n",
    )
    replace_once(
        home,
        "                        child: GestureDetector(\n                          onDoubleTap: () {\n"
        "                            if (showOneTime) {\n",
        "                        child: GestureDetector(\n                          behavior: HitTestBehavior.opaque,\n"
        "                          onTap: () {\n                            if (showOneTime) {\n",
    )
    replace_once(
        home,
        "                          child: TextFormField(\n                            controller: model.serverPasswd,\n",
        "                          child: MouseRegion(cursor: SystemMouseCursors.click, child: IgnorePointer(child: TextFormField(\n"
        "                            controller: model.serverPasswd,\n",
    )
    replace_once(
        home,
        "                          ).workaroundFreezeLinuxMint(),\n                        ),\n                      ),\n"
        "                      if (showOneTime)\n",
        "                          ).workaroundFreezeLinuxMint())),\n                        ),\n                      ),\n"
        "                      if (showOneTime)\n",
    )


ABOUT_TEXTS = [
    ("What it is for", "A cosa serve"),
    ("With this app a lab or a clinic lets Vladyslav Pereverzyev reach its computer when a case "
     "needs help. The app cannot take control of other computers.",
     "Con questa app un laboratorio o una clinica lascia entrare Vladyslav Pereverzyev nel proprio "
     "computer quando un caso ha bisogno di aiuto. L'app non può controllare altri computer."),
    ("How to use it", "Come si usa"),
    ("Give the ID and the password of this window to the person who helps you. A click on the ID "
     "or the password copies it. To be reached when nobody sits at the computer, install the app "
     "and set a permanent password with the pencil next to the password.",
     "Dai l'ID e la password di questa finestra a chi ti aiuta. Un clic sull'ID o sulla password "
     "li copia. Per essere raggiunto quando nessuno è al computer, installa l'app e imposta una "
     "password permanente con la matita accanto alla password."),
    ("The screen, the keyboard, the clipboard and the files of a session are encrypted end to end. "
     "Let in only people you know: whoever has the ID and the password can use this computer. "
     "You can end a session at any moment from the window that shows it.",
     "Lo schermo, la tastiera, gli appunti e i file di una sessione sono cifrati da un capo "
     "all'altro. Fai entrare solo persone che conosci: chi ha l'ID e la password può usare questo "
     "computer. Puoi chiudere una sessione in qualsiasi momento dalla finestra che la mostra."),
    ("Updates", "Aggiornamenti"),
    ("When it starts, the app looks for a new version on GitHub and always asks before it installs "
     "one.",
     "All'avvio l'app cerca una nuova versione su GitHub e chiede sempre prima di installarla."),
    ("Network and privacy", "Rete e privacy"),
    ("vp-network-tip",
     "To find each other, the computers use the public servers of RustDesk, which see the ID and "
     "the IP address of each computer. The app collects nothing for Vladyslav Pereverzyev: no "
     "account and no tracking.",
     "Per trovarsi, i computer usano i server pubblici di RustDesk, che vedono l'ID e l'indirizzo "
     "IP di ogni computer. L'app non raccoglie niente per Vladyslav Pereverzyev: nessun account e "
     "nessun tracciamento."),
    ("Links", "Link"),
    ("Source code", "Codice sorgente"),
    ("Licence", "Licenza"),
    ("Test build", "Versione di prova"),
    ("vp-licence-tip",
     "This remote desktop is based on RustDesk (github.com/rustdesk/rustdesk) and changed by "
     "Vladyslav Pereverzyev from November 2026 on. It is released under the GNU Affero General "
     "Public License version 3. RustDesk is a trademark of its owners; this app is not affiliated "
     "with or endorsed by the RustDesk project.",
     "Questo desktop remoto è basato su RustDesk (github.com/rustdesk/rustdesk) e modificato da "
     "Vladyslav Pereverzyev da novembre 2026. È distribuito con la licenza GNU Affero General "
     "Public License versione 3. RustDesk è un marchio dei suoi titolari; questa app non è "
     "affiliata al progetto RustDesk né approvata da esso."),
    ("The app is free software and comes as it is, without any warranty. As far as the law "
     "allows, Vladyslav Pereverzyev is not liable for any damage that comes from its use. The "
     "details are in the README and in the licence.",
     "L'app è software libero e viene fornita così com'è, senza alcuna garanzia. Nei limiti "
     "consentiti dalla legge, Vladyslav Pereverzyev non risponde dei danni che derivano dal suo uso. "
     "I dettagli sono nel README e nella licenza."),
    # Not on the About page: the text of the update window, without the name of the app.
    ("A new version is available", "È disponibile una nuova versione"),
]


def no_update_card():
    # The update window opens at every start, so the home window shows no update card as well.
    replace_once("flutter/lib/desktop/pages/desktop_home_page.dart",
                 "if (updateUrl.isNotEmpty && !isCardClosed) {",
                 "if (updateUrl.isNotEmpty && !isCardClosed && !bind.isIncomingOnly()) {")


def about_page():
    # The About page tells the user what the app is, how to use it and what it sends where, with
    # the version of this app next to the RustDesk one, the links of this project and, as the
    # AGPL asks, the RustDesk copyright and the source code. No RustDesk slogan, no blue box.
    ref = os.environ.get("GITHUB_REF", "")
    version = f"'{ref[len('refs/tags/v'):]}'" if ref.startswith("refs/tags/v") else "translate('Test build')"
    texts = {t[0]: f'translate("{t[0]}")' for t in ABOUT_TEXTS}
    repo = "https://github.com/vladpereverzyev/rustdesk"
    dart = """class _AboutState extends State<_About> {
  @override
  Widget build(BuildContext context) {
    return futureBuilder(future: () async {
      final license = await bind.mainGetLicense();
      final version = await bind.mainGetVersion();
      final buildDate = await bind.mainGetBuildDate();
      final fingerprint = await bind.mainGetFingerprint();
      final myId = await bind.mainGetMyId();
      return {
        'license': license,
        'version': version,
        'buildDate': buildDate,
        'fingerprint': fingerprint,
        'myId': myId
      };
    }(), hasData: (data) {
      final license = data['license'].toString();
      final version = data['version'].toString();
      final buildDate = data['buildDate'].toString();
      final fingerprint = data['fingerprint'].toString();
      final myId = data['myId'].toString();
      const linkStyle = TextStyle(decoration: TextDecoration.underline);
      Widget line(String text) => SelectionArea(
          child: Text(text).marginSymmetric(vertical: 4.0));
      Widget link(String text, String url) => InkWell(
          onTap: () => launchUrlString(url),
          child: Text(text, style: linkStyle).marginSymmetric(vertical: 4.0));
      Widget section(String title, List<Widget> children) =>
          _Card(title: title, children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: children,
              ),
            ).marginOnly(left: _kContentHMargin, bottom: 10)
          ]);
      final scrollController = ScrollController();
      return SingleChildScrollView(
        controller: scrollController,
        child: Column(children: [
          section(translate('About RustDesk'), [
            line('${translate('Version')}: @VERSION@ (RustDesk $version)'),
            line('${translate('Build Date')}: $buildDate'),
            line('${translate('ID')}: $myId'),
            if (!isWeb) line('${translate('Fingerprint')}: $fingerprint'),
          ]),
          section(@T0@, [line(@T1@)]),
          section(@T2@, [line(@T3@)]),
          section(translate('Security'), [line(@T4@)]),
          section(@T5@, [line(@T6@)]),
          section(@T7@, [line(@T8@)]),
          section(@T9@, [
            link(translate('Website'), 'https://vladpereverzyev.com'),
            link(@T10@, '@REPO@'),
            link(translate('Privacy Statement'), '@REPO@/blob/vladpereverzyev/README.md#privacy'),
            link(@T11@, '@REPO@/blob/vladpereverzyev/LICENCE'),
          ]),
          section(@T11@, [
            line('Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.'),
            if (license.isNotEmpty) line(license),
            line(@T13@),
            line(@T14@),
          ]),
        ]),
      );
    });
  }
}

//#endregion
"""
    keys = [t[0] for t in ABOUT_TEXTS]
    for i, en in enumerate(keys):
        dart = dart.replace(f"@T{i}@", texts[en])
    dart = dart.replace("@VERSION@", "${" + version + "}").replace("@REPO@", repo)
    sub_once(
        "flutter/lib/desktop/pages/desktop_setting_page.dart",
        r"class _AboutState extends State<_About> \{.*?//#endregion\n",
        lambda _: dart,
    )

    def rust(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')
    entries = "".join(f'        ("{rust(t[0])}", "{rust(t[-1])}"),\n' for t in ABOUT_TEXTS)
    replace_once("src/lang/it.rs", '        ("Later", "Più tardi"),\n',
                 '        ("Later", "Più tardi"),\n' + entries)
    tips = "".join(f'        ("{rust(t[0])}", "{rust(t[1])}"),\n' for t in ABOUT_TEXTS if len(t) == 3)
    replace_once("src/lang/en.rs", '        ("Ready", "Online, ready to connect"),',
                 '        ("Ready", "Online, ready to connect"),\n' + tips.rstrip("\n"))
    # translate() swaps every "RustDesk" for the name of the app. The "vp-" texts speak about
    # RustDesk itself, its servers and its project, so they keep the name.
    replace_once("src/lang.rs", '                && name != "powered_by_me"\n',
                 '                && name != "powered_by_me"\n                && !name.starts_with("vp-")\n')

    # about-translations.json holds, for every other language of the app, the texts of "Later"
    # and of ABOUT_TEXTS in the same order.
    keys = ["Later"] + [t[0] for t in ABOUT_TEXTS]
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "about-translations.json"), encoding="utf-8") as f:
        translations = json.load(f)
    for lang, values in translations.items():
        assert len(values) == len(keys), lang
        lines = "".join(f'        ("{rust(k)}", "{rust(v)}"),\n' for k, v in zip(keys, values))
        replace_once(f"src/lang/{lang}.rs", "    ].iter().cloned().collect();",
                     lines + "    ].iter().cloned().collect();")


CM_BUTTON = """    Widget textWidget;
    // The pills of the home window: the main action filled azure with dark text, every other
    // button outlined, like Install.
    final primary = color == MyTheme.accent;
    final fg = primary ? const Color(0xFF@BUTTON_TEXT@) : const Color(0xFFF1F4F6);
    final label = Text(
      translate(text),
      style: TextStyle(
          color: fg, fontFamily: 'Jost', fontSize: 13, fontWeight: FontWeight.w400),
      textAlign: TextAlign.center,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
    textWidget = icon != null ? Flexible(child: label) : Expanded(child: label);
    final borderRadius = BorderRadius.circular(18.0);
    final btn = Container(
      height: 36,
      decoration: BoxDecoration(
          color: primary ? MyTheme.accent : Colors.transparent,
          borderRadius: borderRadius,
          border: Border.all(
              color: primary ? MyTheme.accent : const Color(0x59FFFFFF))),
      child: InkWell(
        borderRadius: borderRadius,
        hoverColor: primary ? const Color(0x33FFFFFF) : const Color(0x1A2791CB),
        onTap: () {
          if (onClick == null) return;
          checkClickTime(client.id, onClick);
        },
        onTapDown: (details) {
          if (onTapDown == null) return;
          checkClickTime(client.id, () {
            onTapDown.call(details);
          });
        },
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (icon != null)
              ColorFiltered(
                colorFilter: ColorFilter.mode(
                    primary ? fg : const Color(0xFF@ICON@), BlendMode.srcIn),
                child: icon,
              ).marginOnly(right: 6),
            textWidget,
          ],
        ),
      ),
    );
    return (tooltip != null
            ? Tooltip(
                message: translate(tooltip),
                child: btn,
              )
            : btn)
        .marginSymmetric(horizontal: 4, vertical: 5);
  }"""

CM_CARD = """Widget buildConnectionCard(Client client) {
  // Laid out like the home window: logo, title and the boards with the azure line on the panel,
  // then the buttons and the status line on the gradient of the install banner.
  return Consumer<ServerModel>(
    builder: (context, value, child) => Container(
      key: ValueKey(client.id),
      color: Theme.of(context).colorScheme.background,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _CmHeader(client: client),
                  client.type_() == ClientType.file ||
                          client.type_() == ClientType.portForward ||
                          client.type_() == ClientType.terminal ||
                          client.disconnected
                      ? Offstage()
                      : _PrivilegeBoard(client: client),
                ],
              ),
            ),
          ),
          Container(
            decoration: const BoxDecoration(gradient: _kCmGradient),
            padding: const EdgeInsets.fromLTRB(16, 9, 16, 1),
            child: _CmControlPanel(client: client),
          ),
          _CmStatusLine(client: client),
        ],
      ),
    ),
  );
}

const _kCmGradient = LinearGradient(
  begin: Alignment.centerLeft,
  end: Alignment.centerRight,
  colors: [Color(0xFF011E2E), Color(0xFF063049)],
);

// The board of the home window: a 2 px azure line on the left, the label in small capitals.
Widget _cmBoard({required String label, Widget? action, required Widget child, required double height}) {
  return Container(
    margin: const EdgeInsets.only(left: 20, right: 20, top: 5),
    padding: const EdgeInsets.only(left: 7),
    height: height,
    decoration: const BoxDecoration(
      border: Border(left: BorderSide(color: MyTheme.accent, width: 2)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 20,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label.toUpperCase(),
                style: const TextStyle(fontSize: 11, letterSpacing: 2.2, color: Color(0xFF@AZURE_LIGHT@)),
              ),
              if (action != null) action,
            ],
          ),
        ),
        Expanded(child: child),
      ],
    ),
  );
}

class _CmStatusLine extends StatefulWidget {
  final Client client;

  const _CmStatusLine({Key? key, required this.client}) : super(key: key);

  @override
  State<_CmStatusLine> createState() => _CmStatusLineState();
}

class _CmStatusLineState extends State<_CmStatusLine> {
  int _seconds = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (widget.client.authorized && !widget.client.disconnected) {
        setState(() => _seconds++);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final client = widget.client;
    final live = client.authorized && !client.disconnected;
    final text = client.authorized
        ? (client.disconnected ? translate("Disconnected") : translate("Connected"))
        : "${translate("Request access to your device")}...";
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Divider(height: 1, thickness: 1),
        Container(
          decoration: const BoxDecoration(gradient: _kCmGradient),
          padding: const EdgeInsets.only(left: 7, top: 11, bottom: 11, right: 20),
          child: SizedBox(
            height: 24,
            child: Row(
              children: [
                Container(
                  height: 8,
                  width: 8,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    color: live
                        ? const Color.fromARGB(255, 50, 190, 166)
                        : (client.disconnected ? kColorWarn : MyTheme.accent),
                  ),
                ).marginSymmetric(horizontal: 13),
                Flexible(
                  child: Text(text,
                      style: const TextStyle(fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                ),
                if (live)
                  Text(
                    formatDurationToTime(Duration(seconds: _seconds)),
                    style: const TextStyle(fontSize: 13, color: Color(0xFF@AZURE_LIGHT@)),
                  ).marginOnly(left: 8),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _AppIcon"""

CM_HEADER_BUILD = """  Widget build(BuildContext context) {
    super.build(context);
    final showChat = client.authorized &&
        (client.type_() == ClientType.remote ||
            client.type_() == ClientType.file ||
            client.type_() == ClientType.camera);
    String? kind;
    if (client.type_() == ClientType.terminal) kind = translate("Terminal");
    if (client.type_() == ClientType.file) kind = translate("Transfer file");
    if (client.type_() == ClientType.camera) kind = translate("View camera");
    if (client.portForward.isNotEmpty) kind = "Port Forward: ${client.portForward}";
    final hover = false.obs;
    final chat = Tooltip(
      message: translate(client.type_() == ClientType.file ? 'Transfer file' : 'Chat'),
      child: InkWell(
      onTap: () => checkClickTime(client.id, () {
        if (client.type_() == ClientType.file) {
          gFFI.chatModel.toggleCMFilePage();
        } else {
          gFFI.chatModel.toggleCMChatPage(MessageKey(client.peerId, client.id));
        }
      }),
      onHover: (value) => hover.value = value,
      child: Obx(() => Icon(
            client.type_() == ClientType.file
                ? Icons.drive_file_move_rounded
                : Icons.chat_rounded,
            size: 20,
            color: hover.value
                ? Theme.of(context).textTheme.titleLarge?.color
                : const Color(0xFF@ICON@),
          )),
    ));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Align(alignment: Alignment.center, child: loadLogo()),
        Padding(
          padding: const EdgeInsets.only(left: 20.0, right: 20, top: 16.0, bottom: 5),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(translate("Connection"), style: Theme.of(context).textTheme.titleLarge),
              if (kind != null)
                Text(kind, style: Theme.of(context).textTheme.bodySmall).marginOnly(top: 10),
            ],
          ),
        ),
        _cmBoard(
          label: translate("ID"),
          action: showChat ? chat : null,
          height: 57,
          child: Text(
            formatID(client.peerId),
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w300),
          ).marginOnly(top: 6),
        ),
      ],
    );
  }

  @override
  bool get wantKeepAlive => true;"""

PRIVILEGE_HEAD_OLD = """    return Container(
      width: double.infinity,
      height: 160.0,
      margin: EdgeInsets.all(5.0),
      padding: EdgeInsets.all(5.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10.0),
        color: Theme.of(context).colorScheme.background,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            spreadRadius: 1,
            blurRadius: 1,
            offset: Offset(0, 1.5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            translate("Permissions"),
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w300),
            textAlign: TextAlign.center,
          ).marginOnly(left: 4.0, bottom: 8.0),
          Expanded(
            child: GridView.count(
              crossAxisCount: crossAxisCount,
              padding: EdgeInsets.symmetric(horizontal: spacing),
              mainAxisSpacing: spacing,
              crossAxisSpacing: spacing,
"""

PRIVILEGE_HEAD_NEW = """    return _cmBoard(
      label: translate("Permissions"),
      height: 102,
      child: Column(
        children: [
          Expanded(
            child: GridView.count(
              crossAxisCount: crossAxisCount,
              padding: const EdgeInsets.only(top: 6),
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 4,
              crossAxisSpacing: spacing,
              childAspectRatio: 1.6,
"""


def connection_window():
    # The window that asks to let a session in and then shows it, built like the home window: the
    # same size, the app icon and name in the title bar with no tab, the logo, a title, the boards
    # with the azure line, grey icons, the pills and the status line on the gradient. The account
    # name of the other side (often an e-mail address) is never shown.
    replace_once("flutter/lib/consts.dart", "const Size kConnectionManagerWindowSizeClosedChat = Size(300, 490);",
                 "const Size kConnectionManagerWindowSizeClosedChat = Size(314, 631);")
    replace_once("flutter/lib/consts.dart", "const Size kConnectionManagerWindowSizeOpenChat = Size(700, 490);",
                 "const Size kConnectionManagerWindowSizeOpenChat = Size(714, 631);")
    replace_once("flutter/lib/models/server_model.dart", "        label: client.name,\n",
                 f"        label: '{DISPLAY_NAME}',\n")

    server = "flutter/lib/desktop/pages/server_page.dart"
    replace_once(server, "import 'package:flutter_hbb/consts.dart';\n",
                 "import 'package:flutter_hbb/consts.dart';\nimport 'package:flutter_hbb/common/formatter/id_formatter.dart';\n")
    replace_once(server, "              showTitle: false,\n              showMaximize: false,",
                 "              showTitle: true,\n              showMaximize: false,")
    replace_once(server, "              selectedBorderColor: MyTheme.accent,\n              maxLabelWidth: 100,",
                 "              selectedBorderColor: Colors.transparent,\n"
                 "              selectedTabBackgroundColor: Colors.transparent,\n"
                 "              unSelectedTabBackgroundColor: Colors.transparent,\n"
                 "              maxLabelWidth: 100,")
    # The title bar shows only the app icon and name, as on the home window: the tabs draw nothing.
    replace_once(server, "              tabBuilder: (key, icon, label, themeConf) {\n",
                 "              tabBuilder: (key, icon, label, themeConf) {\n"
                 "                if (key.isNotEmpty) return const SizedBox.shrink();\n")
    sub_once(server, r"Widget buildConnectionCard\(Client client\) \{.*?\n\}\n\nclass _AppIcon",
             lambda _: CM_CARD.replace("@AZURE_LIGHT@", AZURE_LIGHT))
    sub_once(server, r"  Widget build\(BuildContext context\) \{\n    super\.build\(context\);\n    return Container\(\n"
             r".*?  @override\n  bool get wantKeepAlive => true;",
             lambda _: CM_HEADER_BUILD.replace("@ICON@", ICON))
    replace_once(server, PRIVILEGE_HEAD_OLD, PRIVILEGE_HEAD_NEW)
    replace_once(server, "    final spacing = 10.0;\n", "    final spacing = 14.0;\n")
    replace_once(
        server,
        "        decoration: BoxDecoration(\n          color: enabled\n"
        "              ? (canModify ? MyTheme.accent : MyTheme.accent.withOpacity(0.6))\n"
        "              : Colors.grey[700],\n          borderRadius: BorderRadius.circular(10.0),\n        ),\n"
        "        padding: EdgeInsets.all(8.0),\n",
        "",
    )
    replace_once(server, "                child: Icon(\n                  iconData,\n                  color: Colors.white,\n                ),",
                 "                child: Icon(\n                  iconData,\n"
                 "                  color: enabled ? const Color(0xFFD0D0D0) : const Color(0x667D90A0),\n"
                 "                  size: 20,\n                ),")
    sub_once(server, r"    Widget textWidget;\n    if \(icon != null\) \{.*?        \.marginAll\(4\);\n  \}",
             lambda _: CM_BUTTON.replace("@BUTTON_TEXT@", BUTTON_TEXT).replace("@ICON@", ICON))
    # A single action is a pill of the width of Install, centred, as on the home window.
    replace_once(server, "        Row(\n          children: [\n            Expanded(\n              child: buildButton(context,\n"
                         "                  color: Colors.redAccent,",
                 "        Row(\n          mainAxisAlignment: MainAxisAlignment.center,\n          children: [\n"
                 "            SizedBox(\n              width: 158,\n              child: buildButton(context,\n"
                 "                  color: Colors.redAccent,")
    replace_once(server, "        Expanded(\n            child: buildButton(context,\n                color: MyTheme.accent,\n"
                         "                onClick: handleClose,",
                 "        SizedBox(\n            width: 158,\n            child: buildButton(context,\n"
                 "                color: MyTheme.accent,\n                onClick: handleClose,")

    chat = "flutter/lib/common/widgets/chat_page.dart"
    replace_once(chat, "isOwnMessage ? MyTheme.accent : Colors.blueGrey,",
                 "isOwnMessage ? Color(0xFF063049) : Color(0xFF04263A),")
    replace_once(chat, "                        color: MyTheme.accent,\n                        icon: Icons.send_rounded,",
                 f"                        color: Color(0xFF{ICON}),\n                        icon: Icons.send_rounded,")
    replace_once(
        chat,
        "                        border: OutlineInputBorder(\n                          borderRadius: BorderRadius.circular(10.0),\n"
        "                          borderSide: const BorderSide(\n                            width: 1,\n"
        "                            style: BorderStyle.solid,\n                          ),\n                        ),\n",
        "                        border: OutlineInputBorder(\n                          borderRadius: BorderRadius.circular(8.0),\n"
        "                          borderSide: const BorderSide(color: Color(0x4DFFFFFF)),\n                        ),\n"
        "                        enabledBorder: OutlineInputBorder(\n                          borderRadius: BorderRadius.circular(8.0),\n"
        "                          borderSide: const BorderSide(color: Color(0x4DFFFFFF)),\n                        ),\n"
        "                        focusedBorder: OutlineInputBorder(\n                          borderRadius: BorderRadius.circular(8.0),\n"
        f"                          borderSide: const BorderSide(color: Color(0xFF{AZURE})),\n                        ),\n",
    )

def remove_quit_button():
    # The incoming-only home shows a Quit button at the bottom right. The window closes from
    # the title bar, so the button is redundant. This removal fails the build if the block is
    # no longer found, so a mismatch never silently leaves the button in.
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    block = (
        "    if (bind.isIncomingOnly()) {\n"
        "      final quitButtonText =\n"
        "          bind.mainGetBuildinOption(key: kOptionQuitButtonText).trim();\n"
        "      return Align(\n"
        "        alignment: Alignment.centerRight,\n"
        "        child: OutlinedButton(\n"
        "          onPressed: () {\n"
        "            SystemNavigator.pop(); // Close the application\n"
        "            // https://github.com/flutter/flutter/issues/66631\n"
        "            if (isWindows) {\n"
        "              exit(0);\n"
        "            }\n"
        "          },\n"
        "          child: Text(quitButtonText.isEmpty ? translate('Quit') : quitButtonText),\n"
        "        ),\n"
        "      ).marginAll(14);\n"
        "    }\n"
    )
    file = ROOT / home
    text = file.read_text(encoding="utf-8")
    if text.count(block) != 1:
        sys.exit(f"quit button block not found in {home}")
    file.write_text(text.replace(block, "", 1), encoding="utf-8")
    print(f"patched: {home}")


def reachable_only_while_open():
    # Reachable only while the window is open. The app never installs a background service, so
    # nothing runs at boot or in the background: it serves from the open window (the server runs
    # in the main process) and the title-bar close quits the process, which ends that server with
    # it. Run the exe as administrator to let a session handle UAC on this computer.
    replace_once(
        "libs/hbb_common/src/config.rs",
        "pub fn is_disable_installation() -> bool {\n"
        "    is_some_hard_opton(\"disable-installation\")\n"
        "}",
        "pub fn is_disable_installation() -> bool {\n"
        "    true\n"
        "}",
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        "import 'dart:async';\n",
        "import 'dart:async';\nimport 'dart:io';\n",
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        "    mainWindowClose() async => await windowManager.hide();",
        "    mainWindowClose() async {\n"
        "      if (bind.isIncomingOnly()) {\n"
        "        exit(0);\n"
        "      } else {\n"
        "        await windowManager.hide();\n"
        "      }\n"
        "    }",
    )


def main():
    replace_once(
        "libs/hbb_common/src/config.rs",
        'APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
        f'APP_NAME: RwLock<String> = RwLock::new("{APP_NAME}".to_owned());',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"',
        f'VALUE "FileDescription", "{DISPLAY_NAME} Remote Desktop" "\\0"',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "ProductName", "RustDesk" "\\0"',
        f'VALUE "ProductName", "{DISPLAY_NAME}" "\\0"',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "InternalName", "rustdesk" "\\0"',
        f'VALUE "InternalName", "{EXE_NAME}" "\\0"',
    )
    replace_once(
        "flutter/windows/runner/Runner.rc",
        'VALUE "OriginalFilename", "rustdesk.exe" "\\0"',
        f'VALUE "OriginalFilename", "{EXE_NAME}.exe" "\\0"',
    )
    # The portable packer is the outer exe people download and has its own version info.
    replace_once(
        "libs/portable/Cargo.toml",
        'description = "RustDesk Remote Desktop"',
        f'description = "{DISPLAY_NAME} Remote Desktop"',
    )
    replace_once(
        "libs/portable/Cargo.toml",
        'ProductName = "RustDesk"',
        f'ProductName = "{DISPLAY_NAME}"',
    )
    replace_once(
        "libs/portable/Cargo.toml",
        'OriginalFilename = "rustdesk.exe"',
        f'OriginalFilename = "{EXE_NAME}.exe"',
    )
    replace_once(
        "libs/portable/Cargo.toml",
        'FileDescription = "RustDesk Remote Desktop"',
        f'FileDescription = "{DISPLAY_NAME} Remote Desktop"',
    )
    replace_once(
        "flutter/windows/runner/main.cpp",
        'std::wstring app_name = L"RustDesk";',
        f'std::wstring app_name = L"{APP_NAME}";',
    )
    # The window title, which is also how a second start finds the open window.
    replace_once(
        "flutter/windows/runner/main.cpp",
        "  HWND hwnd = ::FindWindowW(getWindowClassName(), app_name.c_str());",
        f'  app_name = L"{DISPLAY_NAME}";\n  HWND hwnd = ::FindWindowW(getWindowClassName(), app_name.c_str());',
    )
    # Texts: RustDesk puts the app name in place of "RustDesk" in every translation and in the
    # {app name} placeholders. People read the display name there.
    replace_once(
        "src/lang.rs",
        "                let app_name = crate::get_app_name();\n",
        f'                let app_name = "{DISPLAY_NAME}".to_owned();\n',
    )
    replace_once(
        "src/lang.rs",
        "    let (name, placeholder_value) = extract_placeholder(&name);\n",
        "    let (name, placeholder_value) = extract_placeholder(&name);\n"
        "    let placeholder_value = placeholder_value\n"
        f'        .map(|v| if v == crate::get_app_name() {{ "{DISPLAY_NAME}".to_owned() }} else {{ v }});\n',
    )
    # The name in Settings, Apps of Windows.
    replace_once(
        "src/platform/windows.rs",
        "/v DisplayName /t REG_SZ /d \\\"{app_name}\\\"",
        f"/v DisplayName /t REG_SZ /d \\\"{DISPLAY_NAME}\\\"",
    )
    # The tooltip of the tray icon.
    replace_all(
        "src/tray.rs",
        "                crate::get_app_name(),\n                translate(",
        f'                "{DISPLAY_NAME}",\n                translate(',
        2,
    )
    replace_once(
        "flutter/lib/desktop/widgets/tabbar_widget.dart",
        '"RustDesk",\n                              style: TextStyle(fontSize: 13),',
        f'"{DISPLAY_NAME}",\n                              style: TextStyle(fontSize: 13),',
    )

    replace_once(
        "flutter/lib/common.dart",
        "static const Color accent = Color(0xFF0071FF);",
        f"static const Color accent = Color(0xFF{AZURE});",
    )
    replace_once(
        "flutter/lib/common.dart",
        "static const Color accent50 = Color(0x770071FF);",
        f"static const Color accent50 = Color(0x77{AZURE});",
    )
    replace_once(
        "flutter/lib/common.dart",
        "static const Color accent80 = Color(0xAA0071FF);",
        f"static const Color accent80 = Color(0xAA{AZURE});",
    )
    replace_once(
        "flutter/lib/common.dart",
        "static const Color button = Color(0xFF2C8CFF);",
        f"static const Color button = Color(0xFF{AZURE_STRONG});",
    )
    replace_once(
        "flutter/lib/desktop/pages/desktop_home_page.dart",
        "Color.fromARGB(255, 226, 66, 188),\n                  Color.fromARGB(255, 244, 114, 124),",
        "Color.fromARGB(255, {}, {}, {}),\n                  Color.fromARGB(255, {}, {}, {}),".format(*MIDNIGHT, *PANEL),
    )
    replace_once(
        "flutter/lib/desktop/pages/desktop_tab_page.dart",
        "body: DesktopTab(\n              controller: tabController,\n              tail: Offstage(",
        "body: DesktopTab(\n              controller: tabController,\n              showTitle: true,\n              tail: Offstage(",
    )
    theme()
    polish()
    type_scale()
    updates()
    copy_on_click()
    about_page()
    narrow_settings()
    title_buttons()
    fixed_size_window()
    shortcut_names()
    connection_window()
    no_update_card()
    remove_quit_button()
    reachable_only_while_open()

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
