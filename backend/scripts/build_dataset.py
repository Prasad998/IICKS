"""Regenerates the templated block of incidents.csv and kb_articles.csv.

The original synthetic dataset has, per category, a small hand-written "seed"
block (the first few rows) followed by a much larger "generated" block that
turned out to reuse only a handful of underlying phrasings hundreds of times
(e.g. Authentication's 200 rows had only 64 unique descriptions). That meant
similarity search would return several literally-identical rows for one
query, and the category centroids were built from far less real vocabulary
than the row count suggested.

This script keeps every seed row untouched, and replaces only the generated
block with rows built from a much larger combinatorial template space, large
enough that every replacement row is genuinely unique. Row counts, category
balance, and ticket/article ID ranges are all preserved exactly - this is a
content fix, not a schema or volume change.

Usage (from backend/):
    python scripts/build_dataset.py
"""

import csv
import itertools
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INCIDENTS_PATH = DATA_DIR / "incidents.csv"
ARTICLES_PATH = DATA_DIR / "kb_articles.csv"

# Each category's seed block (untouched) and generated block (rebuilt) sizes,
# taken from the current files' exact ID ranges.
CATEGORY_ID_PREFIX = {
    "Authentication": 1,
    "Network": 2,
    "Application": 3,
    "Endpoint": 4,
    "Database": 5,
}
INCIDENT_SEED_COUNT = 4
INCIDENT_GENERATED_COUNT = 196
ARTICLE_SEED_COUNT = 2
ARTICLE_GENERATED_COUNT = 198


# ---------------------------------------------------------------------------
# Vocabulary pools. Each category gets: symptom/resolution template pairs,
# a list of systems/applications, and a list of context or user-role slots.
# Combinations = len(templates) * len(systems) * len(slots), which comfortably
# exceeds the ~196 unique rows needed per category.
# ---------------------------------------------------------------------------

INCIDENT_POOLS = {
    "Authentication": {
        "templates": [
            ("{user} reports login rejected for {system} after a recent password reset",
             "Reset Active Directory cache and resync the identity profile for {system}"),
            ("{user} is locked out of {system} after multiple failed MFA attempts",
             "Unlock the account and re-enroll the MFA device for {system}"),
            ("Single sign-on fails for {system} after a password change for {user}",
             "Refresh the SSO token and clear the browser session for {system}"),
            ("{user} cannot access {system} due to a missing role assignment",
             "Assign the correct role for {system} through the identity governance workflow"),
            ("{user}'s session for {system} expires immediately after signing in",
             "Extend the session token lifetime and clear cached credentials for {system}"),
            ("{user} is unable to complete identity verification for {system}",
             "Re-issue the identity verification challenge for {system} and confirm device trust"),
            ("{system} rejects sign-in for {user} after a phone number change",
             "Re-enroll the MFA device for {system} using the updated phone number"),
            ("{user} cannot reset their own password for {system}",
             "Unlock the self-service password reset flow for {system} and verify security questions"),
            ("Access to {system} is denied for {user} after an org transfer",
             "Update the access policy for {system} to reflect the new organizational unit"),
            ("{system} sign-in loops back to the login page for {user}",
             "Clear the stale authentication cookie and reissue a fresh session for {system}"),
        ],
        "systems": [
            "SAP", "Salesforce", "Workday", "Okta", "the HR portal",
            "the finance application", "the VPN portal", "Confluence",
            "the customer support console", "the procurement system",
            "the expense reporting tool", "the intranet", "ServiceNow",
            "the vendor management portal",
        ],
        "slots": [
            "a new employee", "a contractor", "a manager", "a remote worker",
            "a finance team member", "a support engineer", "an executive assistant",
            "a warehouse supervisor", "an IT administrator", "a vendor account",
        ],
        "slot_key": "user",
    },
    "Network": {
        "templates": [
            ("{user} reports {system} disconnecting every few minutes",
             "Update the client software and rotate the connection profile for {system}"),
            ("{user} experiences packet loss when using {system}",
             "Validate the routing path and fail over the impacted segment for {system}"),
            ("{user} sees high latency spikes on {system} during peak hours",
             "Tune the QoS policy and rebalance traffic on {system}"),
            ("{system} intermittently drops connectivity for {user}",
             "Restart the tunnel and renew its certificate for {system}"),
            ("DNS resolution fails intermittently for {user} on {system}",
             "Flush the resolver cache and validate DNS forwarders for {system}"),
            ("{user} cannot establish a connection through {system}",
             "Check the firmware version and reset the session for {system}"),
            ("Throughput on {system} degrades for {user} during business hours",
             "Adjust the MTU size and inspect for a duplex mismatch on {system}"),
            ("{system} certificate expired, blocking access for {user}",
             "Renew the certificate and restart the service for {system}"),
            ("{user} reports call quality issues over {system}",
             "Open the required media ports and re-negotiate the tunnel for {system}"),
            ("A routing loop was detected affecting {user} on {system}",
             "Correct the static route and clear the routing table on {system}"),
        ],
        "systems": [
            "Cisco AnyConnect", "Palo Alto GlobalProtect", "the SD-WAN link",
            "the office WiFi", "the branch office firewall", "the VPN gateway",
            "the load balancer", "the DNS resolver", "the proxy server",
            "the MPLS circuit", "Zscaler", "the wireless controller",
            "the site-to-site tunnel", "the network switch stack",
        ],
        "slots": [
            "a remote office user", "a branch office employee", "an analyst",
            "a new employee", "a warehouse worker", "an executive",
            "a night-shift operator", "a field technician", "a contractor",
            "a support engineer",
        ],
        "slot_key": "user",
    },
    "Application": {
        "templates": [
            ("{system} failed {context} with a timeout error",
             "Increase the timeout threshold and restart {system}"),
            ("{system} crashed {context} due to a memory leak",
             "Deploy the patched release and restart {system}"),
            ("{system} queue backlog is growing {context}",
             "Scale out the worker pool and clear the stuck messages for {system}"),
            ("{system} returns HTTP 500 errors intermittently {context}",
             "Roll back the last release and redeploy {system}"),
            ("{system} deployment failed {context}",
             "Fix the misconfigured feature flag and redeploy {system}"),
            ("{system} hit a race condition under concurrent load {context}",
             "Apply the locking fix and restart {system}"),
            ("{system} served stale cached data {context}",
             "Invalidate the cache and warm it before restarting {system}"),
            ("{system} failed to process records {context}",
             "Patch the malformed input handler and rerun {system}"),
            ("{system} showed a sudden spike in error rate {context}",
             "Roll forward the hotfix and monitor {system} closely"),
            ("{system} hung indefinitely waiting on a downstream dependency {context}",
             "Add a circuit breaker and restart {system}"),
        ],
        "systems": [
            "the payroll batch job", "the order management API",
            "the inventory sync service", "the reporting pipeline", "the ETL job",
            "the CRM sync job", "the invoicing service", "the e-commerce checkout flow",
            "the mobile app backend", "the integration middleware",
            "the ticketing system", "the notification service",
            "the document generation service", "the scheduling engine",
        ],
        "slots": [
            "overnight", "during month-end close", "during peak traffic",
            "right after a deployment", "during a scheduled failover",
            "during the nightly batch window", "during quarter close",
            "during a marketing campaign", "during a schema migration",
            "while syncing with a partner system",
        ],
        "slot_key": "context",
    },
    "Endpoint": {
        "templates": [
            ("{system} for {user} won't boot after the last update",
             "Reimage the device and reapply the standard build for {user}"),
            ("{system} for {user} shows a blue screen error",
             "Roll back the driver and re-run diagnostics on the device for {user}"),
            ("{system} for {user} is stuck mid-encryption",
             "Resume the encryption job and verify the recovery key for {user}"),
            ("A patch failed to install on {system} for {user}",
             "Retry the patch deployment and clear the update cache for {user}"),
            ("{system} for {user} is flagged as non-compliant",
             "Push the compliance policy again and re-check status for {user}"),
            ("{system} for {user} is offline and unreachable",
             "Restart the network stack and re-register the device for {user}"),
            ("{system} for {user} has abnormally fast battery drain",
             "Replace the battery and recalibrate power settings for {user}"),
            ("{system} for {user} fails to enroll in device management",
             "Re-enroll the device and reissue the management certificate for {user}"),
            ("A peripheral connected to {system} is not detected for {user}",
             "Reinstall the driver and reset the USB controller for {user}"),
            ("{system} for {user} repeatedly disconnects from the docking setup",
             "Update the docking station firmware and reseat the device for {user}"),
        ],
        "systems": [
            "a company laptop", "a desktop workstation", "a mobile device",
            "a VDI session client", "a point-of-sale terminal", "a field service tablet",
            "a warehouse handheld scanner", "a kiosk terminal", "a conference room PC",
            "a ruggedized laptop", "a call center workstation", "a lab test workstation",
            "a branch office desktop", "a loaner laptop",
        ],
        "slots": [
            "a new hire", "a field technician", "an executive",
            "a warehouse operator", "a remote employee", "a contractor",
            "a support engineer", "a finance analyst", "a shift supervisor",
            "an IT administrator",
        ],
        "slot_key": "user",
    },
    "Database": {
        "templates": [
            ("{system} storage threshold reached {context}",
             "Extend storage allocation and archive stale records for {system}"),
            ("{system} CPU usage spiked {context}",
             "Tune the slow query and add a covering index for {system}"),
            ("Backup failed for {system} because the volume is full {context}",
             "Increase the backup volume and rerun the scheduled job for {system}"),
            ("{system} connection pool is exhausted {context}",
             "Increase the pool size and restart the connection manager for {system}"),
            ("Replication lag detected on {system} {context}",
             "Resync the replica and monitor throughput for {system}"),
            ("A deadlock was detected on {system} {context}",
             "Identify the blocking transaction and adjust the isolation level for {system}"),
            ("{system} query timeout occurred {context}",
             "Rewrite the query plan and update statistics for {system}"),
            ("Data corruption was suspected on {system} {context}",
             "Restore from the last verified backup and run integrity checks on {system}"),
            ("{system} failed over unexpectedly {context}",
             "Investigate the failover trigger and rebalance the cluster for {system}"),
            ("{system} could not connect after a certificate rotation {context}",
             "Update the trust store and restart the connection pool for {system}"),
        ],
        "systems": [
            "the Oracle database", "the PostgreSQL cluster", "the SQL Server instance",
            "the MongoDB replica set", "the reporting database", "the production database",
            "the backup volume", "the analytics warehouse", "the customer data store",
            "the billing database", "the audit log database", "the session store",
            "the search index cluster", "the data lake ingestion job",
        ],
        "slots": [
            "during month-end reporting", "during checkout processing",
            "during the payroll run", "during an audit", "during the nightly ETL window",
            "during a schema migration", "during peak trading hours",
            "during a scheduled maintenance window", "during a failover test",
            "while ingesting a large batch",
        ],
        "slot_key": "context",
    },
}

ARTICLE_POOLS = {
    "Authentication": {
        "templates": [
            ("Resolve {system} sign-in failures {detail}",
             "Checklist covering session tokens, MFA enrollment, and identity sync steps to restore access to {system} {detail}."),
            ("Unlock and restore access to {system} {detail}",
             "Procedure for clearing lockouts, resetting MFA, and validating role assignment for {system} {detail}."),
            ("Diagnose SSO token issues on {system} {detail}",
             "Guide for refreshing SSO tokens, clearing browser sessions, and checking identity provider status for {system} {detail}."),
            ("Fix password reset problems on {system} {detail}",
             "Runbook for validating self-service reset flows and security question resets on {system} {detail}."),
            ("Investigate access denied errors on {system} {detail}",
             "Reference for reviewing access policies, org unit assignment, and governance approvals for {system} {detail}."),
            ("Recover from MFA enrollment failures on {system} {detail}",
             "Steps for re-enrolling authenticator devices and validating phone number changes for {system} {detail}."),
        ],
        "systems": INCIDENT_POOLS["Authentication"]["systems"],
        "details": [
            "for remote workers", "for new hires", "after a password policy change",
            "on mobile devices", "for contractor accounts", "after an identity provider migration",
            "for shared service accounts", "during a security incident", "after a phone number change",
            "for privileged accounts", "on VPN-connected devices", "for federated partner accounts",
            "after an org restructuring", "for API service accounts", "on legacy browsers",
            "after a directory sync", "for VIP executive accounts", "during onboarding",
            "for offboarded accounts pending cleanup", "after a certificate renewal",
        ],
    },
    "Network": {
        "templates": [
            ("Troubleshoot {system} instability {detail}",
             "Checklist for client version, profile corruption, tunnel logs, and gateway failover validation for {system} {detail}."),
            ("Diagnose packet loss and latency on {system} {detail}",
             "Guide covering routing checks, QoS tuning, and segment failover for {system} {detail}."),
            ("Restore connectivity after {system} certificate expiry {detail}",
             "Runbook for renewing certificates and restarting services on {system} {detail}."),
            ("Resolve DNS resolution failures involving {system} {detail}",
             "Reference for flushing resolver caches and validating forwarders for {system} {detail}."),
            ("Fix throughput degradation on {system} {detail}",
             "Steps for MTU tuning, duplex checks, and firmware validation on {system} {detail}."),
            ("Recover from a routing loop affecting {system} {detail}",
             "Procedure for correcting static routes and clearing routing tables on {system} {detail}."),
        ],
        "systems": INCIDENT_POOLS["Network"]["systems"],
        "details": [
            "for remote offices", "for branch locations", "on mobile clients",
            "after a firmware update", "for site-to-site tunnels", "during peak business hours",
            "for VIP users", "after an ISP failover", "on guest networks", "for VoIP traffic",
            "after a configuration change", "for multi-site deployments", "on legacy hardware",
            "after a provider outage", "for high-availability pairs", "during a planned migration",
            "for satellite offices", "on encrypted tunnels", "for contractor VPN access",
            "after a certificate authority change",
        ],
    },
    "Application": {
        "templates": [
            ("Troubleshoot {system} timeout and crash errors {detail}",
             "Checklist for diagnosing timeouts, memory leaks, and crash loops in {system} {detail}."),
            ("Clear queue backlogs in {system} {detail}",
             "Runbook for scaling workers and draining stuck messages in {system} {detail}."),
            ("Roll back a failed {system} deployment {detail}",
             "Steps for reverting a release and validating feature flags for {system} {detail}."),
            ("Resolve intermittent HTTP 500 errors from {system} {detail}",
             "Guide for isolating faulty releases and redeploying {system} {detail}."),
            ("Fix stale cache issues in {system} {detail}",
             "Reference for invalidating and warming caches in {system} {detail}."),
            ("Diagnose downstream dependency hangs in {system} {detail}",
             "Procedure for adding circuit breakers and restarting {system} {detail}."),
        ],
        "systems": INCIDENT_POOLS["Application"]["systems"],
        "details": [
            "during month-end close", "during peak traffic", "after a deployment",
            "during a schema migration", "during quarter close", "for the nightly batch window",
            "during a marketing campaign", "for partner integrations", "after a dependency upgrade",
            "for multi-region deployments", "during a scheduled failover", "for high-volume tenants",
            "after a configuration rollout", "during a load test", "for legacy API consumers",
            "after a database migration", "during a canary release", "for background job processing",
            "after a certificate rotation", "for third-party webhook consumers",
        ],
    },
    "Endpoint": {
        "templates": [
            ("Recover {system} that won't boot {detail}",
             "Reimaging and standard-build checklist for {system} {detail}."),
            ("Resolve blue screen errors on {system} {detail}",
             "Driver rollback and diagnostic procedure for {system} {detail}."),
            ("Fix a stuck disk encryption job on {system} {detail}",
             "Recovery-key validation and resume procedure for {system} {detail}."),
            ("Retry a failed patch deployment on {system} {detail}",
             "Steps for clearing the update cache and redeploying patches on {system} {detail}."),
            ("Restore compliance status on {system} {detail}",
             "Runbook for re-pushing compliance policy and re-checking status on {system} {detail}."),
            ("Re-enroll {system} in device management {detail}",
             "Certificate reissue and enrollment procedure for {system} {detail}."),
        ],
        "systems": INCIDENT_POOLS["Endpoint"]["systems"],
        "details": [
            "for new hires", "for field technicians", "for executives",
            "for warehouse kiosks", "for remote employees", "for contractor devices",
            "for shared workstations", "for point-of-sale terminals", "for conference room hardware",
            "for loaner devices", "after an OS upgrade", "for BYOD devices",
            "for devices returning from repair", "for offboarded employee devices",
            "for devices in low-connectivity sites", "after a firmware update",
            "for devices enrolled via Autopilot", "for devices with third-party VPN clients",
            "for devices flagged by antivirus", "for devices missing a compliance certificate",
        ],
    },
    "Database": {
        "templates": [
            ("Resolve storage threshold alerts on {system} {detail}",
             "Archival and storage-extension checklist for {system} {detail}."),
            ("Tune high CPU usage on {system} {detail}",
             "Query tuning and indexing guide for {system} {detail}."),
            ("Recover from a failed backup job on {system} {detail}",
             "Volume-expansion and rerun procedure for {system} {detail}."),
            ("Fix connection pool exhaustion on {system} {detail}",
             "Pool sizing and connection manager restart runbook for {system} {detail}."),
            ("Resolve replication lag on {system} {detail}",
             "Resync and throughput monitoring guide for {system} {detail}."),
            ("Diagnose and clear deadlocks on {system} {detail}",
             "Blocking-transaction identification and isolation-level procedure for {system} {detail}."),
        ],
        "systems": INCIDENT_POOLS["Database"]["systems"],
        "details": [
            "during month-end reporting", "during payroll processing",
            "for audit workloads", "during nightly ETL windows", "during schema migrations",
            "during peak trading hours", "for high-availability pairs", "during failover testing",
            "for multi-tenant workloads", "for reporting workloads", "for data warehouse loads",
            "for customer-facing read replicas", "during a certificate rotation",
            "for encrypted-at-rest volumes", "for cross-region replication",
            "for backup verification jobs", "during a capacity review",
            "for disaster-recovery drills", "during a maintenance window",
            "for compliance audits",
        ],
    },
}


def unique_rows(pool: dict, count: int, seed_texts: set) -> list[tuple]:
    """Generates `count` unique (primary_text, secondary_text) tuples from a
    template/system/slot pool, skipping anything that collides with an
    existing seed row or an earlier generated row."""
    templates = pool["templates"]
    systems = pool["systems"]
    slots = pool.get("slots") or pool.get("details")
    slot_key = pool.get("slot_key", "detail")

    combos = itertools.product(templates, systems, slots)
    results = []
    seen = set(seed_texts)

    for (primary_tmpl, secondary_tmpl), system, slot in combos:
        kwargs = {"system": system, slot_key: slot}
        primary = primary_tmpl.format(**kwargs)
        if primary in seen:
            continue
        secondary = secondary_tmpl.format(**kwargs)
        seen.add(primary)
        results.append((primary, secondary))
        if len(results) == count:
            break

    if len(results) < count:
        raise RuntimeError(
            f"Only generated {len(results)}/{count} unique rows - widen the template/system/slot pools."
        )
    return results


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rebuild_incidents() -> tuple[int, int]:
    rows = load_csv(INCIDENTS_PATH)
    by_category: dict[str, list[dict]] = {}
    for row in rows:
        by_category.setdefault(row["category"], []).append(row)

    before_unique = len({r["description"] for r in rows})

    new_rows: list[dict] = []
    for category, items in by_category.items():
        items_sorted = sorted(items, key=lambda r: int(r["ticket_id"].split("-")[1]))
        seed = items_sorted[:INCIDENT_SEED_COUNT]
        seed_texts = {r["description"] for r in seed}

        pool = INCIDENT_POOLS[category]
        generated_pairs = unique_rows(pool, INCIDENT_GENERATED_COUNT, seed_texts)

        prefix = CATEGORY_ID_PREFIX[category]
        generated_rows = [
            {
                "ticket_id": f"INC-{prefix}00{str(index).zfill(3)}",
                "description": description,
                "category": category,
                "resolution": resolution,
            }
            for index, (description, resolution) in enumerate(generated_pairs, start=1)
        ]
        new_rows.extend(seed)
        new_rows.extend(generated_rows)

    new_rows.sort(key=lambda r: (r["category"], int(r["ticket_id"].split("-")[1])))
    write_csv(INCIDENTS_PATH, ["ticket_id", "description", "category", "resolution"], new_rows)

    after_unique = len({r["description"] for r in new_rows})
    return before_unique, after_unique


def rebuild_articles() -> tuple[int, int]:
    rows = load_csv(ARTICLES_PATH)
    by_category: dict[str, list[dict]] = {}
    for row in rows:
        by_category.setdefault(row["category"], []).append(row)

    before_unique = len({r["title"] for r in rows})

    new_rows: list[dict] = []
    for category, items in by_category.items():
        items_sorted = sorted(items, key=lambda r: int(r["article_id"].split("-")[1]))
        seed = items_sorted[:ARTICLE_SEED_COUNT]
        seed_texts = {r["title"] for r in seed}

        pool = ARTICLE_POOLS[category]
        generated_pairs = unique_rows(pool, ARTICLE_GENERATED_COUNT, seed_texts)

        prefix = CATEGORY_ID_PREFIX[category]
        generated_rows = [
            {
                "article_id": f"KB-{prefix}00{str(index).zfill(3)}",
                "title": title,
                "category": category,
                "content": content,
            }
            for index, (title, content) in enumerate(generated_pairs, start=1)
        ]
        new_rows.extend(seed)
        new_rows.extend(generated_rows)

    new_rows.sort(key=lambda r: (r["category"], int(r["article_id"].split("-")[1])))
    write_csv(ARTICLES_PATH, ["article_id", "title", "category", "content"], new_rows)

    after_unique = len({r["title"] for r in new_rows})
    return before_unique, after_unique


def main() -> None:
    inc_before, inc_after = rebuild_incidents()
    art_before, art_after = rebuild_articles()

    print("incidents.csv:")
    print(f"  unique descriptions: {inc_before} -> {inc_after} (out of 1000 rows)")
    print("kb_articles.csv:")
    print(f"  unique titles: {art_before} -> {art_after} (out of 1000 rows)")


if __name__ == "__main__":
    main()
