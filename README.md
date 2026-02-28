# telegram-ksubugreport-anabot

这是一个用于解析并分析 Android 设备上 **KSU BUG 报告** 的 Telegram 机器人。它可以自动处理日志压缩包，提取关键信息并以用户友好的方式通过 Telegram 返回，为开发者和调试人员节省大量时间。

## 🎯 主要特性

- ✅ **自动解压** `.tar.gz` 格式的日志包。
- 🔍 **解析关键文件**：`basic.txt`、`defconfig`/`.defconfig.gz`、`modules.json`。
- 🌐 **多语言支持**：目前提供中文和英文，可根据用户 Telegram 语言设置自动选择。
- 📎 **附件检测与发送**：自动识别可用的日志文件（如 `adb_tree.txt`、`pstore.tar.gz` 等）并打包发送。
- 🧩 **APatch 兼容**：兼容 APatch 的 BUG 报告文件逻辑，自动处理不同文件结构。
- 🧵 **支持超级群组线程**，在群组中同样表现良好。
- 🧹 **运行结束自动清理** 临时文件，避免磁盘累积。

## 🛠 安装与运行指南

**前提条件*：确保你有一个 Telegram Bot Token(可在@BotFather获取)，并且你的服务器环境支持 Python 3.8+。**

### Docker 使用

```bash
docker pull ghcr.io/luyanci/tgkb_bot:latest
docker run -d --name ksubugreport-anabot \
    -e BOT_TOKEN=你的_telegram_bot_token \
    ghcr.io/luyanci/tgkb_bot:latest
```

### 本地使用

1. **克隆仓库**

```bash
git clone https://github.com/luyanci/telegram-ksubugreport-anabot.git
cd telegram-ksubugreport-anabot
```

2. **创建并激活虚拟环境**

```bash
python -m venv .venv
source .venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置 Bot Token**

在项目跟目录有一个 `.env.example` 文件，复制一份并命名为 `.env`，然后将 `BOT_TOKEN` 变量填写为你实际的 Telegram Bot Token。

```bash
BOT_TOKEN=你的telegram_bot_token
```

5. **运行机器人**

```bash
python bot.py
```

机器人会开始以长轮询方式运行，你可以在 Telegram 上向它发送 `/start` 测试是否存活 或将日志包回复给它，使用 `/checklog` 命令触发解析。

## 📁 日志包格式说明

机器人期望接收一个通过 Telegram 发送的 `.tar.gz` 文件，内部目录结构通常包含：

- `basic.txt`：包含内核版本、设备信息等简要配置。
- `defconfig` 或 `defconfig.gz`：内核配置文件。
- `modules.json`：已加载模块信息。
- 若干附加文件，如 `adb_tree.txt`、`pstore.tar.gz`、`dmesg.txt` 等。

它会将必要的文件提取并分析，返回解析结果并发送可下载的附件。

**由于受 Telegram API 限制，机器人只能接受小于20MB的文件，否则会返回错误提示。**

## 🧩 开发与本地测试

你可以在本地环境中使用 `python bot.py` 启动机器人，并通过 Telegram 与它交互进行测试。确保你的 Telegram Bot Token 已正确配置在 `.env` 文件中。

## 📝 本地化支持

语言文本存放在 `locale/` 目录的 JSON 文件里；添加新语言只需新增对应文件并按照现有格式填入条目。

## 📦 依赖

列在 `requirements.txt`，主要包括：

- `python-telegram-bot` telegram 机器人核心库
- `python-dotenv` 用于加载环境变量

## 🧼 清理策略

处理完日志后，机器人会删除临时目录和下载的压缩包，防止磁盘空间占用过多。这在 `bot.py` 的 `finally` 块中实现。

## 🤝 贡献与许可

欢迎通过 fork 和 pull request 提交改进。项目遵循 [MIT 许可证](LICENSE)。

欢迎使用 `telegram-ksubugreport-anabot`，如果有任何问题或建议，请在 GitHub 上提出 issue。