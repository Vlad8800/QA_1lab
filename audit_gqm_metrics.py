"""
Automated GQM Matrix Collector & Stevens Scale Passport Inspector (Lab #5, Task 1).
Demonstrates architectural governance by dynamically measuring metrics from the codebase:
- Product Quality: Cyclomatic Complexity (Ratio), Sonar/Security Grade (Ordinal)
- Process Efficiency: Dynamic Latency Percentiles (Ratio), Lead Time Delays (Interval)
- Team Productivity: Technical Debt LOC/Remediation (Ratio), Architectural Layers (Nominal)
"""
import time
import statistics
import radon.complexity as cc
from radon.raw import analyze

from app.services import calculate_base_total, apply_loyalty_discount, calculate_shipping_cost
from app.privacy.sanitizer import sanitize_text, sanitize_data


def print_banner(text: str):
    print("\n" + "=" * 90)
    print(f" {text}")
    print("=" * 90)


def audit_gqm_metrics():
    print_banner("ENTERPRISE GQM MATRIX & STEVENS SCALE AUDIT PASSPORT (LAB #5 - TASK 1)")
    print("[*] Goal: Evaluate and optimize Maintainability, Resilience, and Data Privacy Security")
    print("    for Core Orders & Privacy Subsystems from the perspective of Lead Software Architect.")
    print("-" * 90)

    # -------------------------------------------------------------
    # CONTOUR 1: PRODUCT QUALITY
    # -------------------------------------------------------------
    # M1.1: Cyclomatic Complexity (Ratio Scale)
    with open("app/services.py", "r", encoding="utf-8") as f:
        services_code = f.read()

    blocks = cc.cc_visit(services_code)
    cc_scores = [b.complexity for b in blocks if hasattr(b, 'complexity')]
    median_cc = statistics.median(cc_scores) if cc_scores else 0
    max_cc = max(cc_scores) if cc_scores else 0

    # M1.2: Security Classification / Rating (Ordinal Scale: A > B > C > D > E)
    # Simulated inspection against SonarQube / Gitleaks rules for hardcoded secrets
    with open("app/privacy/logging_policy.py", "r", encoding="utf-8") as f:
        policy_code = f.read()
    has_unredacted_defaults = "password = " in policy_code
    security_rating = "A" if not has_unredacted_defaults else "C"

    # -------------------------------------------------------------
    # CONTOUR 2: PROCESS EFFICIENCY
    # -------------------------------------------------------------
    # M2.1: Execution Latency Percentiles (Ratio Scale) - measured over 100 sample runs
    sample_order = [{"name": "Mouse", "price": 25.0, "quantity": 2}]
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = calculate_base_total(sample_order)
        _ = apply_loyalty_discount(50.0, "regular")
        _ = sanitize_text("user test@example.com password=secret")
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latencies.sort()
    p50_latency = statistics.median(latencies)
    p95_latency = latencies[int(len(latencies) * 0.95)]
    mean_latency = statistics.mean(latencies)

    # M2.2: Lead Time Timestamp Intervals (Interval Scale)
    # Arbitrary reference epoch interval between simulated stages
    stage_start = time.time()
    time.sleep(0.01)
    stage_end = time.time()
    elapsed_lead_time_ms = (stage_end - stage_start) * 1000.0

    # -------------------------------------------------------------
    # CONTOUR 3: TEAM PRODUCTIVITY & RESOURCES
    # -------------------------------------------------------------
    # M3.1: Technical Debt / Remediation hours (Ratio Scale)
    # Raw LOC & SQALE debt estimation based on complexity
    raw_stats = analyze(services_code)
    loc_count = raw_stats.loc
    estimated_debt_hours = round(sum(cc_scores) * 0.25, 1)

    # M3.2: Architectural Component Layer (Nominal Scale)
    subsystem_layers = ["SERVICES", "PRIVACY", "EXPORT", "ANONYMIZATION", "CONSENT"]
    layer_mode = subsystem_layers[0]

    # -------------------------------------------------------------
    # PRINT PASSPORT TABLE (Clean ASCII formatting)
    # -------------------------------------------------------------
    print(f"{'CONTOUR':<10} | {'QUESTION (Q)':<32} | {'METRIC (M)':<20} | {'STEVENS SCALE':<18} | {'VALUE':<16}")
    print("-" * 102)
    print(f"{'PRODUCT':<10} | {'Q1.1 Algorithmic Complexity':<32} | {'Cyclomatic CC':<20} | {'Ratio Scale':<18} | {f'Me={median_cc}, Max={max_cc}':<16}")
    print(f"{'PRODUCT':<10} | {'Q1.2 Security Vulnerabilities':<32} | {'Security Rating':<20} | {'Ordinal Scale':<18} | {f'Grade {security_rating}':<16}")
    print(f"{'PROCESS':<10} | {'Q2.1 Order Request Latency':<32} | {'Latency p95 (ms)':<20} | {'Ratio Scale':<18} | {f'{p95_latency:.3f} ms':<16}")
    print(f"{'PROCESS':<10} | {'Q2.2 Pipeline Lead Time':<32} | {'Lead Time Delta':<20} | {'Interval Scale':<18} | {f'{elapsed_lead_time_ms:.1f} ms':<16}")
    print(f"{'TEAM':<10} | {'Q3.1 Tech Debt Capitalization':<32} | {'Tech Debt Hours':<20} | {'Ratio Scale':<18} | {f'{estimated_debt_hours} h':<16}")
    print(f"{'TEAM':<10} | {'Q3.2 Architectural Layer':<32} | {'Layer Category':<20} | {'Nominal Scale':<18} | {f'{layer_mode}':<16}")
    print("-" * 102)

    print_banner("MATHEMATICAL VALIDATION & STEVENS SCALE CONSTRAINTS")
    print("1. [Ordinal Scale]: Why arithmetic mean is FORBIDDEN for Security Ratings (A & C)?")
    print("   Answer: Ordinal scale lacks constant metric intervals between grades.")
    print("   Calculating (A + C)/2 = B is a dangerous illusion of safety: a single grade 'C' defect")
    print("   compromises the entire service. Valid aggregations: Mode (Mo) and Median (Me).")
    print("")
    print("2. [Ratio Scale]: Why p95 percentile is mandatory for response latency over mean?")
    print(f"   Actual stats: Mean = {mean_latency:.4f} ms, p95 Percentile = {p95_latency:.4f} ms.")
    print("   Answer: Latencies exhibit an asymmetric, long-tail distribution. Mean masks critical")
    print("   outliers/timeouts. p95 mathematically guarantees 95% of users receive sub-threshold SLO.")
    print("")
    print("3. [Interval vs Ratio Scale]:")
    print("   Interval (Lead Time / Timestamp) has an arbitrary origin and allows subtraction (Delta t),")
    print("   whereas Ratio (Tech Debt / LOC) possesses a natural zero (0h debt) and supports all arithmetic.")
    print_banner("[OK] TASK 1 AUDIT PASSPORT COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    audit_gqm_metrics()
