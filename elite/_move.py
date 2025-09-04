"""
Author: Elite_zhangjunjie
CreateDate:
LastEditors: Elite_zhangjunjie
LastEditTime: 2022-11-11 17:25:15
Description: Motion and task execution related
"""

import time
from typing import Optional

from elite.types import CmdResponse

from ._baseec import BaseEC


class ECMove(BaseEC):
    """EC movement related class, all basic movement services are implemented here"""

    def __wait_stop(self) -> None:
        while True:
            time.sleep(0.005)
            result = self.RobotState(self.send_CMD("getRobotState").result)
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

    def stop(self) -> CmdResponse:
        """Stop robot movement

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        return self.send_CMD("stop")

    def run(self) -> CmdResponse:
        """Resume robot automatic operation (used after pause)

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        return self.send_CMD("run")

    def pause(self) -> CmdResponse:
        """Pause robot

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        return self.send_CMD("pause")

    # JBI file processing
    def check_if_jbi_exists(self, file_name: str) -> CmdResponse:
        """Check if JBI file exists

        Args
        ----
            file_name (str): JBI file name

        Returns
        -------
            int: 0: does not exist, 1: exists
        """
        return self.send_CMD("checkJbiExist", {"filename": file_name})

    def run_jbi(self, file_name: str) -> CmdResponse:
        """Run JBI file

        Args
        ----
            file_name (str): File name to run

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        return self.send_CMD("runJbi", {"filename": file_name})

    def get_jbi_state(self, file_name: str) -> BaseEC.JbiRunState:
        """Get JBI file running status

        Args
        ----
            file_name (str): JBI file name

        Returns
        -------
            JbiRunState: 0 stopped, 1 paused, 2 emergency stopped, 3 running, 4 error
        """
        return self.JbiRunState(
            self.send_CMD("getJbiState", {"filename": file_name}).result["runState"]
        )

    # Jog motion
    def jog(self, index: int, speed: Optional[float] = None) -> CmdResponse:
        """Jog motion:
                The robot will not stop immediately after stopping the jog command, need to use stop command to stop
                If no next jog command is received for more than 1s, reception stops and robot jog motion stops
        Args
        ----
            index (int): 0~11 even numbers for negative direction, odd numbers for positive direction
            speed (float, optional): 0.05 ~ 100. Defaults to None.

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        if speed:
            return self.send_CMD("jog", {"index": index, "speed": speed})
        else:
            return self.send_CMD("jog", {"index": index})

    def move_joint(
        self,
        target_joint: list,
        speed: float,
        acc: Optional[int] = None,
        dec: Optional[int] = None,
        cond_type: Optional[int] = None,
        cond_num: Optional[int] = None,
        cond_value: Optional[int] = None,
        cond_judgement: Optional[str] = None,
        block: Optional[bool] = True,
    ) -> CmdResponse:
        """Joint motion, need to check robot motion status to determine if motion is complete after execution

        Args
        ----
            target_joint (list): Target joint data, requires 8 values, 6 will cause error
            speed (float): Joint speed percentage
            acc (int, optional): Acceleration, defaults to 0 if not specified. Defaults to 0.
            dec (int, optional): Deceleration, defaults to 0 if not specified. Defaults to 0.
            cond_type (int, optional): IO type, 0 for input, 1 for output
            cond_num (int, optional): IO address, 0~63
            cond_value (int, optional): IO status, 0/1, when IO status matches, immediately abandon this motion and execute next instruction
            block (bool, optional): True: blocking motion, False: non-blocking motion. Defaults to True.

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        params = {"targetPos": target_joint, "speed": speed}
        if acc is not None:
            params["acc"] = acc
        if dec is not None:
            params["dec"] = dec
        if cond_type is not None:
            params["cond_type"] = cond_type
        if cond_num is not None:
            params["cond_num"] = cond_num
        if cond_value is not None:
            params["cond_value"] = cond_value
        if cond_judgement is not None:
            params["cond_judgement"] = cond_judgement
        if block:
            move_ret = self.send_CMD("moveByJoint", params)
            if move_ret.success:
                self.__wait_stop()
            return move_ret
        else:
            return self.send_CMD("moveByJoint", params)

    def move_line(
        self,
        target_joint: list,
        speed: int,
        speed_type: Optional[int] = None,
        acc: Optional[int] = None,
        dec: Optional[int] = None,
        cond_type: Optional[int] = None,
        cond_num: Optional[int] = None,
        cond_value: Optional[int] = None,
        cond_judgment: Optional[str] = None,
        block: Optional[bool] = True,
    ) -> CmdResponse:
        """Linear motion, need to check robot motion status to determine if motion is complete after execution

        Args
        ----
            target_joint (list): Target joint data
            speed (int): Linear speed: 1-3000; Rotation speed: 1-300;
            speed_type (int, optional): 0 for V linear speed, 1 for VR rotation speed, 2 for AV, 3 for AVR. Defaults to None.
            acc (int, optional): Acceleration, defaults to 0 if not specified. Defaults to None.
            dec (int, optional): Deceleration, defaults to 0 if not specified. Defaults to None.
            cond_type (int, optional): IO type, 0 for input, 1 for output.
            cond_num (int, optional): IO address, 0~63.
            cond_value (int, optional): IO status, 0/1, when IO status matches, immediately abandon this motion and execute next instruction.
            block (bool, optional): True: blocking motion, False: non-blocking motion. Defaults to True.

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        params = {"targetPos": target_joint, "speed": speed}
        if speed_type is not None:
            params["speed_type"] = speed_type
        if acc is not None:
            params["acc"] = acc
        if dec is not None:
            params["dec"] = dec
        if cond_type is not None:
            params["cond_type"] = cond_type
        if cond_num is not None:
            params["cond_num"] = cond_num
        if cond_value is not None:
            params["cond_value"] = cond_value
        if cond_judgment is not None:
            params["cond_judgment"] = cond_judgment
        if block:
            move_ret = self.send_CMD("moveByLine", params)
            if move_ret.success:
                self.__wait_stop()
            return move_ret
        else:
            return self.send_CMD("moveByLine", params)

    def move_arc(
        self,
        mid_pos: list,
        target_pos: list,
        speed: int,
        speed_type: Optional[int] = None,
        acc: Optional[int] = None,
        dec: Optional[int] = None,
        cond_type: Optional[int] = None,
        cond_num: Optional[int] = None,
        cond_value: Optional[int] = None,
        block: Optional[bool] = True,
    ) -> CmdResponse:
        """Arc motion, need to check robot motion status to determine if motion is complete after execution

        Args
        ----
            target_joint (list): Target joint data
            speed (int): Linear speed: 1-3000; Rotation speed: 1-300;
            speed_type (int, optional): 0 for V linear speed, 1 for VR rotation speed, 2 for AV, 3 for AVR. Defaults to None.
            acc (int, optional): Acceleration, defaults to 0 if not specified. Defaults to None.
            dec (int, optional): Deceleration, defaults to 0 if not specified. Defaults to None.
            cond_type (int, optional): IO type, 0 for input, 1 for output.
            cond_num (int, optional): IO address, 0~63.
            cond_value (int, optional): IO status, 0/1, when IO status matches, immediately abandon this motion and execute next instruction.
            block (bool, optional): True: blocking motion, False: non-blocking motion. Defaults to True.

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        params = {"midPos": mid_pos, "targetPos": target_pos, "speed": speed}
        if speed_type is not None:
            params["speed_type"] = speed_type
        if acc is not None:
            params["acc"] = acc
        if dec is not None:
            params["dec"] = dec
        if cond_type is not None:
            params["cond_type"] = cond_type
        if cond_num is not None:
            params["cond_num"] = cond_num
        if cond_value is not None:
            params["cond_value"] = cond_value
        print(params)
        if block:
            move_ret = self.send_CMD("moveByArc", params)
            if move_ret.success:
                self.__wait_stop()
            return move_ret
        else:
            return self.send_CMD("moveByArc", params)

    def move_speed_j(self, vj: list, acc: float, t: float) -> CmdResponse:
        """Joint uniform motion

        Args
        ----
            vj (list): 8 joint velocity values, unit: degrees/second
            acc (float): Joint acceleration >0, degrees/s**2
            t (float): Joint uniform motion time

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        return self.send_CMD("moveBySpeedj", {"vj": vj, "acc": acc, "t": t})

    def move_stop_speed_j(self, stop_acc: int) -> CmdResponse:
        """Stop joint uniform motion

        Args
        ----
            stop_acc (int): Stop motion with this acceleration, >0

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        return self.send_CMD("stopj", {"acc": stop_acc})

    def move_speed_l(
        self, v: list, acc: float, t: float, arot: Optional[float] = None
    ) -> CmdResponse:
        """Linear uniform motion

        Args
        ----
            v (list): Velocity values along 6 directions, first three units mm/s, last three degrees/s
            acc (float): Displacement acceleration, >0, unit mm/s**2
            t (float): Total time for linear uniform motion, >0
            arot (float, optional): Attitude acceleration, >0, unit degrees/s**2. Defaults to None.

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        params = {"v": v, "acc": acc, "t": t}
        if arot is not None:
            params["arot"] = arot
        return self.send_CMD("moveBySpeedl", params)

    def move_stop_speed_l(self, stop_acc: int) -> CmdResponse:
        """Stop linear uniform motion

        Args
        ----
            stop_acc (int): Stop motion with this acceleration, range: >0

        Returns
        -------
            bool: Execution result, True: execution successful, False: execution failed
        """
        return self.send_CMD("stopl", {"acc": stop_acc})

    def move_line_in_coord(
        self,
        target_user_pose: list,
        speed: float,
        speed_type: int,
        user_coord: list,
        acc: int = 0,
        dec: int = 0,
        cond_type: Optional[int] = None,
        cond_num: Optional[int] = None,
        cond_value: Optional[int] = None,
        unit_type: Optional[int] = None,
    ):
        """Linear motion in specified coordinate system

        Args
        ----
            target_user_pose (list): Pose in specified coordinate system.
            speed (float): Linear speed: 1-3000; Rotation speed: 1-300.
            speed_type (int): 0 for V linear speed, 1 for VR rotation speed, 2 for AV, 3 for AVR.
            user_coord (list): Specified coordinate system data.
            acc (int, optional): Acceleration. Defaults to 0.
            dec (int, optional): Deceleration. Defaults to 0.
            cond_type (int, optional): IO type, 0 for input, 1 for output.
            cond_num (int, optional): IO address, 0~63.
            cond_value (int, optional): IO status, 0/1, when IO status matches, immediately abandon this motion and execute next instruction.
            unit_type (int, optional): User coordinate rx, ry, rz, 0: degrees, 1: radians, defaults to radians if not specified. Defaults to None.
        """
        params = {
            "targetUserPose": target_user_pose,
            "speed": speed,
            "speed_type": speed_type,
        }
        if user_coord is not None:
            params["user_coord"] = user_coord
        if acc is not None:
            params["acc"] = acc
        if dec is not None:
            params["dec"] = dec
        if cond_type is not None:
            params["cond_type"] = cond_type
        if cond_num is not None:
            params["cond_num"] = cond_num
        if cond_value is not None:
            params["cond_value"] = cond_value
        if unit_type is not None:
            params["unit_type"] = unit_type

        return self.send_CMD("moveByLineCoord", params)

    # Waypoint operation section
    def clear_path_point(self) -> CmdResponse:
        """Clear waypoint information 2.0

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        return self.send_CMD("clearPathPoint")

    def move_by_path(self) -> CmdResponse:
        """Waypoint motion

        Returns
        -------
            int: -1 if failed, successful: total number of waypoints
        """
        return self.send_CMD("moveByPath")

    def add_path_point(
        self,
        way_point: list,
        move_type: int,
        speed: float,
        acc: int = 20,
        dec: int = 20,
        smooth: Optional[int] = None,
        circular_radius: Optional[int] = None,
        speed_type: Optional[int] = None,
        cond_type: Optional[int] = None,
        cond_num: Optional[int] = None,
        cond_value: Optional[int] = None,
        cond_judgment: Optional[str] = None,
    ) -> CmdResponse:
        """Add waypoint information
           #!If motion type is joint motion, speed_type is invalid, not recommended

        Args
        ----
            way_point (list): Target position
            move_type (int): 0 joint motion, 1 linear motion (rotation speed determined by linear speed), 2 linear motion (linear speed determined by rotation speed), 3 arc motion
            speed_type (int): Speed type, 0: V (linear speed) corresponding speed [1,3000], 1: VR (rotation speed) corresponding speed [1-300], 2: AV (absolute linear speed) corresponding [min_AV,max_AV], 3: AVR (absolute rotation speed) corresponding [min_AVR,max_AVR]
            speed (float): Motion speed, when no speed_type parameter, corresponds to joint speed [1,100], linear and arc speed [1,3000], rotation speed [1,300]
            acc(int, optional): Acceleration, Defaults to 20.
            dec(int, optional): Deceleration, Defaults to 20.
            smooth (int, optional): Smoothness, 0~7, use either this parameter or blend radius, this parameter is gradually being deprecated, Defaults to 0.
            circular_radius (int, optional): Blend radius, 0~2147483647, this value calculates different blend radii based on different points, Defaults to 0.
            cond_type (int, optional): IO type, 0 for input, 1 for output.
            cond_num (int, optional): IO address, 0~63.
            cond_value (int, optional): IO status, 0/1, when IO status matches, immediately abandon this motion and execute next instruction.

        Returns
        -------
            bool: True if operation successful, False if operation failed
        """
        params = {
            "wayPoint": way_point,
            "moveType": move_type,
            "speed": speed,
            "acc": acc,
            "dec": dec,
        }
        if smooth is not None:
            params["smooth"] = smooth
        if circular_radius is not None:
            params["circular_radius"] = circular_radius
        if speed_type is not None:
            params["speed_type"] = speed_type
        if cond_type is not None:
            params["cond_type"] = cond_type
        if cond_num is not None:
            params["cond_num"] = cond_num
        if cond_value is not None:
            params["cond_value"] = cond_value
        if cond_judgment is not None:
            params["cond_judgment"] = cond_judgment

        return self.send_CMD("addPathPoint", params)

    def get_running_path_index(self) -> CmdResponse:
        """Get current running waypoint index

        Returns
        -------
            int: Current running waypoint index, -1 for non-waypoint motion
        """
        return self.send_CMD("getPathPointIndex")
