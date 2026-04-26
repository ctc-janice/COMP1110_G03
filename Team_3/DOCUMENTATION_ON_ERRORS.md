# DFS Algorithm - Error Documentation

## Issues in `recursive_journeyGenerator()`

### 1. **Missing Return Statement** ⚠️ CRITICAL
**Problem:** The function doesn't return anything.
```python
def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=[]):
    # ... code ...
    # No return statement!
```

**Impact:** When `tui.py` calls this function, it gets `None` instead of the list of paths, causing "No routes found" errors in the UI.

**Fix:** Add at the end of the function:
```python
def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=[]):
    # ... existing code ...
    return results
```

---

### 2. **Global State Pollution** ⚠️ CRITICAL
**Problem:** `results` and `visited` are defined at module level and never reset.
```python
results = []        # Global variable
visited = set()     # Global variable

def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=[]):
    # Uses global variables
```

**Impact:** 
- Calling the function twice accumulates results from both searches
- Second search carries over visited nodes from first search
- Results become corrupted and incorrect

**Example:**
```
Search 1: Find paths A→B (gets 3 paths, stored in results)
Search 2: Find paths C→D (adds to results, now has 3+new paths instead of just new ones)
```

**Fix:** Move `results` and `visited` inside the function as local variables that reset each call.

---

### 3. **Mutable Default Argument** ⚠️ MAJOR
**Problem:** `journey=[]` is a Python anti-pattern.
```python
def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=[]):
    #                                                              ^^^^^^
    #                                                    Mutable default!
```

**Impact:** The same empty list object is reused across all function calls, causing state to leak between different invocations.

**Fix:** Remove the default value or pass an empty list explicitly:
```python
def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=None):
    if journey is None:
        journey = []
```

---

### 4. **Improper Journey Copying**
**Problem:** `results.append(journey)` appends a reference to the list, not a copy.
```python
if currentpoint == endpoint:
    results.append(journey)  # Appends reference, not a copy
```

**Impact:** All stored journeys point to the same list object. Later modifications corrupt previous results.

**Fix:** Append a copy instead:
```python
if currentpoint == endpoint:
    results.append(journey[:])  # Append a copy, not reference
```

---

## Summary Table

| Error | Severity | Impact | Fix |
|-------|----------|--------|-----|
| No return statement | CRITICAL | Function returns `None` | Add `return results` |
| Global state pollution | CRITICAL | Results corrupted on multiple calls | Move to local variables |
| Mutable default argument | MAJOR | State leaks between calls | Remove default or use `None` |
| Reference append | MAJOR | List corruption | Use `journey[:]` |

---

## Testing Recommendation

After fixes, test with:
1. Single search (A→B)
2. Two consecutive searches (A→B, then C→D)
3. Verify both searches return correct paths independently
