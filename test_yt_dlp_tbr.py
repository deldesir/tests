import pytest
import subprocess
import json
import os
import logging

# Define the YouTube URL here
YOUTUBE_URL = "https://www.youtube.com/watch?v=hBC7i-vHWsU"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def youtube_url():
    # Define the YouTube URL here
    return YOUTUBE_URL

# Fixture to install all versions of yt-dlp
@pytest.fixture(scope="session")
def install_all_yt_dlp(request):
    installed_versions = set()  # Set to keep track of installed versions
    
    def _install_all_yt_dlp(versions):
        for version in versions:
            if version not in installed_versions:
                try:
                    # Dynamically construct the path to yt-dlp binary based on the version
                    subprocess.run(["pipx", "install", f"--suffix=_{version}", f"yt-dlp=={version}", "--force"], check=True)
                    subprocess.run(["pipx", "ensurepath"], check=True)
                    # Check the installed version of yt-dlp
                    yt_dlp_version = version.replace(".", "-")
                    yt_dlp_path = f"/root/.local/share/pipx/venvs/yt-dlp-{yt_dlp_version}/bin/yt-dlp"
                    installed_version_output = subprocess.check_output([yt_dlp_path, "--version"], stderr=subprocess.PIPE)
                    installed_version = installed_version_output.decode('utf-8').strip()
                    assert installed_version == version, f"Failed to install yt-dlp version {version}. Installed version: {installed_version}"
                    logger.info(f"Installed yt-dlp version: {installed_version}")
                    installed_versions.add(version)  # Add installed version to set
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install yt-dlp: {e}")
                    raise e
    return _install_all_yt_dlp

# Fixture to fetch video information
@pytest.fixture(scope="function")
def video_info(youtube_url, yt_dlp_version):
    try:
        yt_dlp_version = yt_dlp_version.replace(".", "-") 
        yt_dlp_path = os.path.expanduser(f"/root/.local/share/pipx/venvs/yt-dlp-{yt_dlp_version}/bin/yt-dlp")
        info_output = subprocess.check_output([yt_dlp_path, "--print-json", "--skip-download", youtube_url], stderr=subprocess.PIPE)
        decoded_output = info_output.decode('utf-8').strip()
        return json.loads(decoded_output)  # Decode JSON
    except (subprocess.CalledProcessError, json.decoder.JSONDecodeError) as e:
        logger.error(f"Failed to retrieve format information for video {youtube_url}: {e}")
        return None

# Function to download video
def download_video(video_url, format_options, video_info, yt_dlp_version):
    if video_info is None:
        logger.warning("Skipping download due to missing video info.")
        return "SKIPPED"
    # Define output file path
    video_id = video_info['id']
    output_file = f"{video_id} - {yt_dlp_version}.%(ext)s"
    # Download the video
    yt_dlp_version = yt_dlp_version.replace(".", "-")
    yt_dlp_path = os.path.expanduser(f"/root/.local/share/pipx/venvs/yt-dlp-{yt_dlp_version}/bin/yt-dlp")
    command = [yt_dlp_path] + format_options + ["-o", output_file, video_url]
    try:
        logger.info(f"Downloading video to: {output_file}")
        subprocess.run(command, check=True)
        return "SUCCESS"
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e}")
        return "FAILED"

# Test function using the youtube_url and video_info fixtures
@pytest.mark.parametrize("yt_dlp_version", [
    "2024.03.10",
    "2024.04.09",
    "2024.05.27",
])
def test_yt_dlp_download(install_all_yt_dlp, yt_dlp_version, youtube_url, video_info, request):
    # Install all versions of yt-dlp
    versions = [
        "2024.03.10",
        "2024.04.09",
        "2024.05.27,
    ]
    install_all_yt_dlp(versions)
    
    logger.info(f"Testing video: {youtube_url} with yt-dlp version {yt_dlp_version}")
    logger.info("----------------------------------------------------------------")
    
    # Check if video_info is retrieved successfully
    assert video_info is not None, "Failed to retrieve video information."
    
    # Print available formats and qualities
    if 'formats' in video_info:
        logger.info("Available formats and qualities:")
        for format_info in video_info['formats']:
            logger.info(f"{format_info['format_id']}: {format_info['ext']} - {format_info['tbr']} kbps")
    
    # Download the video
    format_options = ["--format", "best", "--format-sort", "tbr~1000"]
    download_result = download_video(youtube_url, format_options, video_info, yt_dlp_version)
    
    # Check if download is successful
    assert download_result == "SUCCESS", f"Video download failed for video: {youtube_url} using yt-dlp version {yt_dlp_version}"
    logger.info("Download successful!")

