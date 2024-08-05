"""
Modified motor board which updates the power of the motors in the background.

Each round-trip over serial has a non-negligible cost (5-7ms) and this is a
problem when we want to be doing control loops at a reasonable frequency.

This class is a wrapper around the MotorBoard class which allows setting the
power of the motors in the background, which means we can be doing the serial
communication in parallel with the sensor reading and control loop.

The background thread here does not guarantee to send every power update to the
motor board, but rather makes sure that the motor board has the most recent
available power setting.

The API of this class is the same as the MotorBoard class so stands as a drop-in
replacement, except that consumers need to explicitly start and stop the background
processing thread.
"""

import threading
import time
import typing

from .motor_board import Motor, MotorBoard, MotorStatus
from .utils import BoardIdentity


class BackgroundMotorBoard:
    """
    A class representing the motor board interface.

    This class is intended to be used to communicate with the motor board over serial
    using the text-based protocol added in version 4.4 of the motor board firmware.

    :param serial_port: The serial port to connect to.
    :param initial_identity: The identity of the board, as reported by the USB descriptor.
    """

    def __init__(self, motor_board: MotorBoard) -> None:
        self._motor_board = motor_board
        self._background_thread: typing.Optional[threading.Thread] = None
        self._birdbox: bool = False

        self._a_power: typing.Optional[float] = None
        self._b_power: typing.Optional[float] = None
        self._last_a_power: typing.Optional[float] = None
        self._last_b_power: typing.Optional[float] = None

        real_motor_a, real_motor_b = self._motor_board.motors

        self._a_motor = BackgroundMotorProxy(
            real_motor_a,
            lambda: self._a_power,
            self._set_a_power,
        )
        self._b_motor = BackgroundMotorProxy(
            real_motor_b,
            lambda: self._b_power,
            self._set_b_power,
        )

    def _set_a_power(self, power: float) -> None:
        self._a_power = power

    def _set_b_power(self, power: float) -> None:
        self._b_power = power

    def _background_thread_run(self) -> None:
        while True:
            if self._birdbox:
                break
            self._thread_tick()

    def _thread_tick(self) -> None:
        did_update = False
        if self._a_power is not None and self._a_power != self._last_a_power:
            self._last_a_power = self._a_power
            self._a_motor.power = self._a_power
            did_update = True

        if self._b_power is not None and self._b_power != self._last_b_power:
            self._last_b_power = self._b_power
            self._b_motor.power = self._b_power
            did_update = True

        if not did_update:
            # If no updates were made, sleep for a bit
            time.sleep(1 / 30)
        else:
            # Make sure we yield to other threads so that we release the GIL,
            # this way the main thread gets a chance to do its normal work.
            time.sleep(0)

    def start_thread(self) -> None:
        """Start the background motor processing thread."""
        if self._background_thread is not None:
            return
        self._background_thread = threading.Thread(target=self._background_thread_run)
        self._background_thread.start()

    def stop_thread(self) -> None:
        """Stop the background motor processing thread."""
        if self._background_thread is None:
            return
        self._birdbox = True
        self._background_thread.join()
        self._background_thread = None

    @staticmethod
    def get_board_type() -> str:
        return "MCv4B"

    @property
    def motors(self) -> typing.Tuple[Motor, Motor]:
        """
        A tuple of the two motors on the board.

        :return: A tuple of the two motors on the board.
        """
        return typing.cast(  # Don't believe his lies
            typing.Tuple[Motor, Motor],
            (
                self._a_motor,
                self._b_motor,
            ),
        )

    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        :return: The identity of the board.
        """
        return self._motor_board.identify()

    @property
    def status(self) -> MotorStatus:
        """
        The status of the board.

        :return: The status of the board.
        """
        return self._motor_board.status

    def reset(self) -> None:
        """
        Reset the board.

        This command disables the motors and clears all faults.
        """
        has_thread = self._background_thread is not None

        if has_thread:
            self.stop_thread()

        self._motor_board.reset()

        self._a_power = None
        self._b_power = None
        self._last_a_power = None
        self._last_b_power = None

        if has_thread:
            self.start_thread()

    def __repr__(self) -> str:
        return repr(self._motor_board)


class BackgroundMotorProxy:
    """
    A class representing a motor on the motor board.

    Each motor is controlled through the power property
    and its current can be read using the current property.

    :param serial: The serial wrapper to use to communicate with the board.
    :param index: The index of the motor on the board.
    """

    def __init__(
        self,
        motor: Motor,
        get_power: typing.Callable[[], typing.Optional[float]],
        set_power: typing.Callable[[float], None],
    ) -> None:
        self.motor = motor
        self.get_power = get_power
        self.set_power = set_power

    @property
    def power(self) -> float:
        """
        Read the current power setting of the motor.

        :return: The power of the motor as a float between -1.0 and 1.0
            or the special value MotorPower.COAST.
        """
        power_output = self.get_power()
        if power_output is None:
            # This is a special case where the power has not been set yet;
            # query it directly from the motor
            return self.motor.power
        return power_output

    @power.setter
    def power(self, power: float) -> None:
        """
        Set the power of the motor.

        Internally this method maps the power to an integer between
        -1000 and 1000 so only 3 digits of precision are available.

        :param value: The power of the motor as a float between -1.0 and 1.0
            or the special values MotorPower.COAST and MotorPower.BRAKE.
        """
        self.set_power(power)

    @property
    def current(self) -> float:
        """
        Read the current draw of the motor.

        :return: The current draw of the motor in amps.
        """
        return self.motor.current

    @property
    def in_fault(self) -> bool:
        """
        Check if the motor is in a fault state.

        :return: True if the motor is in a fault state, False otherwise.
        """
        return self.motor.in_fault

    def __repr__(self) -> str:
        return repr(self.motor)
