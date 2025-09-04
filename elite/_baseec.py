"""
Author: Elite_zhangjunjie
CreateDate:
LastEditors: Elite_zhangjunjie
LastEditTime: 2022-09-07 16:47:46
Description:
"""

import json
import socket
import sys
import threading
import time
from enum import IntEnum
from typing import Optional

from loguru._logger import Core, Logger

from elite.types import CmdResponse


class BaseEC:
    _communicate_lock = threading.Lock()

    send_recv_info_print = False

    def _log_init(self, ip):
        def _filter(record):
            """Filter display based on log_name when multiple stderr outputs exist"""
            return record["extra"].get("ip") == ip

        # * ------
        self.logger = Logger(
            core=Core(),
            exception=None,
            depth=0,
            record=False,
            lazy=False,
            colors=False,
            raw=False,
            capture=True,
            patcher=None,
            extra={"ip": ip},
        )

        # * ------
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> |<yellow>Robot_IP: "
            + ip
            + "</yellow>| <level>"
            + "{level:<8}".ljust(7)
            + " | {message}</level>"
        )
        self.logger.add(sys.stderr, format=format_str, filter=_filter, colorize=True)

        _logger_add = self.logger.add

        def _add(*args, **kwargs):
            if "format" not in kwargs:
                kwargs["format"] = format_str
            if "filter" not in kwargs:
                kwargs["filter"] = _filter
            _logger_add(*args, **kwargs)

        self.logger.add = _add

    def us_sleep(self, t):
        """Microsecond-level delay (theoretically achievable)
        Unit: μs
        """
        start, end = 0, 0
        start = time.time()
        t = (t - 500) / 1000000  # \\500 accounts for operational and computational error
        while end - start < t:
            end = time.time()

    def _set_sock_sendBuf(self, send_buf: int, is_print: bool = False):
        """Set socket send buffer size

        Args
        ----
            send_buf (int): Buffer size to set
            is_print (bool, optional): Whether to print data. Defaults to False.
        """

        if self.sock_cmd is None:
            self.logger.error("Socket invalid, connection is broken")
            return

        if is_print:
            before_send_buff = self.sock_cmd.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            self.logger.info(f"before_send_buff: {before_send_buff}")
            self.sock_cmd.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buf)
            time.sleep(1)
            after_send_buff = self.sock_cmd.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            self.logger.info(f"after_send_buff: {after_send_buff}")
            time.sleep(1)
        else:
            self.sock_cmd.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buf)

    def connect_ETController(self, ip: str, port: int = 8055, timeout: float = 2) -> tuple:
        """Connect to EC series robot port 8055

        Args:
            ip (str): Robot IP
            port (int, optional): SDK port number. Defaults to 8055.
            timeout (float, optional): TCP communication timeout. Defaults to 2.

        Returns
        -------
            [tuple]: (True/False, socket/None), returned socket is globally defined in this module
        """
        self.sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # -------------------------------------------------------------------------------
        # Set nodelay
        # self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)   # Set nodelay
        # self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        # sock.settimeout(timeout)
        # -------------------------------------------------------------------------------

        try:
            self.sock_cmd.settimeout(5)
            self.sock_cmd.connect((ip, port))
            self.logger.debug(ip + " connect success")
            self.connect_state = True
            return (True, self.sock_cmd)
        except Exception:
            self.sock_cmd.close()
            self.logger.critical(ip + " connect fail")
            quit()
            return (False, None)

    def disconnect_ETController(self) -> None:
        """Disconnect EC robot port 8055"""
        if self.sock_cmd:
            self.sock_cmd.close()
            self.sock_cmd = None
        else:
            self.sock_cmd = None
            self.logger.critical("socket already closed")

    def send_CMD(
        self, cmd: str, params: Optional[dict] = None, id: int = 1, ret_flag: bool = True
    ) -> CmdResponse:
        """Send specified command to port 8055

        Args
        ----
            cmd (str): Command
            params (Dict[str,Any], optional): Parameters. Defaults to None.
            id (int, optional): ID number. Defaults to 1.
            ret_flag (bool, optional): Whether to receive data after sending. Defaults to True.

        Returns
        -------
            Any: Corresponding command return information or error message
        """

        if self.sock_cmd is None:
            self.logger.error("Socket invalid, connection is broken")
            return CmdResponse(False, "", "")

        parsed_params = params if params else {}
        sendStr = json.dumps({"jsonrpc": "2.0", "method": cmd, "params": parsed_params, "id": id})

        if self.send_recv_info_print:  # print send msg
            self.logger.info(f"Send: Func is {cmd}")
            self.logger.info(sendStr)

        try:
            with BaseEC._communicate_lock:
                self.sock_cmd.sendall(bytes(sendStr, "utf-8"))

                if not ret_flag:
                    return CmdResponse(True, "", "")

                ret = self.sock_cmd.recv(1024)
                jdata = json.loads(str(ret, "utf-8"))

                if self.send_recv_info_print:  # print recv nsg
                    self.logger.info(f"Recv: Func is {cmd}")
                    self.logger.info(str(ret, "utf-8"))

                if "result" in jdata:
                    if jdata["id"] != id:
                        self.logger.warning(
                            "id match fail,send_id={0},recv_id={0}", id, jdata["id"]
                        )
                    return CmdResponse(True, json.loads(jdata["result"]), jdata["id"])

                if "error" in jdata:
                    self.logger.warning(f"CMD: {cmd} | {jdata['error']['message']}")
                    return CmdResponse(False, jdata["error"]["message"], jdata["id"])

                self.logger.error("Received package didn't match any known structure")
                return CmdResponse(False, "", "")

        except Exception as e:
            self.logger.error(f"CMD: {cmd} |Exception: {e}")
            quit()
            return (False, None, None)

    class Frame(IntEnum):
        """Coordinate system (used for specifying coordinate system during jogging, etc.)"""

        JOINT_FRAME = 0  # Joint coordinate system
        BASE_FRAME = 1  # Cartesian/World coordinate system
        TOOL_FRAME = 2  # Tool coordinate system
        USER_FRAME = 3  # User coordinate system
        CYLINDER_FRAME = 4  # Cylindrical coordinate system

    class ToolNumber(IntEnum):
        """Tool coordinate system (used for setting/viewing tool coordinate system data)"""

        TOOL0 = 0  # Tool 0
        TOOL1 = 1  # Tool 1
        TOOL2 = 2  # Tool 2
        TOOL3 = 3  # Tool 3
        TOOL4 = 4  # Tool 4
        TOOL5 = 5  # Tool 5
        TOOL6 = 6  # Tool 6
        TOOL7 = 7  # Tool 7

    class UserFrameNumber(IntEnum):
        """User coordinate system (used for setting/viewing user coordinate system data)"""

        USER0 = 0  # User 0
        USER1 = 1  # User 1
        USER2 = 2  # User 2
        USER3 = 3  # User 3
        USER4 = 4  # User 4
        USER5 = 5  # User 5
        USER6 = 6  # User 6
        USER7 = 7  # User 7

    class AngleType(IntEnum):
        """Pose unit (used for setting/returning pose data units)"""

        DEG = 0  # Degrees
        RAD = 1  # Radians

    class CycleMode(IntEnum):
        """Cycle mode (used for querying/setting current cycle mode)"""

        STEP = 0  # Single step
        CYCLE = 1  # Single cycle
        CONTINUOUS_CYCLE = 2  # Continuous cycle

    class RobotType(IntEnum):
        """Robot subtype"""

        EC63 = 3  # EC63
        EC66 = 6  # EC66
        EC612 = 12  # EC612

    class ToolBtn(IntEnum):
        """End-effector button"""

        BLUE_BTN = 0  # End blue button
        GREEN_BTN = 1  # End green button

    class ToolBtnFunc(IntEnum):
        """End-effector button function"""

        DISABLED = 0  # Disabled
        DRAG = 1  # Drag
        RECORD_POINT = 2  # Drag recording point

    class JbiRunState(IntEnum):
        """JBI run state"""

        STOP = 0  # JBI run stopped
        PAUSE = 1  # JBI run paused
        ESTOP = 2  # JBI emergency stop
        RUN = 3  # JBI running
        ERROR = 4  # JBI run error
        DEC_TO_STOP = 5  # JBI decelerating to stop
        DEC_TO_PAUSE = 6  # JBI decelerating to pause

    class MlPushResult(IntEnum):
        """ML point push result"""

        CORRECT = 0  # Correct
        WRONG_LENGTH = -1  # Length error
        WRONG_FORMAT = -2  # Format error
        TIMESTAMP_IS_NOT_STANDARD = -3  # Timestamp not standard

    class RobotMode(IntEnum):
        """Robot mode"""

        TECH = 0  # Teach mode
        PLAY = 1  # Run mode
        REMOTE = 2  # Remote mode

    class RobotState(IntEnum):
        """Robot state"""

        STOP = 0  # Stopped
        PAUSE = 1  # Paused
        ESTOP = 2  # Emergency stop
        PLAY = 3  # Running
        ERROR = 4  # Error
        COLLISION = 5  # Collision
