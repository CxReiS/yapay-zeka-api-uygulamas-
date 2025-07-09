import subprocess


def run(cmd):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    output = result.stdout.strip()
    if result.stderr:
        output += ("\n" + result.stderr.strip())
    print(output)
    return output


def main():
    run("git fetch origin")
    diff = run("git diff origin/main...HEAD --stat")
    if diff:
        with open("update_report.txt", "w", encoding="utf-8") as f:
            f.write(diff + "\n")
    else:
        print("✅ Güncel")


if __name__ == "__main__":
    main()
