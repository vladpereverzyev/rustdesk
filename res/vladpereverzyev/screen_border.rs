// A red frame around the whole screen while someone is connected to this computer, so the
// person sitting at it sees at a glance that a remote session is open. RustDesk shows only the
// connection-manager window, which is easy to miss behind other windows. The frame is a
// borderless, always-on-top, click-through window shaped as a thin rectangle outline: it never
// takes focus and the mouse passes through it. It is shown when the first connection that can see
// the computer authorizes and removed when the last one ends (see the hooks in
// src/server/connection.rs).

use std::sync::{mpsc, Mutex, Once};
use std::thread::JoinHandle;

use winapi::{
    shared::{
        minwindef::{HINSTANCE, LPARAM, LRESULT, UINT, WPARAM},
        windef::{HGDIOBJ, HWND},
    },
    um::{
        libloaderapi::GetModuleHandleW,
        wingdi::{CombineRgn, CreateRectRgn, CreateSolidBrush, DeleteObject, RGB, RGN_DIFF},
        winuser::{
            CreateWindowExW, DefWindowProcW, DispatchMessageW, GetMessageW, GetSystemMetrics,
            PostMessageW, PostQuitMessage, RegisterClassExW, SetLayeredWindowAttributes,
            SetWindowRgn, ShowWindow, TranslateMessage, LWA_ALPHA, MSG, SM_CXVIRTUALSCREEN,
            SM_CYVIRTUALSCREEN, SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SW_SHOWNA, WM_CLOSE,
            WM_DESTROY, WNDCLASSEXW, WS_EX_LAYERED, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW,
            WS_EX_TOPMOST, WS_EX_TRANSPARENT, WS_POPUP,
        },
    },
};

const BORDER_PX: i32 = 6; // thickness of the frame
const COLOUR: (u8, u8, u8) = (227, 36, 43); // a strong red
const CLASS: &str = "VladyslavPereverzyevScreenBorder";

struct Border {
    hwnd: usize, // the overlay window; usize so the handle can cross threads
    thread: JoinHandle<()>,
}

static BORDER: Mutex<Option<Border>> = Mutex::new(None);

/// Show the red frame when `active`, remove it otherwise. Idempotent; the lock serializes calls
/// so show and hide never overlap. Any failure is swallowed: a missing frame must never break a
/// connection.
pub fn set_active(active: bool) {
    let mut guard = match BORDER.lock() {
        Ok(g) => g,
        Err(_) => return,
    };
    if active {
        if guard.is_some() {
            return;
        }
        let (tx, rx) = mpsc::channel::<usize>();
        let thread = std::thread::spawn(move || run(tx));
        // Wait until the window exists (sub-millisecond), so a later hide always has its handle.
        match rx.recv() {
            Ok(hwnd) if hwnd != 0 => *guard = Some(Border { hwnd, thread }),
            _ => {
                let _ = thread.join();
            }
        }
    } else if let Some(border) = guard.take() {
        unsafe {
            PostMessageW(border.hwnd as HWND, WM_CLOSE, 0, 0);
        }
        let _ = border.thread.join();
    }
}

fn wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

unsafe extern "system" fn wndproc(hwnd: HWND, msg: UINT, w: WPARAM, l: LPARAM) -> LRESULT {
    if msg == WM_DESTROY {
        PostQuitMessage(0);
        return 0;
    }
    DefWindowProcW(hwnd, msg, w, l)
}

fn ensure_class(hinstance: HINSTANCE) {
    static REGISTER: Once = Once::new();
    REGISTER.call_once(|| unsafe {
        let name = wide(CLASS);
        let mut wc: WNDCLASSEXW = std::mem::zeroed();
        wc.cbSize = std::mem::size_of::<WNDCLASSEXW>() as u32;
        wc.lpfnWndProc = Some(wndproc);
        wc.hInstance = hinstance;
        wc.hbrBackground = CreateSolidBrush(RGB(COLOUR.0, COLOUR.1, COLOUR.2));
        wc.lpszClassName = name.as_ptr();
        RegisterClassExW(&wc);
    });
}

fn run(tx: mpsc::Sender<usize>) {
    unsafe {
        let hinstance = GetModuleHandleW(std::ptr::null()) as HINSTANCE;
        ensure_class(hinstance);
        let name = wide(CLASS);
        let x = GetSystemMetrics(SM_XVIRTUALSCREEN);
        let y = GetSystemMetrics(SM_YVIRTUALSCREEN);
        let w = GetSystemMetrics(SM_CXVIRTUALSCREEN);
        let h = GetSystemMetrics(SM_CYVIRTUALSCREEN);
        let hwnd = CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_LAYERED,
            name.as_ptr(),
            name.as_ptr(),
            WS_POPUP,
            x,
            y,
            w,
            h,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            hinstance,
            std::ptr::null_mut(),
        );
        if hwnd.is_null() {
            let _ = tx.send(0);
            return;
        }
        // Only the frame is part of the window: the outer rectangle minus an inner one. The hole
        // is outside the window, so everything below shows and clicks through it.
        let outer = CreateRectRgn(0, 0, w, h);
        let inner = CreateRectRgn(BORDER_PX, BORDER_PX, w - BORDER_PX, h - BORDER_PX);
        CombineRgn(outer, outer, inner, RGN_DIFF);
        SetWindowRgn(hwnd, outer, 1); // the window now owns `outer`
        DeleteObject(inner as HGDIOBJ);
        // A layered window is invisible until this is set; 255 keeps the frame fully opaque.
        SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA);
        ShowWindow(hwnd, SW_SHOWNA);
        let _ = tx.send(hwnd as usize);
        let mut msg: MSG = std::mem::zeroed();
        while GetMessageW(&mut msg, std::ptr::null_mut(), 0, 0) > 0 {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }
}
