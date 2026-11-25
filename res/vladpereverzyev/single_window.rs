// One window on screen. While someone is connected the connection manager is shown, so the home
// window steps aside; it comes back when the last connection ends. The home window is only hidden
// (never closed), so the process stays alive and reachable while a session is open. Only the home
// window of this process is touched: the connection manager runs in its own process, so its window
// is never matched. Driven by the connection lifecycle hooks in src/server/connection.rs.

use winapi::{
    shared::{
        minwindef::{BOOL, DWORD, FALSE, LPARAM, TRUE},
        windef::HWND,
    },
    um::{
        processthreadsapi::GetCurrentProcessId,
        winuser::{
            EnumWindows, GetWindowTextW, GetWindowThreadProcessId, SetForegroundWindow, ShowWindow,
            SW_HIDE, SW_SHOW,
        },
    },
};

const TITLE: &str = "Vladyslav Pereverzyev";

struct Found {
    pid: DWORD,
    hwnd: Option<HWND>,
}

/// Hide the home window while `connected`, show it again otherwise. Any failure is swallowed so it
/// can never break a connection.
pub fn set_connected(connected: bool) {
    unsafe {
        let mut found = Found {
            pid: GetCurrentProcessId(),
            hwnd: None,
        };
        EnumWindows(Some(enum_proc), &mut found as *mut _ as LPARAM);
        if let Some(hwnd) = found.hwnd {
            if connected {
                ShowWindow(hwnd, SW_HIDE);
            } else {
                ShowWindow(hwnd, SW_SHOW);
                SetForegroundWindow(hwnd);
            }
        }
    }
}

unsafe extern "system" fn enum_proc(hwnd: HWND, lparam: LPARAM) -> BOOL {
    let found = &mut *(lparam as *mut Found);
    let mut pid: DWORD = 0;
    GetWindowThreadProcessId(hwnd, &mut pid);
    if pid != found.pid {
        return TRUE; // another process, such as the connection manager
    }
    let mut buf = [0u16; 128];
    let n = GetWindowTextW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
    if n > 0 && String::from_utf16_lossy(&buf[..n as usize]) == TITLE {
        found.hwnd = Some(hwnd);
        return FALSE; // the home window; stop enumerating
    }
    TRUE
}
