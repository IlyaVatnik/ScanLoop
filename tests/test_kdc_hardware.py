import time
import os
from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube

def test_hardware():
    serial = "27254353"
    print(f"Connecting to Thorlabs Cube {serial}...")
    stage = ThorlabsCube(serial_no=serial, max_velocity_mm_s=1.2, acceleration_mm_s2=1.5)
    try:
        # Check velocity & acceleration readback
        vel_params = stage.get_velocity()
        print(f"Initial get_velocity(): {vel_params}")
        assert abs(vel_params["max_velocity"] - 1.2) < 0.05, f"Vel mismatch: {vel_params}"
        assert abs(vel_params["acceleration"] - 1.5) < 0.05, f"Acc mismatch: {vel_params}"

        # Test setting new velocity & acceleration
        print("Setting velocity=2.0, acceleration=2.5...")
        stage.set_velocity(max_velocity_mm_s=2.0, acceleration_mm_s2=2.5)
        vel_params2 = stage.get_velocity()
        print(f"Updated get_velocity(): {vel_params2}")
        assert abs(vel_params2["max_velocity"] - 2.0) < 0.05
        assert abs(vel_params2["acceleration"] - 2.5) < 0.05

        # Restore original
        stage.set_velocity(max_velocity_mm_s=1.2, acceleration_mm_s2=1.5)

        # Check position in steps and micrometers
        steps = stage.get_position_steps()
        pos_um = stage.get_position()
        min_step = stage.get_min_step()
        print(f"Position steps: {steps} (type: {type(steps).__name__})")
        print(f"Position um: {pos_um:.6f} um")
        print(f"Min step: {min_step:.6f} um")
        assert isinstance(steps, int)
        assert abs(pos_um - steps * min_step) < 1e-6

        print("SUCCESS: Hardware ThorlabsCube verification passed cleanly!")
    finally:
        stage.close()
        print("Disconnected.")

if __name__ == "__main__":
    test_hardware()
