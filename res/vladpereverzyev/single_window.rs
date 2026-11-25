// One window on screen, in one place. While the connection manager is up (from the moment a peer
// starts connecting, not only once it is let in), the home window steps aside, and it comes back
// when the manager closes. A monitor thread keeps this true by watching for the manager window,
// instead of tying it to the moment a session authorizes, so the two windows are never shown side
// by side during the connect handshake.
//
// The home window is only hidden (never closed), so the process stays alive and reachable while a
// session is open. The connection manager runs in its own process, so it is found by title across
// the process boundary and, when it first appears, moved onto the home window's spot. Started from
// the connection hook in src/server/connection.rs. Any failure is swallowed, so it can never break
// a connection.

use std::ptr::null_mut;
use std::sync::atomic::{AtomicBool, AtomicI64, Ordering};
use std::time::Duration;

use winapi::{
    shared::{
        minwindef::{BOOL, DWORD, FALSE, LPARAM, TRUE},
        windef::{HWND, RECT},
    },
    um::{
        processthreadsapi::GetCurrentProcessId,
        winuser::{
            EnumWindows, GetWindowRect, GetWindowTextW, GetWindowThreadProcessId, IsWindowVisible,
            SetForegroundWindow, SetWindowPos, ShowWindow, SWP_NOACTIVATE, SWP_NOSIZE,
            SWP_NOZORDER, SW_HIDE, SW_SHOW,
        },
    },
};

const TITLE: &str = "Vladyslav Pereverzyev";

static MONITOR: AtomicBool = AtomicBool::new(false);
static HOME_CENTRE: AtomicI64 = AtomicI64::new(0); // packed: (x << 32) | (y as u32)

/// Start the monitor the first time a peer begins connecting; it runs for the life of the app.
pub fn ensure_monitor() {
    if MONITOR.swap(true, Ordering::SeqCst) {
        return;
    }
    std::thread::spawn(|| unsafe {
        let pid = GetCurrentProcessId();
        loop {
            tick(pid);
            std::thread::sleep(Duration::from_millis(150));
        }
    });
}

unsafe fn tick(pid: DWORD) {
    let home = match find(Search {
        pid,
        other_process: false,
        require_visible: false,
        hwnd: None,
    }) {
        Some(h) => h,
        None => return,
    };
    let home_visible = IsWindowVisible(home) != 0;
    if home_visible {
        // Remember where the home window is, to drop the connection manager onto the same spot.
        let mut r: RECT = std::mem::zeroed();
        GetWindowRect(home, &mut r);
        let cx = (r.left + r.right) / 2;
        let cy = (r.top + r.bottom) / 2;
        HOME_CENTRE.store(((cx as i64) << 32) | (cy as u32 as i64), Ordering::SeqCst);
    }
    let cm = find(Search {
        pid,
        other_process: true,
        require_visible: true,
        hwnd: None,
    });
    match cm {
        Some(cm) => {
            if home_visible {
                ShowWindow(home, SW_HIDE);
            }
            // Keep the manager on the home window's spot, centred, so it reads as a swap in place
            // even if it tries to open or settle elsewhere.
            let packed = HOME_CENTRE.load(Ordering::SeqCst);
            let cx = (packed >> 32) as i32;
            let cy = packed as u32 as i32;
            let mut cr: RECT = std::mem::zeroed();
            GetWindowRect(cm, &mut cr);
            let (w, h) = (cr.right - cr.left, cr.bottom - cr.top);
            let (tx, ty) = (cx - w / 2, cy - h / 2);
            if (cr.left - tx).abs() > 2 || (cr.top - ty).abs() > 2 {
                SetWindowPos(cm, null_mut(), tx, ty, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
            }
        }
        None => {
            if !home_visible {
                ShowWindow(home, SW_SHOW);
                SetForegroundWindow(home);
            }
        }
    }
}

struct Search {
    pid: DWORD,
    other_process: bool, // false: a window of this process; true: a window of another process
    require_visible: bool,
    hwnd: Option<HWND>,
}

unsafe fn find(mut s: Search) -> Option<HWND> {
    EnumWindows(Some(enum_proc), &mut s as *mut _ as LPARAM);
    s.hwnd
}

unsafe extern "system" fn enum_proc(hwnd: HWND, lparam: LPARAM) -> BOOL {
    let s = &mut *(lparam as *mut Search);
    let mut wpid: DWORD = 0;
    GetWindowThreadProcessId(hwnd, &mut wpid);
    let in_this = wpid == s.pid;
    if s.other_process == in_this {
        return TRUE; // wrong side of the process boundary
    }
    if s.require_visible && IsWindowVisible(hwnd) == 0 {
        return TRUE;
    }
    // The connection manager retitles its window with the peer id ("Vladyslav Pereverzyev - 123"),
    // so match on the name being present rather than on the exact title.
    let mut buf = [0u16; 128];
    let n = GetWindowTextW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
    if n > 0 && String::from_utf16_lossy(&buf[..n as usize]).contains(TITLE) {
        s.hwnd = Some(hwnd);
        return FALSE;
    }
    TRUE
}
