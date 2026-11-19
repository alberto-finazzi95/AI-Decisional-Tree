"""Write a SonarCloud analysis link and metadata to the GitHub Actions summary."""

import os
from pathlib import Path
from urllib.parse import urlencode


def main() -> None:
    """Append the SonarCloud dashboard link, branch, and commit to the job summary."""
    summary_path = os.environ["GITHUB_STEP_SUMMARY"]
    project_key = os.environ["SONAR_PROJECT_KEY"]
    branch = os.environ["GITHUB_REF_NAME"]
    commit = os.environ["GITHUB_SHA"]

    query = urlencode({"id": project_key, "branch": branch})
    summary = (
        "## SonarCloud analysis\n\n"
        "The analysis was uploaded successfully. View its Quality Gate and metrics "
        f"in the [SonarCloud dashboard](https://sonarcloud.io/dashboard?{query}).\n\n"
        f"- Branch: `{branch}`\n"
        f"- Commit: `{commit}`\n"
    )

    with Path(summary_path).open("a", encoding="utf-8") as file:
        file.write(summary)


if __name__ == "__main__":
    main()
