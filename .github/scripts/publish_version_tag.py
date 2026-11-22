"""Create and push the current software-version tag when it does not exist."""

import re
import subprocess
import sys

VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a Git command and return its captured output."""
    return subprocess.run(
        ["git", *args],
        check=check,
        capture_output=True,
        text=True,
    )


def remote_tag_exists(tag: str) -> bool:
    """Return whether the exact tag is present on origin."""
    result = git("ls-remote", "--tags", "--refs", "origin", f"refs/tags/{tag}")
    return bool(result.stdout.strip())


def main() -> None:
    """Publish the supplied semantic-version tag unless it already exists remotely."""
    if len(sys.argv) != 2 or VERSION_PATTERN.fullmatch(sys.argv[1]) is None:
        raise SystemExit("Usage: publish_version_tag.py MAJOR.MINOR.PATCH")

    version = sys.argv[1]
    tag = version

    if remote_tag_exists(tag):
        print(f"Tag {tag} already exists on origin; nothing to publish.")
        return

    existing_local_tag = git("tag", "--list", tag).stdout.strip()
    if existing_local_tag:
        tag_commit = git("rev-parse", f"refs/tags/{tag}^{{}}").stdout.strip()
        head_commit = git("rev-parse", "HEAD").stdout.strip()
        if tag_commit != head_commit:
            raise SystemExit(f"Local tag {tag} exists but does not point to the current commit.")
    else:
        git("tag", tag, "HEAD")
        print(f"Created local tag {tag}.")

    push = git("push", "origin", f"refs/tags/{tag}", check=False)
    if push.returncode != 0:
        if remote_tag_exists(tag):
            print(f"Tag {tag} was published by another run; nothing further to do.")
            return
        raise SystemExit(push.stderr.strip() or f"Failed to publish tag {tag}.")

    print(f"Published tag {tag} to origin.")


if __name__ == "__main__":
    main()
