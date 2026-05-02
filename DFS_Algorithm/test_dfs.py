"""
Test script for DFS_algorithm.py
Tests both recursive_journeyGenerator and iterativeDFS against sample data
and various edge cases.

Move to the directory and run the test by typing this in the terminal

python test_dfs.py

"""

import sys
import math

# Add project root to path so imports work
sys.path.insert(0, ".")

from Controller_IO.io_handler import load_network
from DFS_Algorithm.DFS_algorithm import createAdjList, recursive_journeyGenerator, iterativeDFS


def load_sample_data():
    stops, segments = load_network(
        "Controller_IO/sample_data/stops.csv",
        "Controller_IO/sample_data/segments.csv"
    )
    return stops, segments


def test_adj_list(segments):
    print("=" * 60)
    print("TEST: createAdjList")
    print("=" * 60)
    adj = createAdjList(segments)
    print(f"  Stops in adj_list: {len(adj)}")
    for stop, segs in sorted(adj.items()):
        neighbours = [s["to"] for s in segs]
        print(f"    {stop} -> {neighbours}")
    
    # Check: every stop referenced in segments should be a key
    all_froms = set(s["from"] for s in segments)
    all_tos   = set(s["to"] for s in segments)
    all_stops_in_segs = all_froms | all_tos
    missing_from_adj = all_stops_in_segs - set(adj.keys())
    if missing_from_adj:
        print(f"  ⚠ WARNING: Stops referenced as 'to' but never as 'from': {missing_from_adj}")
        print(f"    These are LEAF nodes. If used as startpoint in iterativeDFS, it will crash!")
    else:
        print(f"  ✓ All stops appear as keys in adj_list")
    print()
    return adj


def test_basic_routes(adj, stops):
    print("=" * 60)
    print("TEST: Basic routes (both algorithms)")
    print("=" * 60)
    
    # Test a few known-good pairs
    test_pairs = [
        ("HK001", "HK004", "Central -> Causeway Bay"),
        ("HK001", "HK007", "Central -> Mong Kok"),
        ("HK002", "HK006", "Admiralty -> Jordan"),
        ("HK001", "HK013", "Central -> North Point"),
    ]
    
    for start, end, desc in test_pairs:
        print(f"\n  Route: {desc} ({start} -> {end})")
        
        # Recursive
        try:
            rec_results = recursive_journeyGenerator(adj, start, end)
            rec_count = len(rec_results) if rec_results else 0
            print(f"    Recursive: {rec_count} paths found")
        except Exception as e:
            print(f"    Recursive: ✗ CRASHED - {type(e).__name__}: {e}")
            rec_results = None
        
        # Iterative
        try:
            iter_results = iterativeDFS(adj, start, end)
            iter_count = len(iter_results) if iter_results else 0
            print(f"    Iterative: {iter_count} paths found")
        except Exception as e:
            print(f"    Iterative: ✗ CRASHED - {type(e).__name__}: {e}")
            iter_results = None
        
        # Compare results
        if rec_results is not None and iter_results is not None:
            if rec_count == iter_count:
                print(f"    ✓ Both agree: {rec_count} paths")
            else:
                print(f"    ⚠ MISMATCH: recursive={rec_count}, iterative={iter_count}")
                # Show details
                print(f"      Recursive paths:")
                for p in rec_results:
                    route = " -> ".join([p[0]["from"]] + [s["to"] for s in p])
                    print(f"        {route}")
                print(f"      Iterative paths:")
                for p in iter_results:
                    route = " -> ".join([p[0]["from"]] + [s["to"] for s in p])
                    print(f"        {route}")


def test_same_origin_dest(adj):
    print("\n" + "=" * 60)
    print("TEST: Same origin and destination")
    print("=" * 60)
    
    # Recursive
    try:
        rec = recursive_journeyGenerator(adj, "HK001", "HK001")
        print(f"  Recursive: returned {rec} (type: {type(rec).__name__})")
    except Exception as e:
        print(f"  Recursive: ✗ CRASHED - {type(e).__name__}: {e}")
    
    # Iterative
    try:
        it = iterativeDFS(adj, "HK001", "HK001")
        print(f"  Iterative: returned {it} (type: {type(it).__name__})")
    except Exception as e:
        print(f"  Iterative: ✗ CRASHED - {type(e).__name__}: {e}")


def test_nonexistent_stops(adj):
    print("\n" + "=" * 60)
    print("TEST: Non-existent stops")
    print("=" * 60)
    
    bad_pairs = [
        ("FAKE001", "HK001", "Fake start"),
        ("HK001", "FAKE002", "Fake end"),
        ("FAKE001", "FAKE002", "Both fake"),
    ]
    
    for start, end, desc in bad_pairs:
        print(f"\n  {desc}: {start} -> {end}")
        
        # Recursive
        try:
            rec = recursive_journeyGenerator(adj, start, end)
            print(f"    Recursive: returned {rec}")
        except Exception as e:
            print(f"    Recursive: ✗ CRASHED - {type(e).__name__}: {e}")
        
        # Iterative
        try:
            it = iterativeDFS(adj, start, end)
            print(f"    Iterative: returned {it}")
        except Exception as e:
            print(f"    Iterative: ✗ CRASHED - {type(e).__name__}: {e}")


def test_leaf_node_as_start(adj):
    """Test starting from a stop that has no outgoing edges in adj_list."""
    print("\n" + "=" * 60)
    print("TEST: Leaf node (stop with no outgoing segments) as start")
    print("=" * 60)
    
    # Find stops that appear as 'to' but never as 'from'
    all_tos = set()
    for segs in adj.values():
        for s in segs:
            all_tos.add(s["to"])
    leaf_nodes = all_tos - set(adj.keys())
    
    if not leaf_nodes:
        print("  (No leaf nodes in sample data with reverse segments)")
    
    for leaf in leaf_nodes:
        print(f"\n  Leaf node: {leaf}")
        try:
            it = iterativeDFS(adj, leaf, "HK001")
            print(f"    Iterative: returned {it}")
        except Exception as e:
            print(f"    Iterative: ✗ CRASHED - {type(e).__name__}: {e}")
        
        try:
            rec = recursive_journeyGenerator(adj, leaf, "HK001")
            print(f"    Recursive: returned {rec}")
        except Exception as e:
            print(f"    Recursive: ✗ CRASHED - {type(e).__name__}: {e}")


def test_max_path_length(adj):
    print("\n" + "=" * 60)
    print("TEST: max_path_length filtering")
    print("=" * 60)
    
    # Get all paths first
    all_rec = recursive_journeyGenerator(adj, "HK001", "HK007")
    all_it  = iterativeDFS(adj, "HK001", "HK007")
    
    if all_rec:
        print(f"  All recursive paths: {len(all_rec)}")
        for p in all_rec:
            print(f"    len={len(p)}: {' -> '.join([p[0]['from']] + [s['to'] for s in p])}")
    
    if all_it:
        print(f"  All iterative paths: {len(all_it)}")
        for p in all_it:
            print(f"    len={len(p)}: {' -> '.join([p[0]['from']] + [s['to'] for s in p])}")
    
    # Now test with max_path_length = 3
    print(f"\n  With max_path_length = 3:")
    rec_filtered = recursive_journeyGenerator(adj, "HK001", "HK007", max_path_length=3)
    it_filtered  = iterativeDFS(adj, "HK001", "HK007", max_path_length=3)
    
    if rec_filtered:
        print(f"    Recursive filtered: {len(rec_filtered)} paths")
        for p in rec_filtered:
            print(f"      len={len(p)}: {' -> '.join([p[0]['from']] + [s['to'] for s in p])}")
    
    if it_filtered:
        print(f"    Iterative filtered: {len(it_filtered)} paths")
        for p in it_filtered:
            print(f"      len={len(p)}: {' -> '.join([p[0]['from']] + [s['to'] for s in p])}")
    
    # Check that filtering actually worked
    if rec_filtered:
        violations = [p for p in rec_filtered if len(p) > 3]
        if violations:
            print(f"    ⚠ Recursive: {len(violations)} paths STILL exceed max_path_length!")
        else:
            print(f"    ✓ Recursive: all paths within limit")
    
    if it_filtered:
        violations = [p for p in it_filtered if len(p) > 3]
        if violations:
            print(f"    ⚠ Iterative: {len(violations)} paths STILL exceed max_path_length!")
        else:
            print(f"    ✓ Iterative: all paths within limit")


def test_disconnected_stops(adj):
    """Test stops that cannot reach each other (HK011, HK009 etc.)."""
    print("\n" + "=" * 60)
    print("TEST: Potentially disconnected / hard-to-reach stops")
    print("=" * 60)
    
    # HK009 connects only via HK010, and HK011 connects only via HK008
    tricky_pairs = [
        ("HK009", "HK013", "HKU -> North Point"),
        ("HK011", "HK007", "Kennedy Town -> Mong Kok"),
        ("HK013", "HK009", "North Point -> HKU"),
    ]
    
    for start, end, desc in tricky_pairs:
        print(f"\n  {desc}: {start} -> {end}")
        
        try:
            rec = recursive_journeyGenerator(adj, start, end)
            rec_count = len(rec) if rec else 0
            print(f"    Recursive: {rec_count} paths")
        except Exception as e:
            print(f"    Recursive: ✗ CRASHED - {type(e).__name__}: {e}")
        
        try:
            it = iterativeDFS(adj, start, end)
            it_count = len(it) if it else 0
            print(f"    Iterative: {it_count} paths")
        except Exception as e:
            print(f"    Iterative: ✗ CRASHED - {type(e).__name__}: {e}")


def test_all_pairs_exhaustive(adj, stops):
    """Run both algorithms for ALL pairs and compare counts."""
    print("\n" + "=" * 60)
    print("TEST: Exhaustive all-pairs comparison")
    print("=" * 60)
    
    stop_ids = sorted(stops.keys())
    mismatches = 0
    crashes = 0
    
    for start in stop_ids:
        for end in stop_ids:
            if start == end:
                continue
            
            try:
                rec = recursive_journeyGenerator(adj, start, end)
                rec_count = len(rec) if rec else 0
            except Exception as e:
                print(f"  ✗ Recursive CRASH {start}->{end}: {e}")
                crashes += 1
                rec_count = -1
            
            try:
                it = iterativeDFS(adj, start, end)
                it_count = len(it) if it else 0
            except Exception as e:
                print(f"  ✗ Iterative CRASH {start}->{end}: {e}")
                crashes += 1
                it_count = -1
            
            if rec_count != it_count and rec_count >= 0 and it_count >= 0:
                mismatches += 1
                print(f"  ⚠ MISMATCH {start} -> {end}: recursive={rec_count}, iterative={it_count}")
    
    total_pairs = len(stop_ids) * (len(stop_ids) - 1)
    print(f"\n  Total pairs tested: {total_pairs}")
    print(f"  Mismatches: {mismatches}")
    print(f"  Crashes: {crashes}")
    if mismatches == 0 and crashes == 0:
        print(f"  ✓ All pairs agree and no crashes!")


def test_mutable_default_bug():
    """Test if calling the functions multiple times leaks state via mutable defaults."""
    print("\n" + "=" * 60)
    print("TEST: Mutable default argument leakage")
    print("=" * 60)
    
    stops, segments = load_sample_data()
    adj = createAdjList(segments)
    
    # Call recursive twice and check results are independent
    r1 = recursive_journeyGenerator(adj, "HK001", "HK004")
    r2 = recursive_journeyGenerator(adj, "HK001", "HK004")
    
    if r1 is not None and r2 is not None:
        if len(r1) == len(r2):
            print(f"  ✓ Recursive: consistent results ({len(r1)} paths both times)")
        else:
            print(f"  ⚠ Recursive: INCONSISTENT! Call 1={len(r1)}, Call 2={len(r2)}")
    
    # Call iterative twice
    i1 = iterativeDFS(adj, "HK001", "HK004")
    i2 = iterativeDFS(adj, "HK001", "HK004")
    
    if i1 is not None and i2 is not None:
        if len(i1) == len(i2):
            print(f"  ✓ Iterative: consistent results ({len(i1)} paths both times)")
        else:
            print(f"  ⚠ Iterative: INCONSISTENT! Call 1={len(i1)}, Call 2={len(i2)}")


def test_max_path_length_filter_correctness():
    """Test the 'remove while iterating' bug in max_path_length filtering."""
    print("\n" + "=" * 60)
    print("TEST: max_path_length filter-while-iterating bug")
    print("=" * 60)
    
    stops, segments = load_sample_data()
    adj = createAdjList(segments)
    
    # Get all paths first
    all_paths = recursive_journeyGenerator(adj, "HK001", "HK007")
    if all_paths:
        lengths = [len(p) for p in all_paths]
        print(f"  All paths HK001->HK007: {len(all_paths)} paths, lengths: {sorted(lengths)}")
        
        # Now filter with max_path_length = 2 (very restrictive)
        filtered = recursive_journeyGenerator(adj, "HK001", "HK007", max_path_length=2)
        if filtered:
            bad = [p for p in filtered if len(p) > 2]
            if bad:
                print(f"  ⚠ FILTER BUG: {len(bad)} paths with length > 2 leaked through!")
                for p in bad:
                    print(f"    len={len(p)}: {' -> '.join([p[0]['from']] + [s['to'] for s in p])}")
            else:
                print(f"  ✓ Filter worked correctly: {len(filtered)} paths with length ≤ 2")
        else:
            print(f"  Filtered result: {filtered} (no paths ≤ 2 segments)")
    
    # Same test for iterative
    all_paths_it = iterativeDFS(adj, "HK001", "HK007")
    if all_paths_it:
        filtered_it = iterativeDFS(adj, "HK001", "HK007", max_path_length=2)
        if filtered_it:
            bad_it = [p for p in filtered_it if len(p) > 2]
            if bad_it:
                print(f"  ⚠ ITERATIVE FILTER BUG: {len(bad_it)} paths leaked through!")
            else:
                print(f"  ✓ Iterative filter worked: {len(filtered_it)} paths with length ≤ 2")


if __name__ == "__main__":
    stops, segments = load_sample_data()
    adj = test_adj_list(segments)
    
    test_basic_routes(adj, stops)
    test_same_origin_dest(adj)
    test_nonexistent_stops(adj)
    test_leaf_node_as_start(adj)
    test_max_path_length(adj)
    test_disconnected_stops(adj)
    test_mutable_default_bug()
    test_max_path_length_filter_correctness()
    test_all_pairs_exhaustive(adj, stops)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
