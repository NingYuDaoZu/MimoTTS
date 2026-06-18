<div align="center">

# MiMo TTS Studio

基于 **小米 MiMo-V2.5-TTS** 系列模型的桌面语音合成工具，集预置音色、音色设计、音色克隆于一体。

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.14-blue)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## 功能特性

### 🎵 预置音色
使用 `mimo-v2.5-tts` 模型，内置 9 种精品音色，开箱即用。

| 音色 | 语言 | 性别 |
|------|------|------|
| MiMo-默认 | 中文 | - |
| 冰糖 | 中文 | 女 |
| 茉莉 | 中文 | 女 |
| 苏打 | 中文 | 男 |
| 白桦 | 中文 | 男 |
| Mia | 英文 | 女 |
| Chloe | 英文 | 女 |
| Milo | 英文 | 男 |
| Dean | 英文 | 男 |

### 🎨 音色设计
使用 `mimo-v2.5-tts-voicedesign` 模型，通过自然语言描述自定义音色，无需音频样本。

描述维度包括：性别与年龄、音色质感、情绪语气、语速节奏、角色人设、说话风格、场景描写等。

### 🎙️ 音色克隆
使用 `mimo-v2.5-tts-voiceclone` 模型，上传参考音频（mp3/wav，≤10MB），精准复刻任意音色。支持流式模式。

---

## 快速开始

# 克隆仓库
git clone https://github.com/yourname/mimotts.git
cd mimotts

# 安装依赖
pip install openai customtkinter darkdetect

# 运行
python app.py
```

---

## 配置 API Key

两种方式任选其一：

1. **界面输入**：在程序顶部输入框填写 API Key 并点击"保存"，密钥会存储到 `key.txt`
2. **手动配置**：在程序同目录下创建 `key.txt`，将 API Key 写入（一行纯文本）

> API Key 获取方式请参考 [MiMo TTS 官方文档](https://platform.mimotts.com)

---

## 使用说明

### 预置音色
1. 从下拉框选择音色
2. （可选）填写风格指令，如"用欢快的语气说"
3. 输入合成文本
4. 点击"生成语音"

### 音色设计
1. 描述你想要的音色特征，如"温柔的青年女性，带英伦口音"
2. 输入合成文本
3. 点击"生成语音"

### 音色克隆
1. 点击"浏览"选择参考音频文件（mp3/wav）
2. （可选）填写风格指令
3. 输入合成文本
4. 可选勾选"流式"模式
5. 点击"生成语音"

---

## 项目结构

```
mimotts/
├── app.py              # GUI 主程序
├── voice_clone.py      # CLI 版音色克隆工具
├── key.txt             # API Key 存储（不提交到 Git）
├── .gitignore
└── README.md
```

---

## 依赖

- [openai](https://github.com/openai/openai-python) — API 调用
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) — 现代化 GUI 框架
- [darkdetect](https://github.com/albertosottile/darkdetect) — 系统主题检测

---

## 致谢

- [小米 MiMo TTS](https://platform.mimotts.com) — 提供语音合成模型 API
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — 提供美观的 Tkinter 扩展
- [小涙滴] — 提供技术支持
---

## 许可证

[MIT License](LICENSE)
