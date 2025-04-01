# Bili2Text v3 开发文档

## 项目结构

```
+-- src                     -- + 源代码
|  +-- utils                --  - 工具函数
|  |  +-- audioTools.py     --      + 音频处理工具
|  |  +-- videoTools.py     --      + 视频处理工具
|  |  +-- textTools.py      --      + 文本处理工具
|  +-- webserver            --  - Web服务器
|  |  +-- db                --      + 数据库
|  |  |  +-- service.py     --          + 数据库服务
|  |  +-- server.py         --      + 服务器
|  |  +-- templates         --      - 模板
|  |  |  +-- ...pages       --          + 网页
|  +-- core.py              --  - 核心
+ requirements.txt          -- - 依赖
+ main.py                   -- - 主程序入口
```

## 测试

### 完整测试

```bash
# 基本用法（使用默认的whisper引擎和small模型）
python test_bili.py BV1xx411c79H

# 使用tiny模型（速度更快但精度较低）
python test_bili.py BV1xx411c79H --model tiny

# 使用讯飞引擎（需要提供appid和secret）
python test_bili.py BV1xx411c79H --engine xunfei --xf-appid 你的APPID --xf-secret 你的SECRET

# 提供自定义转录提示词
python test_bili.py BV1xx411c79H --prompt "这是一个关于科技的视频，使用中文普通话。"

# 不保存元数据
python test_bili.py BV1xx411c79H --no-metadata

```

### 组件测试

```bash
# 仅测试下载功能
python test_components.py download --bv BV1xx411c79H

# 仅测试音频提取功能（需要指定视频文件路径）
python test_components.py audio --video bilibili_video/BV1xx411c79H.mp4

# 仅测试转录功能（需要指定音频文件路径）
python test_components.py transcribe --audio audio/conv/BV1xx411c79H_20230601123456.mp3

# 完整流程测试（与test_bili.py类似，但提供更详细的每步执行信息）
python test_components.py all --bv BV1xx411c79H

# 使用不同的转录引擎参数
python test_components.py transcribe --audio audio/conv/example.mp3 --engine whisper --model tiny

```