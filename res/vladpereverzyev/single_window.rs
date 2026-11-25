// One window on screen, in one place. While someone is connected the connection manager is shown,
// so the home window steps aside, and it comes back when the last connection ends. The home window
// is only hidden (never closed), so the process stays alive and reachable while a session is open.
// To make it read as a swap and not a window jumping elsewhere, the connection manager (which runs
// in its own process) is moved to where the home window was. Driven by the connection lifecycle
// hooks in src/server/connection.rs. Any failure is swallowed so it can never break a connection.

use std::ptr::null_mut;
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
    let mut buf = [0u16; 128];
    let n = GetWindowTextW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
    if n > 0 && String::from_utf16_lossy(&buf[..n as usize]) == TITLE {
        s.hwnd = Some(hwnd);
        return FALSE;
    }
    TRUE
}

/// Hide the home window while `connected`, show it again otherwise. While hiding, move the
/// connection manager to where the home window was, so it reads as a swap in the same place.
pub fn set_connected(connected: bool) {
    unsafe {
        let pid = GetCurrentProcessId();
        let home = match find(Search {
            pid,
            other_process: false,
            require_visible: false,
            hwnd: None,
        }) {
            Some(h) => h,
            None => return,
        };
        if !connected {
            ShowWindow(home, SW_SHOW);
            SetForegroundWindow(home);
            return;
        }
        let mut r: RECT = std::mem::zeroed();
        GetWindowRect(home, &mut r);
        let cx = (r.left + r.right) / 2;
        let cy = (r.top + r.bottom) / 2;
        ShowWindow(home, SW_HIDE);
        // The connection manager opens a moment later, in its own process; wait for it and move it
        // onto the home window's spot, centred, without touching its size or focus.
        std::thread::spawn(move || unsafe {
            for _ in 0..30 {
                if let Some(cm) = find(Search {
                    pid,
                    other_process: true,
                    require_visible: true,
                    hwnd: None,
                }) {
                    let mut cr: RECT = std::mem::zeroed();
                    GetWindowRect(cm, &mut cr);
                    let w = cr.right - cr.left;
                    let h = cr.bottom - cr.top;
                    SetWindowPos(
                        cm,
                        null_mut(),
                        cx - w / 2,
                        cy - h / 2,
                        0,
                        0,
                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE,
                    );
                    break;
                }
                std::thread::sleep(Duration::from_millis(100));
            }
        });
    }
}
