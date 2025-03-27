import os
import time
import json
from ppadb.client import Client as AdbClient
import uiautomator2 as u2
import base64
from qwenvl_agent import perform_gui_grounding_with_api


class Android_VL_Agent:

    def __init__(self):
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self.device_serial = None
        self.u2_device = None
        self.SCREENSHOT_PATH = None
        self.QWEN_MODEL_ID = 'qwen2.5-vl-7b-instruct'
        self.__set_up()

    @staticmethod
    def check_adb_service():
        try:
            result = os.popen("adb devices").read()
            if "List of devices attached" in result:
                return True
            else:
                os.system("adb start-server")
                time.sleep(5)  # 等待 ADB 服务启动
                result = os.popen("adb devices").read()
                if "List of devices attached" in result:
                    return True
                else:
                    return False
        except Exception:
            print("ADB服务启动失败")
            return False
    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def info_parser(info):
        try:
            body = info.split("<tool_call>")[1].split("</tool_call>")[0]
            return json.loads(body)
        except Exception as e:
            print(f"解析失败: {str(e)}")
            return None

    # 启动
    def __set_up(self):
        assert self.check_adb_service()
        devices = self.client.devices()
        self.device_serial = devices[0].serial if devices else None
        self.u2_device = u2.connect(self.device_serial)
        self.SCREENSHOT_PATH = "screenshot.png"

    # 定义单点事件
    def __single_point_event(self,x,y):
        try:
            self.u2_device.click(x, y)
            return True
        except Exception as e:
            print(f"单点失败: {str(e)}")
            return False

    # 定义输入内容
    def __input_content(self,content):
        try:
            self.u2_device.send_keys(content)
            return True
        except Exception as e:
            print(f"输入失败: {str(e)}")
            return False

    # 截图并保存
    def __screenshot(self):
        try:
            # 清除之前的截图
            if os.path.exists(self.SCREENSHOT_PATH):
                os.remove(self.SCREENSHOT_PATH)
            screenshot = self.u2_device.screenshot()
            screenshot.save(self.SCREENSHOT_PATH)
            # screenshot.show()
            return True
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return False

    def __Qwen_vl_agent(self, query):
        output_info = perform_gui_grounding_with_api(self.SCREENSHOT_PATH, query, self.QWEN_MODEL_ID)
        # print(output_info)
        result = self.info_parser(str(output_info))["arguments"]
        return result

    def __action(self,result):
        if "click" in result["action"]:
            coordinate = result["coordinate"]
            self.__single_point_event(coordinate[0],coordinate[1])
        elif "type" in result["action"]:
            self.__input_content(result["text"])

    def run(self,query):
        # 重新连接
        self.u2_device = u2.connect(self.device_serial)
        # 感知
        self.__screenshot()
        # 理解
        result = self.__Qwen_vl_agent(query)
        print(result)
        # 执行
        self.__action(result)

    def __call__(self,query):
        self.run(query)

if __name__ == "__main__":
    agent = Android_VL_Agent()
    # timestep
    timestep = 2
    name = "名字"
    message = "信息"

    agent.run("打开微信")
    time.sleep(timestep)
    agent.run(f"点击和{name}聊天框的的顶部区域进入聊天界面")
    time.sleep(timestep)
    agent.run("点击屏幕底部的输入框部分进入输入界面")
    time.sleep(timestep)
    agent.run(f"在聊天框输入内容：{message}")
    time.sleep(timestep)
    agent.run("点击右侧发送按钮中心位置发送消息")