import os
import json

def guess_service(file_content):
    content = file_content.lower()
    if "flask" in content or "fastapi" in content:
        return "Web API Service"
    elif "subprocess" in content or "netmiko" in content:
        return "Automation / Network Command Service"
    elif "sqlalchemy" in content or "models" in content:
        return "Database Service"
    elif "vault" in content or "secrets" in content:
        return "Credential Manager"
    elif "scheduler" in content or "cron" in content:
        return "Task Scheduler"
    else:
        return "Unknown"

def scan_directory(path):
    report = {
        "project_root": os.path.basename(path),
        "structure": {},
        "services_detected": [],
        "security_risks": []
    }

    for root, dirs, files in os.walk(path):
        rel_path = os.path.relpath(root, path)
        if "__pycache__" in rel_path:
            continue

        report["structure"][rel_path] = files

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r") as f:
                        content = f.read()
                        service = guess_service(content)
                        if service != "Unknown":
                            report["services_detected"].append({
                                "file": full_path,
                                "guessed_service": service
                            })
                        if "password" in content or "secret" in content or "token" in content:
                            report["security_risks"].append({
                                "file": full_path,
                                "keyword_found": "Sensitive word (password/secret/token)"
                            })
                except:
                    pass

    return report

def print_summary(report):
    print("\n🤖 AI ONBOARDING SUMMARY")
    print(f"📁 Project: {report['project_root']}")
    print("\n🧩 Detected Services:")
    for s in report["services_detected"]:
        print(f" - {s['guessed_service']} → {s['file']}")

    print("\n🚨 Potential Security Risks:")
    if not report["security_risks"]:
        print(" - None found.")
    else:
        for r in report["security_risks"]:
            print(f" - {r['file']} (keyword: {r['keyword_found']})")

    print("\n📦 Files and Structure:")
    for path, files in report["structure"].items():
        print(f" - {path}/: {len(files)} files")

    print("\n✅ Report saved to: ai_engine/onboarding_report.json")

if __name__ == "__main__":
    scan_path = os.path.abspath(".")
    report = scan_directory(scan_path)
    print_summary(report)

    # Save to file
    with open("ai_engine/onboarding_report.json", "w") as f:
        json.dump(report, f, indent=4)
