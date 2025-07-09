import subprocess


def run(cmd: str) -> tuple[int, str]:
    """Run a shell command and return its code and output."""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    return result.returncode, output


def main() -> None:
    """Check for updates compared to origin/main."""
    code, fetch_output = run("git fetch origin")
    if code != 0:
        with open("update_report.txt", "w", encoding="utf-8") as f:
            f.write(fetch_output + "\n")
        return

    code, diff_output = run("git diff origin/main...HEAD --stat")
    if code == 0 and not diff_output:
        print("✅ Güncel")
    else:
        with open("update_report.txt", "w", encoding="utf-8") as f:
            f.write(diff_output + "\n")


if __name__ == "__main__":
    main()
