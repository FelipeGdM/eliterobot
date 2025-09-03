"""
Author: Elite_zhangjunjie
CreateDate:
LastEditors: Elite_zhangjunjie
LastEditTime: 2022-05-22 16:34:53
Description: Servo-related class
"""

import time
from enum import Enum

from elite._baseec import BaseEC


class ECServo(BaseEC):
    """EC servo-related class, servo class is related to the robot's motion state, mode, servo on/off operations, etc."""

    # Servo service
    @property
    def mode(self) -> BaseEC.RobotMode:
        """Get the robot's mode

        Returns
        -------
            RobotMode: 0 Teach, 1 Run, 2 Remote

        Examples
        --------
        >>> from elite import EC
        >>> ec = EC(ip="192.168.1.200", auto_connect=True)
        >>> print(ec.mode)  # => RobotMode.TECH
        """
        return self.RobotMode(self.send_CMD("getRobotMode"))

    @property
    def state(self) -> BaseEC.RobotState:
        """Get the robot's running state
            #!The emergency stop state obtained by this command will only exist briefly and will soon be overwritten by alarms. If you need to get the emergency stop status, please use robot_get_estop_status()

        Returns
        -------
            RobotState: 0 Stop, 1 Pause, 2 Emergency stop, 3 Run, 4 Error, 5 Collision

        Examples
        --------
        >>> from elite import EC
        >>> ec = EC(ip="192.168.1.200", auto_connect=True)
        >>> print(ec.state)  # => RobotState.STOP
        """
        return self.RobotState(self.send_CMD("getRobotState"))

    @property
    def estop_status(self) -> int:
        """Get the robot's emergency stop status (hardware status)

        Returns
        -------
            int: 0: Not emergency stop, 1: Emergency stop
        """
        return self.send_CMD("get_estop_status")

    @property
    def servo_status(self) -> bool:
        """Get servo status

        Returns
        -------
            bool: True Enabled, False Disabled
        """
        return self.send_CMD("getServoStatus")

    def set_servo_status(self, _status: int = 1) -> bool:
        """Set robot servo status

        Args
        ----
            status (int, optional): 1 Servo on, 0 Servo off. Defaults to 1.

        Returns
        -------
            bool: True Operation successful, False Operation failed
        """
        return self.send_CMD("set_servo_status", {"status": _status})

    def sync(self) -> bool:
        """Encoder synchronization

        Returns
        -------
            bool: True Operation successful, False Operation failed
        """
        return self.send_CMD("syncMotorStatus")

    @property
    def sync_status(self) -> bool:
        """Get synchronization status

        Returns
        -------
            bool: True Synchronized, False Not synchronized
        """
        return self.send_CMD("getMotorStatus")

    def clear_alarm(self) -> bool:
        """Clear alarm

        Returns
        -------
            bool: True Operation successful, False Operation failed
        """
        return self.send_CMD("clearAlarm")

    def calibrate_encoder_zero(self) -> bool:
        """Encoder zero calibration, returns True if calibration is possible regardless of calibration result, returns False if calibration is not possible

        Returns
        -------
            bool: Can calibrate True, Cannot calibrate False
        """
        return self.send_CMD("calibrate_encoder_zero_position")
