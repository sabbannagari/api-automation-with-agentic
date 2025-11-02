#!/usr/bin/env python3
import subprocess
import sys

test_types = ['system', 'component', 'regression', 'sanity']

print("=" * 80)
print("🚀 Running tests for all test types")
print("=" * 80)

for test_type in test_types:
    print(f"\n{'=' * 80}")
    print(f"📊 Running {test_type.upper()} tests...")
    print("=" * 80)
    
    result = subprocess.run(
        ['python', 'master.py', '--task', f'execute {test_type} tests'],
        capture_output=False
    )
    
    if result.returncode == 0:
        print(f"✅ {test_type.upper()} tests completed")
    else:
        print(f"❌ {test_type.upper()} tests failed")

print("\n" + "=" * 80)
print("✅ All test types executed!")
print("=" * 80)
