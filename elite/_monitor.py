"""
Author: ZhangJunJie
CreateDate:
LastEditTime: 2022-05-16 19:50:18
Description:
"""

import collections
import os
import platform
import socket
import struct
import threading
import time


class ECMonitorInfo:
    """EC series robot 8056 data structure"""

    # Ordered dictionary structure, dictionaries in Python 3 are ordered by default
    _ec_struct = collections.OrderedDict()
    _ec_struct["MessageSize"] = "I"
    _ec_struct["TimeStamp"] = "Q"
    _ec_struct["autorun_cycleMode"] = "B"
    _ec_struct["machinePos"] = "d" * 8
    _ec_struct["machinePose"] = "d" * 6
    _ec_struct["machineUserPose"] = "d" * 6
    _ec_struct["torque"] = "d" * 8
    _ec_struct["robotState"] = "i"
    _ec_struct["servoReady"] = "i"
    _ec_struct["can_motor_run"] = "i"
    _ec_struct["motor_speed"] = "i" * 8
    _ec_struct["robotMode"] = "i"
    _ec_struct["analog_ioInput"] = "d" * 3
    _ec_struct["analog_ioOutput"] = "d" * 5
    _ec_struct["digital_ioInput"] = "Q"
    _ec_struct["digital_ioOutput"] = "Q"
    _ec_struct["collision"] = "B"
    _ec_struct["machineFlangePose"] = "d" * 6
    _ec_struct["machineUserFlangePose"] = "d" * 6
    _ec_struct["emergencyStopState"] = "B"
    _ec_struct["tcp_speed"] = "d"
    _ec_struct["joint_speed"] = "d" * 8
    _ec_struct["tcpacc"] = "d"
    _ec_struct["jointacc"] = "d" * 8

    def __init__(self) -> None:
        self.MessageSize = None
        self.TimeStamp = None
        self.autorun_cycleMode = None
        self.machinePos = [None] * 8
        self.machinePose = [None] * 6
        self.machineUserPose = [None] * 6
        self.torque = [None] * 6
        self.robotState = None
        self.servoReady = None
        self.can_motor_run = None
        self.motor_speed = [None] * 8
        self.robotMode = None
        self.analog_ioInput = [None] * 3
        self.analog_ioOutput = [None] * 5
        self.digital_ioInput = None
        self.digital_ioOutput = None
        self.collision = None
        self.machineFlangePose = [None] * 8
        self.machineUserFlangePose = [None] * 6
        self.emergencyStopState = None
        self.tcp_speed = None
        self.joint_speed = [None] * 8
        self.tcpacc = [None] * 6
        self.jointacc = [None] * 8


class ECMonitor:
    """EC series robot 8056 monitoring class implementation"""

    __SEND_FREQ = 8  # 8ms
    _FMT_MSG_SIZE = "I"  # Default byte for data length information

    _PORT = 8056

    def __init__(self) -> None:
        # self.robot_ip = ip
        self.monitor_info = ECMonitorInfo()
        self._monitor_recv_flag = False  # Whether data reception has started
        self._monitor_lock = threading.Lock()

    def __first_connect(self) -> None:
        """Initial connection, receive and parse the 8056 data packet length for the current version"""
        # Get the data length information for the current ECMonitorInfo version
        self.__current_msg_size_get()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.robot_ip, self._PORT))
            byte_msg_size = sock.recv(struct.calcsize(self._FMT_MSG_SIZE))
            sock.shutdown(2)
            sock.close()
            self.MSG_SIZE = struct.unpack("!" + self._FMT_MSG_SIZE, byte_msg_size)[
                0
            ]  # Actual robot byte length
            # Parse the usable byte length
            self.__msg_size_judgment()
        except socket.timeout as e:
            print(f"Connect IP : {self.robot_ip} Port : {self._PORT} timeout")
            sock.shutdown(2)
            sock.close()

    def __current_msg_size_get(self) -> None:
        """Get all data length information for the current version"""
        temp = 0
        for i in ECMonitorInfo._ec_struct.values():
            temp += struct.calcsize(i)

        self.version_msg_size = int(temp)  # Total length for the ECMonitorInfo version

    def __msg_size_judgment(self):
        """Judge data length"""
        if self.version_msg_size > self.MSG_SIZE:
            self.unpack_size = self.MSG_SIZE
        elif self.version_msg_size < self.MSG_SIZE:
            self.unpack_size = self.version_msg_size  # Determine usable byte length based on current version and actual robot transmission

    def __socket_create(self):
        """Create socket connection"""
        self.sock_monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_monitor.connect((self.robot_ip, self._PORT))

    def monitor_run(self):
        """Monitoring program run"""
        self.monitor_run_state = True
        self.__first_connect()
        self.__socket_create()
        # ? Test
        self._tt = 0  # Total number of data receptions
        self.__br = 0  # Reconnection count
        # ? Test

        while 1:
            self._monitor_lock.acquire()

            buffer = None
            buffer = self.sock_monitor.recv(self.MSG_SIZE, socket.MSG_WAITALL)
            self._monitor_recv_flag = True
            self._recv_buf_size = len(buffer)
            self._tt += 1

            current_unpack_size = 0
            for k, v in ECMonitorInfo._ec_struct.items():
                if current_unpack_size >= self.unpack_size:
                    break

                # Calculate parsed length, byte split
                fmt_size = struct.calcsize(v)
                current_unpack_size += fmt_size
                buff, buffer = buffer[:fmt_size], buffer[fmt_size:]
                # Unpack
                value = struct.unpack("!" + v, buff)

                # Re-establish connection if header is abnormal
                if k == "MessageSize" and value[0] != self.MSG_SIZE:
                    self.sock_monitor.close()
                    self.__socket_create()
                    self._monitor_recv_flag = False
                    # ? Test
                    self.__br += 1
                    # ? Test
                    break

                if len(v) > 1:
                    setattr(self.monitor_info, k, [value[i] for i in range(len(v))])
                else:
                    setattr(self.monitor_info, k, value[0])

            self._monitor_lock.release()
            # self.robot_info_print(is_clear_screen=True)
            if self.monitor_run_state == False:
                self.sock_monitor.close()
                break

    def monitor_info_print(self, t: float = 0.5, is_clear_screen: bool = False):
        """Continuously display current robot information

        Args
        ----
            t (float,optional): Time interval between two data refreshes (i.e., time for one data display)
            is_clear_screen (bool, optional): Whether to auto-clear screen. Defaults to False.
        """

        def spilt_line():
            print("————————————————————————————————————————————————————————" * 2)

        def cls_screen():
            sys_p = platform.system()
            if sys_p == "Windows":
                os.system("cls")
            elif sys_p == "Linux":
                os.system("clear")

        if self._monitor_recv_flag:
            print(
                f"Robot IP: {self.robot_ip} | Current Version Bytes size: {self.unpack_size} | Current Recv Buffer Size: {self._recv_buf_size} | TT: {self._tt} | BR: {self.__br}"
            )
            spilt_line()

            for k, v in vars(self.monitor_info).items():
                # Data requiring additional processing
                if k == "TimeStamp":
                    v = time.gmtime(v // 1000)
                    v = time.strftime("%Y-%m-%d %H:%M:%S", v)
                elif k == "digital_ioInput":
                    v = bin(v)[2:].zfill(64)
                elif k == "digital_ioOutput":
                    v = bin(v)[2:].zfill(64)

                print(f"| {k}: {v}")
                spilt_line()

            # Clear screen
            time.sleep(t)
            if is_clear_screen:
                cls_screen()


if __name__ == "__main__":
    import threading

    # ec = ECMonitor("192.168.1.200")
    ec = ECMonitor("172.16.11.251")

    thread_ec = threading.Thread(target=ec.monitor_run, args=(), daemon=True)
    thread_ec.start()
    time.sleep(1)
    print("---")
    while 1:
        ec.monitor_info_print()
