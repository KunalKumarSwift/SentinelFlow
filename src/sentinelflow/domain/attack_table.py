"""A small, curated subset of MITRE ATT&CK used to ground investigations (data only)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttackTechnique:
    """One ATT&CK technique and the signal words that suggest it."""

    technique_id: str
    name: str
    tactic: str
    keywords: tuple[str, ...]


TECHNIQUES: tuple[AttackTechnique, ...] = (
    AttackTechnique(
        "T1110",
        "Brute Force",
        "Credential Access",
        ("brute_force_success", "brute", "force", "login_failed"),
    ),
    AttackTechnique(
        "T1078",
        "Valid Accounts",
        "Initial Access",
        ("login_succeeded", "impossible_travel", "travel"),
    ),
    AttackTechnique(
        "T1552",
        "Unsecured Credentials",
        "Credential Access",
        ("access_key_anomaly", "key", "leaked"),
    ),
    AttackTechnique(
        "T1530", "Data from Cloud Storage", "Collection", ("getobject", "listbuckets", "bucket")
    ),
    AttackTechnique(
        "T1566.002",
        "Spearphishing Link",
        "Initial Access",
        ("phishing_click", "phishing", "url_clicked"),
    ),
    AttackTechnique(
        "T1059.001",
        "PowerShell",
        "Execution",
        ("suspicious_process", "powershell", "process_started"),
    ),
    AttackTechnique(
        "T1071",
        "Application Layer Protocol",
        "Command and Control",
        ("outbound_connection", "beacon"),
    ),
    AttackTechnique(
        "T1567",
        "Exfiltration Over Web Service",
        "Exfiltration",
        ("large_download", "download", "exfiltration"),
    ),
)
