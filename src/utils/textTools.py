import whisper
import os
import json
import base64
import hashlib
import hmac
import time
import requests
import urllib.parse
from src.config import DEFAULT_MODEL
import src.log as log

class WhisperTranscriber:
    """使用OpenAI的Whisper模型进行语音转文字。"""
    
    def __init__(self, model_size=DEFAULT_MODEL):
        """
        初始化Whisper模型。
        
        参数:
            model_size: 使用的模型大小 (tiny, base, small, medium, large)
        """
        self.model = None
        self.model_size = model_size
        
    def is_cuda_available(self):
        """检查是否可用CUDA进行GPU加速。"""
        return whisper.torch.cuda.is_available()
    
    def load_model(self):
        """加载Whisper模型。"""
        if self.model is None:
            device = "cuda" if self.is_cuda_available() else "cpu"
            log.info(f"正在加载Whisper模型 '{self.model_size}' 在 {device} 上...")
            self.model = whisper.load_model(self.model_size, device=device)
            log.info("Whisper模型加载成功！")
    
    def transcribe_audio(self, audio_file, prompt="以下是普通话的句子。"):
        """
        将音频文件转换为文本。
        
        参数:
            audio_file: 音频文件路径
            prompt: 可选的转录提示词
            
        返回:
            转录的文本
        """
        if self.model is None:
            self.load_model()
            
        log.info(f"正在转录音频: {audio_file}")
        result = self.model.transcribe(audio_file, initial_prompt=prompt)
        
        # 从片段中提取文本
        transcription = "".join([segment["text"] for segment in result["segments"] if segment is not None])
        
        return transcription

class XunfeiTranscriber:
    """使用讯飞API进行语音转文字。"""
    
    def __init__(self, appid, secret_key):
        """
        初始化讯飞API客户端。
        
        参数:
            appid: 讯飞API的应用ID
            secret_key: 讯飞API的密钥
        """
        self.appid = appid
        self.secret_key = secret_key
        self.host = 'https://raasr.xfyun.cn/v2/api'
        self.upload_api = '/upload'
        self.get_result_api = '/getResult'
    
    def get_signature(self):
        """根据appid和时间戳生成API签名。"""
        ts = str(int(time.time()))
        
        # 生成MD5哈希
        m2 = hashlib.md5()
        m2.update((self.appid + ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5_bytes = bytes(md5, encoding='utf-8')
        
        # 生成HMAC-SHA1签名
        signature = hmac.new(self.secret_key.encode('utf-8'), md5_bytes, hashlib.sha1).digest()
        signature = base64.b64encode(signature)
        signature = str(signature, 'utf-8')
        
        return signature, ts
    
    def upload_audio(self, audio_file):
        """
        上传音频到讯飞API。
        
        参数:
            audio_file: 音频文件路径
            
        返回:
            转录请求的订单ID
        """
        # 生成签名
        signature, ts = self.get_signature()
        
        # 准备参数
        file_size = os.path.getsize(audio_file)
        file_name = os.path.basename(audio_file)
        
        params = {
            'appId': self.appid,
            'signa': signature,
            'ts': ts,
            'fileSize': file_size,
            'fileName': file_name,
            'duration': '200'  # 默认时长
        }
        
        # 上传文件
        with open(audio_file, 'rb') as f:
            data = f.read(file_size)
        
        url = f"{self.host}{self.upload_api}?{urllib.parse.urlencode(params)}"
        response = requests.post(
            url=url,
            headers={"Content-type": "application/json"},
            data=data
        )
        
        result = response.json()
        
        if result.get('code') != 0:
            log.error(f"上传失败: {result.get('message')}")
            return None
            
        return result['content']['orderId']
    
    def get_transcription_result(self, order_id):
        """
        从讯飞API获取转录结果。
        
        参数:
            order_id: 上传响应中的订单ID
            
        返回:
            转录的文本
        """
        # 生成签名
        signature, ts = self.get_signature()
        
        # 准备参数
        params = {
            'appId': self.appid,
            'signa': signature,
            'ts': ts,
            'orderId': order_id,
            'resultType': "transfer,predict"
        }
        
        # 轮询结果
        url = f"{self.host}{self.get_result_api}?{urllib.parse.urlencode(params)}"
        status = 3  # 初始状态（处理中）
        
        while status == 3:
            response = requests.post(
                url=url,
                headers={"Content-type": "application/json"}
            )
            
            result = response.json()
            status = result['content']['orderInfo']['status']
            
            if status == 4:  # 完成
                break
                
            time.sleep(5)  # 等待后再次检查
        
        if status != 4:
            log.error(f"转录失败，状态码: {status}")
            return None
            
        # 从结果中提取文本
        try:
            order_result_str = result.get("content", {}).get("orderResult", "{}")
            order_result = json.loads(order_result_str)
            
            sentences = []
            for lattice in order_result.get("lattice", []):
                json_1best_str = lattice.get("json_1best", "{}")
                json_1best = json.loads(json_1best_str)
                
                # 提取并处理每个词
                for rt in json_1best.get("st", {}).get("rt", []):
                    sentence = ''.join([cw[0]["w"] for ws in rt["ws"] for cw in ws["cw"]])
                    sentences.append(sentence)
            
            transcription = ' '.join(sentences)
            return transcription
        except Exception as e:
            log.error(f"解析结果出错: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_file):
        """
        使用讯飞API将音频文件转换为文本。
        
        参数:
            audio_file: 音频文件路径
            
        返回:
            转录的文本
        """
        # 上传音频文件
        log.info(f"正在上传音频到讯飞API: {audio_file}")
        order_id = self.upload_audio(audio_file)
        if not order_id:
            return None
            
        # 获取转录结果
        log.info(f"音频上传成功，订单ID: {order_id}，等待转录结果...")
        return self.get_transcription_result(order_id)


# 获取合适的转录器的工厂函数
def get_transcriber(engine="whisper", **kwargs):
    """
    根据指定的引擎获取语音转文字转录器。
    
    参数:
        engine: 使用的转录引擎 ('whisper' 或 'xunfei')
        **kwargs: 转录器的额外参数
        
    返回:
        转录器实例
    """
    if engine.lower() == "whisper":
        model_size = kwargs.get("model_size", DEFAULT_MODEL)
        return WhisperTranscriber(model_size=model_size)
    elif engine.lower() == "xunfei":
        appid = kwargs.get("appid")
        secret_key = kwargs.get("secret_key")
        if not (appid and secret_key):
            raise ValueError("讯飞转录器需要 'appid' 和 'secret_key'")
        return XunfeiTranscriber(appid=appid, secret_key=secret_key)
    else:
        raise ValueError(f"不支持的转录引擎: {engine}")


# 转录音频文件的函数
def transcribe_file(audio_file, engine="whisper", **kwargs):
    """
    将音频文件转换为文本。
    
    参数:
        audio_file: 音频文件路径
        engine: 使用的转录引擎 ('whisper' 或 'xunfei')
        **kwargs: 转录器的额外参数
        
    返回:
        转录的文本
    """
    transcriber = get_transcriber(engine=engine, **kwargs)
    return transcriber.transcribe_audio(audio_file)