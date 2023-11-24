#!/usr/bin/python3
"""Calculate the version based on the git commit count and update pyproject.toml"""
import subprocess
from warnings import warn

branch = "HEAD"


def calculate_version():
    """Calculate the version based on the git commit count since the latest tag"""
    tags = subprocess.check_output(["git", "tag"]).decode().strip().split("\n")

    # Handle no tags condition
    if len(tags) == 1 and tags[0] == "":
        tags = []

    # Check for latest tag and skip if there is no tag
    latest_tag = None
    if tags and max(tags).startswith("v"):
        latest_tag = max(tags)

    if latest_tag:
        commit_count = int(
            subprocess.check_output(["git", "rev-list", "--count", f"{latest_tag}..{branch}"])
            .decode()
            .strip()
        )
    else:
        commit_count = int(
            subprocess.check_output(["git", "rev-list", "--count", branch]).decode().strip()
        )

    major_version = latest_tag.split(".")[0].split("v")[1] if latest_tag else "0"
    minor_version = latest_tag.split(".")[1] if latest_tag else "0"
    patch_version = int(latest_tag.split(".")[2]) + commit_count

    return f"{major_version}.{minor_version}.{patch_version}"


def compare_version(new_version: str, old_version: str):
    """Compare two versions"""
    return list(map(int, new_version.split("."))) <= list(map(int, old_version.split(".")))


def update_version(version):
    """Update version on pyproject.toml"""
    with open("pyproject.toml", "r", encoding="utf-8") as file:
        original_content = file.readlines()

    updated_content = []
    for line in original_content:
        # Check if the new version is greater than the old version
        if line.startswith("version =") and compare_version(version, line.split('"')[1]):
            warn("New version is not greater than the old version")
            return

        if line.startswith("version ="):
            updated_content.append(f'version = "{version}"\n')
        else:
            updated_content.append(line)

    with open("pyproject.toml", "w", encoding="utf-8") as file:
        file.writelines(updated_content)


# Calculate the version and update pyproject.toml
version = calculate_version()
update_version(version)

print(version)
