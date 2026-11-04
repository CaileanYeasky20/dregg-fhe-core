# Reviewer's Quickstart: dregg-fhe-core

This repository is built for formal verification and rigorous, independent critique. We separate **witness generation** (untrusted, high-throughput code) from **verification** (mathematical authority).

## Quick Verification Guide

### 1. Check the Python Reference Suite
Requires standard library only (no external dependencies):
```bash
python3 ref/gen_vectors.py
python3 ref/test_m31ref.py
