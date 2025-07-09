import subprocess


def run(cmd: str) -> subprocess.CompletedProcess:
    """Run a shell command and print its output."""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    return result


def main() -> None:
    """Check for updates compared to origin/main and write a report if needed."""
    run("git fetch origin")
    diff_result = run("git diff origin/main...HEAD --stat")
    diff_output = (diff_result.stdout + diff_result.stderr).strip()

    if diff_result.returncode == 0 and not diff_output:
        print("✅ Güncel")
    else:
        with open("update_report.txt", "w", encoding="utf-8") as f:
            f.write(diff_output + "\n")


if __name__ == "__main__":
    main()
