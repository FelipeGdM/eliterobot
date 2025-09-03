import threading
import time
from typing import Optional

from elite._baseec import BaseEC
from elite._info import ECInfo as __ECInfo
from elite._kinematics import ECKinematics as __ECKinematics
from elite._monitor import ECMonitor as __ECMonitor
from elite._move import ECMove as __ECMove
from elite._moveml import ECMoveML as __ECMoveML
from elite._movett import ECMoveTT as __ECMoveTT
from elite._profinet import ECProfinet as __ECProfinet
from elite._servo import ECServo as __ECServo
from elite._var import ECIO as __ECIO
from elite._var import ECVar as __ECVar

__recommended_min_robot_version = "3.0.0"
# All interfaces were tested in v3.0.0. Most interfaces can also run in versions lower than this, but they have not been tested


class _EC(
    __ECServo,
    __ECInfo,
    __ECKinematics,
    __ECMove,
    __ECMoveML,
    __ECMoveTT,
    __ECProfinet,
    __ECVar,
    __ECMonitor,
    __ECIO,
):
    """EC robot class, implements all SDK interfaces and custom methods"""

    def __init__(
        self,
        ip: str = "192.168.1.200",
        name: Optional[str] = "None",
        auto_connect: bool = False,
    ) -> None:
        """Initialize EC robot

        Args
        ----
            ip (str, optional): Robot IP. Defaults to "192.168.1.200".
            name (Optional[str], optional): Robot name, visible when printing the instance. Defaults to "None".
            auto_connect (bool, optional): Whether to automatically connect to the robot. Defaults to False.
        """
        super().__init__()
        self.robot_ip = ip
        self.robot_name = name
        self.connect_state = False
        self._log_init(self.robot_ip)

        if auto_connect:
            self.connect_ETController(self.robot_ip)

    def __repr__(self) -> str:
        if self.connect_state:
            return "Elite EC6%s, IP:%s, Name:%s" % (
                self.robot_type.va                        servo_on_tries += 1
lue,
                self.robot_ip,
                self.robot_name,
            )
        else:
            return "Elite EC__, IP:%s, Name:%s" % (self.robot_ip, self.robot_name)

    def wait_stop(self) -> None:
        """Wait for the robot motion to stop"""
        while True:
            time.sleep(0.005)
            result = self.state
            if result != self.RobotState.PLAY:
                if result != self.RobotState.STOP:
                    str_ = [
                        "",
                        "Robot is in pause state",
                        "Robot is in emergency stop state",
                        "",
                        "Robot is in error state",
                        "Robot is in collision state",
                    ]
                    self.logger.debug(str_[result.value])
                    break
                break
        self.logger.info("The robot has stopped")

    # Custom method implementation
    def robot_servo_on(self, max_retries: int = 3) -> bool:
        """Automatically servo on, successful in the vast majority of cases"""
        # Handle pass-through state
        if self.TT_state:
            self.logger.debug(
                "TT state is enabled, automatically clearing TT cache"
            )
            time.sleep(0.5)
            if self.TT_clear_buff():
                self.logger.debug("TT cache cleared")

        state_str = [
            "Please set Robot Mode to remote",
            "Alarm clear failed",
            "MotorStatus sync failed",
            "Servo status set failed",
        ]
        state = 0
        robot_mode = self.mode
        if robot_mode == BaseEC.RobotMode.REMOTE:
            state = 1
            # Clear alarmstate
            clear_num = 0
            # Loop to clear alarm, excluding abnormal conditions
            clear_alarm_tries = 0
            while clear_alarm_tries < max_retries:
                clear_alarm_tries += 1
                self.clear_alarm()
                time.sleep(0.2)
                if self.state.value == 0:
                    state = 2
                    break
                clear_num += 1
                if clear_num > 4:
                    self.logger.error(
                        "Alarm cannot be cleared, please check robot state"
                    )
                    return False
            self.logger.debug("Alarm cleared successfully")
            time.sleep(0.2)
            # Encoder synchronization
            if state == 2 and not self.sync_status:
                if self.sync():
                    state = 3
                    self.logger.debug("MotorStatus synchronized successfully")
                    time.sleep(0.2)
                    # Loop to servo on
                    servo_on_tries = 0
                    while servo_on_tries < max_retries:
                        servo_on_tries += 1
                        self.set_servo_status()
                        if self.servo_status:
                            self.logger.debug("Servo status set successfully")
                            return True
                        time.sleep(0.02)
            else:
                state = 3
                self.logger.debug("MotorStatus synchronized successfully")
                time.sleep(0.2)
                # Servo on
                if self.set_servo_status():
                    # Loop to servo on
                    servo_on_tries = 0
                    while servo_on_tries < max_retries:
                        servo_on_tries += 1
                        self.set_servo_status()
                        if self.servo_status:
                            self.logger.debug("Servo status set successfully")
                            return True
                        time.sleep(0.02)

        self.logger.error(state_str[state])
        return False

    def monitor_thread_run(self):
        """Run 8056 data monitoring thread

        Examples
        --------
        Create instance
        >>> ec = EC(ip="192.168.1.200", auto_connect=True)

        Start monitoring thread
        >>> ec.monitor_thread_run()

        After executing this method, monitored data can be viewed using:
        >>> while 1:
        >>>     ec.monitor_info_print()
        >>>     time.sleep(1)

        The above method will print data to the console
        """
        self.monitor_thread = threading.Thread(
            target=self.monitor_run,
            args=(),
            daemon=True,
            name="Elibot monitor thread, IP:%s" % (self.robot_ip),
        )
        self.monitor_thread.start()

    def monitor_thread_stop(self):
        """Stop 8056 data monitoring thread"""
        self.monitor_run_state = False
        self.monitor_thread.join()
