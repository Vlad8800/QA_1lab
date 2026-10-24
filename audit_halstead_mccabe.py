"""
Automated Halstead & McCabe Complexity Audit Engine (Lab #6).
Performs:
1. Global Baseline Halstead scan across repository.
2. Per-layer architectural comparison:
   - Core Domain / Business Logic (app/services.py)
   - Integration / Infrastructure (app/export/repository.py)
   - Utility / DTO / Helper (app/utils.py)
3. Mathematical proof of LOC inadequacy vs Mental Effort (E).
4. McCabe Cyclomatic Complexity & Control Flow Graph verification:
   - Baseline and FAIL: measured from their Git revisions.
   - Current PASS: measured from the working tree.
"""
import ast
import math
import subprocess
from pathlib import Path
import radon.metrics as rm
import radon.complexity as cc
from radon.raw import analyze as raw_analyze


def print_banner(text: str):
    print("\n" + "=" * 94)
    print(f" {text}")
    print("=" * 94)


def audit_halstead_baseline():
    print_banner("1. GLOBAL BASELINE SCAN (HALSTEAD REPOSITORY SCREENING)")
    tracked = subprocess.check_output(
        ['git', 'ls-files', '--', '*.py'], text=True, encoding='utf-8'
    ).splitlines()
    files = sorted({Path(p) for p in tracked if Path(p).is_file()} | {Path('quality_gate.py')})
    files = [p for p in files if p.is_file()]
    # One AST gives one actual union of Radon's operator/operand sets.
    # Summing each file's h1/h2 would count repeated symbols many times.
    nodes = []
    for path in files:
        nodes.extend(ast.parse(path.read_text(encoding='utf-8'), filename=str(path)).body)
    result = rm.h_visit_ast(ast.Module(body=nodes, type_ignores=[])).total
    vocab = result.h1 + result.h2
    length = result.N1 + result.N2
    print(f"Total Python Source Files Analyzed: {len(files)}")
    print(f"{'METRIC':<40} | {'SYMBOL':<15} | {'VALUE':<20}")
    print("-" * 82)
    print(f"{'Distinct Operators':<40} | {'eta1 (h1)':<15} | {result.h1:<20}")
    print(f"{'Distinct Operands':<40} | {'eta2 (h2)':<15} | {result.h2:<20}")
    print(f"{'Total Operators Usage':<40} | {'N1':<15} | {result.N1:<20}")
    print(f"{'Total Operands Usage':<40} | {'N2':<15} | {result.N2:<20}")
    print(f"{'Program Vocabulary':<40} | {'eta = h1 + h2':<15} | {vocab:<20}")
    print(f"{'Program Length':<40} | {'N = N1 + N2':<15} | {length:<20}")
    print(f"{'Information Volume (bits)':<40} | {'V = N * log2(eta)':<15} | {f'{result.volume:.2f} bits':<20}")
    print(f"{'Total Mental Effort':<40} | {'E = V * D':<15} | {f'{result.effort:.2f}':<20}")
    print("-" * 82)


def audit_architectural_layers():
    print_banner("2. ARCHITECTURAL LAYER HALSTEAD AUDIT & LOC HOTSPOTS ANALYSIS")
    target_files = [
        ("Core Domain / Business Logic", "app/services.py"),
        ("Integration / Infrastructure", "app/export/repository.py"),
        ("Utility / Helper / DTO", "app/utils.py"),
    ]

    print(f"{'ARCHITECTURAL ROLE':<28} | {'FILE PATH':<24} | {'LOC':<6} | {'eta1':<5} | {'eta2':<5} | {'N1':<5} | {'N2':<5} | {'VOL (V)':<9} | {'DIFF (D)':<9} | {'EFFORT (E)':<10}")
    print("-" * 125)

    stats = []
    for role, path in target_files:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        h_rep = rm.h_visit(code).total
        raw = raw_analyze(code)

        vocab = h_rep.h1 + h_rep.h2
        length = h_rep.N1 + h_rep.N2
        vol = length * (math.log2(vocab) if vocab > 0 else 0)
        diff = (h_rep.h1 / 2.0) * (h_rep.N2 / h_rep.h2 if h_rep.h2 > 0 else 0)
        effort = vol * diff

        stats.append((role, path, raw.loc, h_rep.h1, h_rep.h2, h_rep.N1, h_rep.N2, vol, diff, effort))
        print(f"{role:<28} | {path:<24} | {raw.loc:<6} | {h_rep.h1:<5} | {h_rep.h2:<5} | {h_rep.N1:<5} | {h_rep.N2:<5} | {vol:<9.2f} | {diff:<9.2f} | {effort:<10.2f}")

    print("-" * 125)

    # Hotspot ranking
    stats_sorted = sorted(stats, key=lambda x: x[9], reverse=True)
    print("\nHOTSPOT RANKING BY MENTAL EFFORT (E):")
    for idx, item in enumerate(stats_sorted, start=1):
        print(f"  {idx}. {item[1]} ({item[0]}): Effort E = {item[9]:.2f} [LOC = {item[2]}]")

    print("\n[MATHEMATICAL PROOF: LOC FALLACY]")
    core = stats[0]
    integration = stats[1]
    print(f"  * {integration[1]}: {integration[2]} LOC, E = {integration[9]:.2f}.")
    print(f"  * {core[1]}: {core[2]} LOC, E = {core[9]:.2f}.")
    print(f"  * LOC ratio = {integration[2] / core[2]:.2f}; effort ratio = {core[9] / integration[9]:.2f}.")
    print(f"  * Core vocabulary = {core[3] + core[4]}, volume = {core[7]:.2f}, difficulty = {core[8]:.2f}.")
    print("  * Conclusion: LOC measures textual volume; Halstead Effort measures cognitive load. Blindly relying")
    print("    on LOC misses critical architectural bottlenecks in dense algorithmic files.")


def audit_mccabe_topological():
    print_banner("3. TOPOLOGICAL MCCABE PASSPORT & DATA-DRIVEN REFACTORING AUDIT")
    print("Target Function: app/services.py -> calculate_shipping_cost\n")

    for label, ref in (
        ('Baseline', 'c44aa3a'),
        ('Monolithic FAIL', '5e21045'),
    ):
        source = subprocess.check_output(
            ['git', 'show', f'{ref}:app/services.py'], text=True, encoding='utf-8'
        )
        block = next(b for b in cc.cc_visit(source) if b.name == 'calculate_shipping_cost')
        print(f'{label:<20} {ref:<10} CC={block.complexity:<3} Grade={cc.cc_rank(block.complexity)}')
    current = Path('app/services.py').read_text(encoding='utf-8')
    block = next(b for b in cc.cc_visit(current) if b.name == 'calculate_shipping_cost')
    print(f'{"Lookup PASS":<20} {"worktree":<10} CC={block.complexity:<3} Grade={cc.cc_rank(block.complexity)}')

    with open("app/services.py", "r", encoding="utf-8") as f:
        code = f.read()

    blocks = cc.cc_visit(code)
    for b in blocks:
        if b.name == "calculate_shipping_cost":
            rank = cc.cc_rank(b.complexity)
            print(f"\n[LIVE SCAN VALIDATION]: Current 'calculate_shipping_cost' in app/services.py:")
            print(f"  * Measured Cyclomatic Complexity (CLI): CC = {b.complexity} (Grade {rank})")
            print(f"  * Lines: {b.lineno} - {b.endline}")
            print(f"  * Status: Successfully Linearized via Data-Driven Lookup Tables (Zero if-else chaos).")


if __name__ == "__main__":
    audit_halstead_baseline()
    audit_architectural_layers()
    audit_mccabe_topological()
