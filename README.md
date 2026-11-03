InputCH - 轻量级智能中文拼音输入法

InputCH 是一款基于 Python 开发的轻量级桌面与 Web 中文拼音输入法。项目采用基于 N-gram + Beam Search 的智能整句解码引擎，支持全局键盘钩子注入、模糊音容错、简拼匹配，并提供可选的本地大语言模型（LLM）续写增强。


核心特性

1. 全局键盘注入
   在 Windows 环境下采用 WH_KEYBOARD_LL 低层键盘钩子，在不抢占窗口焦点的前提下，通过 SendInput 将字符直接写入目标应用。

2. 丰富开源词库
   整合 THUOCL 领域词库、Mozillazg 单字与词组拼音库，以及 RIME essay 百万级词频总表。

3. 智能解码与容错
   - 基于 N-gram 语言模型与 Beam Search 解码。
   - 支持 z/zh, c/ch, s/sh, an/ang, en/eng, in/ing 等声韵母模糊音容错。
   - 支持首字母纯声母简拼输入（如 nh 匹配 你好）。

4. AI 智能续写（可选）
   支持接入 OpenAI 兼容接口（如本地 llama-server 或 Deepseek API），提供输入上下文的整句联想补全。

5. 双运行模式
   提供 Tkinter 桌面浮动候选条客户端，以及基于 Python 标准库的纯 Web HTTP 服务接口。


目录结构

InputCH/
├── app.py                # 桌面客户端（Tkinter 浮动候选条 + Win32 全局钩子）
├── server.py             # Web 服务端接口（HTTP 服务）
├── engine.py             # 解码引擎（Beam Search、词库索引与模型计算）
├── config.py             # 运行配置与参数定义
├── pinyin_util.py        # 拼音音节切分与处理工具
├── pinyin_fallback.py    # 常用汉字拼音离线映射表
├── llm_hook.py           # LLM API 接入与降级处理
├── build_exe.bat         # Windows 一键打包脚本
└── githubMIT/            # 外部开源词库存储目录


快速开始

1. 环境要求
   Python 3.8 或更高版本。
   操作系统：Windows（支持全局键盘注入），Linux / macOS（支持本地模式与 Web 模式）。

2. 安装依赖
   pip install pypinyin pyinstaller Pillow

   注：pypinyin 为可选依赖。若未安装，系统会自动使用内置 fallback 拼音表。

3. 启动桌面客户端
   python app.py
   - 按反引号 (`) 键或点击标题栏状态按钮可切换输入法开启/关闭状态。

4. 启动 Web 服务
   python server.py
   - 启动后访问 http://localhost:8081 即可使用 Web 界面进行拼音输入。


打包为可执行文件

运行根目录下的构建脚本：
build_exe.bat

脚本将执行以下步骤：
1. 自动检查并安装所需 Python 依赖。
2. 自动拉取开源拼音词库。
3. 使用 PyInstaller 生成独立可执行文件 dist/InputCH.exe。


AI 续写配置

如需开启 LLM 联想功能：
1. 启动本地 llama-server 服务（默认端口 8080）：
   llama-server.exe -m model/your-model.gguf -c 15000 --port 8080
2. 当输入法检测到 http://localhost:8080/v1 可用时，将自动激活 AI 续写按钮。


致谢与许可

本项目引用并使用了以下开源资源：
- mozillazg/pinyin-data 及 phrase-pinyin-data
- rime/rime-essay
- THUOCL 清华大学开放中文词汇库