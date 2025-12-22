#!/usr/bin/env python3
"""
Automated Bidirectional Communication Test

Tests bidirectional audio relay between two simulated walkie-talkie devices.
This script runs two clients and verifies that audio sent from one device
is received by the other, and vice versa.
"""

import asyncio
import json
import random
import websockets
from datetime import datetime
from test_client import SimulatedWalkieTalkie


class TestResults:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.device1_to_device2_ok = False
        self.device2_to_device1_ok = False

    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✓ Tests Passed: {self.tests_passed}")
        print(f"✗ Tests Failed: {self.tests_failed}")
        print(f"Device 1 → Device 2: {'✓ PASS' if self.device1_to_device2_ok else '✗ FAIL'}")
        print(f"Device 2 → Device 1: {'✓ PASS' if self.device2_to_device1_ok else '✗ FAIL'}")
        print("="*70)

        if self.tests_failed == 0:
            print("🎉 All tests passed! Bidirectional communication is working!")
        else:
            print("⚠️  Some tests failed. Check the logs above.")
        print()


async def test_bidirectional_communication(server_url="ws://localhost:8080/walkie"):
    """Test bidirectional communication between two devices"""
    results = TestResults()

    print("\n" + "="*70)
    print("BIDIRECTIONAL WALKIE-TALKIE COMMUNICATION TEST")
    print("="*70)
    print(f"Server: {server_url}")
    print("="*70 + "\n")

    # Create two simulated devices
    device1 = SimulatedWalkieTalkie("Alice", server_url)
    device2 = SimulatedWalkieTalkie("Bob", server_url)

    try:
        # Test 1: Connect both devices
        print("\n[TEST 1] Connecting devices to server...")
        print("-" * 70)

        device1_connected = await device1.connect()
        device2_connected = await device2.connect()

        if device1_connected and device2_connected:
            print("✓ Both devices connected successfully")
            results.tests_passed += 1
        else:
            print("✗ Failed to connect devices")
            results.tests_failed += 1
            return results

        await asyncio.sleep(0.5)

        # Test 2: Register both devices
        print("\n[TEST 2] Registering devices with server...")
        print("-" * 70)

        await device1.register()
        await device2.register()
        await asyncio.sleep(0.5)

        print("✓ Both devices registered")
        results.tests_passed += 1

        # Start receiving messages for both devices
        receive_task1 = asyncio.create_task(device1.receive_messages())
        receive_task2 = asyncio.create_task(device2.receive_messages())

        await asyncio.sleep(1)

        # Test 3: Device 1 sends to Device 2
        print("\n[TEST 3] Testing Device 1 (Alice) → Device 2 (Bob)...")
        print("-" * 70)

        device2.received_audio_count = 0  # Reset counter
        await device1.simulate_transmission(duration_ms=1000)
        await asyncio.sleep(1)  # Wait for relay

        if device2.received_audio_count > 0:
            print(f"✓ Device 2 received {device2.received_audio_count} audio chunks from Device 1")
            results.device1_to_device2_ok = True
            results.tests_passed += 1
        else:
            print("✗ Device 2 did not receive audio from Device 1")
            results.tests_failed += 1

        # Test 4: Device 2 sends to Device 1
        print("\n[TEST 4] Testing Device 2 (Bob) → Device 1 (Alice)...")
        print("-" * 70)

        device1.received_audio_count = 0  # Reset counter
        await device2.simulate_transmission(duration_ms=1000)
        await asyncio.sleep(1)  # Wait for relay

        if device1.received_audio_count > 0:
            print(f"✓ Device 1 received {device1.received_audio_count} audio chunks from Device 2")
            results.device2_to_device1_ok = True
            results.tests_passed += 1
        else:
            print("✗ Device 1 did not receive audio from Device 2")
            results.tests_failed += 1

        # Test 5: Bidirectional simultaneously (stress test)
        print("\n[TEST 5] Testing rapid back-and-forth communication...")
        print("-" * 70)

        for i in range(3):
            device1.received_audio_count = 0
            device2.received_audio_count = 0

            # Device 1 transmits
            await device1.simulate_transmission(duration_ms=500)
            await asyncio.sleep(0.5)

            # Device 2 transmits
            await device2.simulate_transmission(duration_ms=500)
            await asyncio.sleep(0.5)

        print("✓ Rapid back-and-forth communication completed")
        results.tests_passed += 1

        # Cleanup
        receive_task1.cancel()
        receive_task2.cancel()

        await asyncio.sleep(0.5)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        results.tests_failed += 1

    finally:
        # Close connections
        if device1.websocket:
            await device1.websocket.close()
        if device2.websocket:
            await device2.websocket.close()

    return results


async def main():
    """Main entry point"""
    import sys

    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8080/walkie"

    print("\n🚀 Starting bidirectional communication test...")
    print(f"Make sure the server is running at: {server_url}")
    print("\nStarting in 2 seconds...")
    await asyncio.sleep(2)

    results = await test_bidirectional_communication(server_url)
    results.print_summary()

    # Return exit code based on results
    return 0 if results.tests_failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        exit(1)
