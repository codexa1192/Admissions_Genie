#!/usr/bin/env python3
"""
Test script for virus scanner functionality.
Tests ClamAV integration and file scanning capabilities.
"""

import os
import sys
from utils.virus_scanner import get_virus_scanner

def test_scanner_availability():
    """Test if ClamAV is available and working."""
    print("="*70)
    print("Testing Virus Scanner Availability")
    print("="*70)

    scanner = get_virus_scanner()

    if scanner.is_available():
        print("✅ ClamAV is available and running")
        version = scanner.get_version()
        print(f"✅ ClamAV version: {version}")
        return True
    else:
        print("❌ ClamAV is NOT available")
        print("\n📝 To install ClamAV:")
        print("  # macOS")
        print("  brew install clamav")
        print("  brew services start clamav")
        print("\n  # Ubuntu/Debian")
        print("  sudo apt-get install clamav clamav-daemon")
        print("  sudo systemctl start clamav-daemon")
        print("\n  # Install Python package")
        print("  pip install python-clamd")
        return False

def test_clean_file():
    """Test scanning a clean file."""
    print("\n" + "="*70)
    print("Testing Clean File Scan")
    print("="*70)

    # Create a clean test file
    test_file = '/tmp/clean_test_file.txt'
    with open(test_file, 'w') as f:
        f.write("This is a clean test file with no viruses.\n")
        f.write("Just some normal text content.\n")

    scanner = get_virus_scanner()
    is_clean, threat_name = scanner.scan_file(test_file)

    # Clean up
    os.remove(test_file)

    if is_clean:
        print(f"✅ Clean file passed: {test_file}")
        print(f"✅ Threat name: {threat_name} (should be None)")
        return True
    else:
        print(f"❌ Clean file rejected: {test_file}")
        print(f"❌ False positive threat: {threat_name}")
        return False

def test_eicar_file():
    """Test scanning EICAR test virus file."""
    print("\n" + "="*70)
    print("Testing EICAR Virus Detection")
    print("="*70)
    print("Note: EICAR is a harmless test virus for antivirus testing")
    print("See: https://www.eicar.org/download-anti-malware-testfile/")

    # EICAR test virus string (harmless test file recognized by all AV software)
    eicar_string = r'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'

    # Create EICAR test file
    test_file = '/tmp/eicar_test.txt'
    with open(test_file, 'w') as f:
        f.write(eicar_string)

    scanner = get_virus_scanner()
    is_clean, threat_name = scanner.scan_file(test_file)

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

    if not is_clean:
        print(f"✅ EICAR virus detected correctly!")
        print(f"✅ Threat identified as: {threat_name}")
        return True
    else:
        print(f"❌ EICAR virus NOT detected - scanner may not be working")
        print(f"❌ File was marked as clean (should be infected)")
        return False

def test_memory_scan():
    """Test scanning bytes in memory."""
    print("\n" + "="*70)
    print("Testing In-Memory Scan")
    print("="*70)

    # Test clean data
    clean_data = b"This is clean data in memory"

    scanner = get_virus_scanner()
    is_clean, threat_name = scanner.scan_bytes(clean_data)

    if is_clean:
        print(f"✅ Clean bytes passed: {len(clean_data)} bytes")
        print(f"✅ Threat name: {threat_name} (should be None)")
        return True
    else:
        print(f"❌ Clean bytes rejected")
        print(f"❌ False positive threat: {threat_name}")
        return False

def main():
    """Run all virus scanner tests."""
    print("\n" + "="*70)
    print("🦠 VIRUS SCANNER TEST SUITE")
    print("="*70)
    print("Testing ClamAV integration for HIPAA compliance")
    print("HIPAA §164.308(a)(5)(ii)(B) - Protection from Malicious Software")
    print("="*70 + "\n")

    results = []

    # Test 1: Scanner availability
    results.append(("Scanner Availability", test_scanner_availability()))

    # Only run other tests if scanner is available
    if results[0][1]:
        results.append(("Clean File Scan", test_clean_file()))
        results.append(("EICAR Virus Detection", test_eicar_file()))
        results.append(("In-Memory Scan", test_memory_scan()))
    else:
        print("\n⚠️  Skipping remaining tests - ClamAV not available")

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("="*70)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")

    if failed == 0 and passed > 0:
        print("✅ ALL TESTS PASSED - Virus scanning is working correctly!")
    elif failed == 1 and results[0][1] == False:
        print("⚠️  ClamAV not installed - Install ClamAV to enable virus scanning")
    else:
        print("❌ SOME TESTS FAILED - Please check ClamAV configuration")

    print("="*70 + "\n")

    # Exit code
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
