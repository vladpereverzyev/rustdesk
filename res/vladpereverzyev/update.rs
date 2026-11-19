// Updates of the Vladyslav Pereverzyev remote desktop from the releases of
// vladpereverzyev/rustdesk on GitHub.
//
// brand.py copies this file to src/vladpereverzyev_update.rs at build time. RustDesk checks its
// own server and verifies a metadata file signed with the RustDesk key; this app asks the
// GitHub API instead and trusts a file only when it comes from a release of its own
// repository over HTTPS with the size and SHA-256 digest that GitHub gives for it. Download,
// verification of the file and installation (`--update`) stay those of RustDesk.

use crate::{
    common::SOFTWARE_UPDATE_URL,
    hbbs_http::{create_http_client_async_with_url_strict, create_http_client_with_url_strict},
    update_metadata::VerifiedUpdateArtifact,
};
use hbb_common::{bail, get_version_number, ResultType};
use serde_json::Value;

const REPO: &str = "vladpereverzyev/rustdesk";
const ASSET: &str = "vladpereverzyev.exe";
const USER_AGENT: &str = "vladpereverzyev";

// The number of the tag the build was made from (1.0.0 for v1.0.0), set by the workflow. Builds
// without a tag have none and never offer an update.
pub const VERSION: Option<&str> = option_env!("VLADPEREVERZYEV_VERSION");

fn release_page(tag: &str) -> String {
    format!("https://github.com/{REPO}/releases/tag/{tag}")
}

fn stable_version(tag: &str) -> Option<&str> {
    let version = tag.strip_prefix('v')?;
    let parts: Vec<&str> = version.split('.').collect();
    if parts.len() == 3 && parts.iter().all(|p| !p.is_empty() && p.chars().all(|c| c.is_ascii_digit())) {
        Some(version)
    } else {
        None
    }
}

fn clear() {
    SOFTWARE_UPDATE_URL.lock().unwrap().clear();
}

pub async fn check() -> ResultType<()> {
    let Some(current) = VERSION else {
        clear();
        return Ok(());
    };
    let url = format!("https://api.github.com/repos/{REPO}/releases/latest");
    let client = create_http_client_async_with_url_strict(&url).await?;
    let response = client
        .get(&url)
        .header("User-Agent", USER_AGENT)
        .header("Accept", "application/vnd.github+json")
        .send()
        .await?;
    if !response.status().is_success() {
        clear();
        bail!("Update check failed with HTTP status {}", response.status());
    }
    let release: Value = serde_json::from_slice(&response.bytes().await?)?;
    let tag = release["tag_name"].as_str().unwrap_or_default();
    match stable_version(tag) {
        Some(latest) if get_version_number(latest) > get_version_number(current) => {
            let page = release_page(tag);
            #[cfg(feature = "flutter")]
            {
                let mut m = std::collections::HashMap::new();
                m.insert("name", "check_software_update_finish");
                m.insert("url", page.as_str());
                if let Ok(data) = serde_json::to_string(&m) {
                    let _ = crate::flutter::push_global_event(crate::flutter::APP_TYPE_MAIN, data);
                }
            }
            *SOFTWARE_UPDATE_URL.lock().unwrap() = page;
        }
        _ => clear(),
    }
    Ok(())
}

// The file of the release behind `release_page_url`, with the size and digest GitHub gives.
pub fn artifact(release_page_url: &str) -> ResultType<VerifiedUpdateArtifact> {
    let Some(tag) = release_page_url.strip_prefix(&format!("https://github.com/{REPO}/releases/tag/")) else {
        bail!("Not a release page of this app: {}", release_page_url);
    };
    let Some(version) = stable_version(tag) else {
        bail!("Not a release tag of this app: {}", tag);
    };
    let url = format!("https://api.github.com/repos/{REPO}/releases/tags/{tag}");
    let client = create_http_client_with_url_strict(&url)?;
    let response = client
        .get(&url)
        .header("User-Agent", USER_AGENT)
        .header("Accept", "application/vnd.github+json")
        .send()?;
    if !response.status().is_success() {
        bail!("Release lookup failed with HTTP status {}", response.status());
    }
    let release: Value = serde_json::from_slice(&response.bytes()?)?;
    let Some(asset) = release["assets"]
        .as_array()
        .and_then(|assets| assets.iter().find(|a| a["name"].as_str() == Some(ASSET)))
    else {
        bail!("The release {} has no {}", tag, ASSET);
    };
    let download_url = format!("https://github.com/{REPO}/releases/download/{tag}/{ASSET}");
    if asset["browser_download_url"].as_str() != Some(download_url.as_str()) {
        bail!("Unexpected download address for {}", ASSET);
    }
    let size = asset["size"].as_u64().unwrap_or(0);
    let sha256 = asset["digest"]
        .as_str()
        .and_then(|d| d.strip_prefix("sha256:"))
        .unwrap_or_default()
        .to_ascii_lowercase();
    if size == 0 || sha256.len() != 64 || !sha256.chars().all(|c| c.is_ascii_hexdigit()) {
        bail!("GitHub gives no size or SHA-256 digest for {}", ASSET);
    }
    Ok(VerifiedUpdateArtifact {
        version: version.to_owned(),
        url: download_url,
        size,
        sha256,
    })
}
