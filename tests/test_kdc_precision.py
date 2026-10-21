import pytest
from Hardware.Stages.Thorlabs.thorlabs_stages import KDC_ENCODER_STEP, ThorlabsCube
from Hardware.Stages.stages_manager import Stages


def test_encoder_step_calculation():
    # Z8 physical specs: 512 steps/rev, 67.49016 gearbox ratio, 1.0 mm pitch
    expected_step = 1000.0 / (512.0 * 67.49016)
    assert abs(KDC_ENCODER_STEP - expected_step) < 1e-12
    assert abs(KDC_ENCODER_STEP - 0.028939403847844007) < 1e-9


def test_500_micron_move_steps():
    # Check that 500 microns maps to 17277 integer steps (not 16667)
    target_um = 500.0
    steps = int(round(target_um / KDC_ENCODER_STEP))
    assert steps == 17277

    actual_um = steps * KDC_ENCODER_STEP
    # Error should be less than half a step (0.015 microns)
    assert abs(actual_um - 500.0) < 0.015
    assert abs(actual_um - 499.986) < 0.001


def test_stages_integer_steps_storage():
    stages = Stages()
    assert stages.abs_position_steps == {'X': 0, 'Y': 0, 'Z': 0}
    assert stages.relative_position_steps == {'X': 0, 'Y': 0, 'Z': 0}
    assert stages.zero_position_steps == {'X': 0, 'Y': 0, 'Z': 0}

    # Simulate position steps
    stages.abs_position_steps['X'] = 17277
    stages.abs_position['X'] = 17277 * KDC_ENCODER_STEP

    # Zero position at 500 steps
    stages.zero_position_steps['X'] = 500
    stages.zero_position['X'] = 500 * KDC_ENCODER_STEP
    stages.update_relative_positions()

    assert stages.relative_position_steps['X'] == 16777
    assert isinstance(stages.relative_position_steps['X'], int)
    assert abs(stages.relative_position['X'] - 16777 * KDC_ENCODER_STEP) < 1e-9
