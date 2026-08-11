# FileKiller - 可自定义桌面文件删除动画

FileKiller 是一个支持自定义视觉与声音资源的 Windows 桌面交互应用。它用完整的动画和音频流程替代普通的文件删除提示，并允许通过 JSON 配置快速切换角色、动作、背景和声音，无需修改 Python 代码。

仓库内的图片与音频仅作为一套默认演示资源。你可以替换成自己的逐帧动画、背景图片、BGM、语音和效果音，制作不同主题的桌面删除效果。

## 功能特点

- **配置驱动的动画流程**：支持入场、移动、交互、动作、特效和退场等多阶段序列帧动画。
- **自定义音频与视频资源**：可分别配置 BGM、交互语音和效果音，也支持包含音轨的 MP4 等媒体文件。
- **灵活的序列帧参数**：每组动画可独立设置图片路径、行列数、显示高度、FPS 和使用的帧序号。
- **可替换界面背景**：瞄准界面的背景图片由配置文件指定。
- **快速切换主题**：通过 `--config` 加载不同配置，资源路径相对于配置文件解析，方便将每套主题独立存放。
- **Windows 右键菜单集成**：可以从桌面或文件资源管理器启动配置好的删除动画。
- **安全删除**：文件通过 `send2trash` 移入回收站，不会直接永久删除。

## 运行方式

### 使用打包程序

1. 运行一次 `FileKiller.exe`，完成 Windows 右键菜单注册。
2. 在桌面或文件资源管理器中右键选择目标文件，启动程序注册的删除特效菜单项。
3. 在选择界面点击目标位置，播放当前配置的动画与音频流程。

> 文件最终会被移入回收站。建议首次使用时先用无用文件测试自定义资源和动画定位。

### 从源码运行

需要 Python 3.12、[uv](https://docs.astral.sh/uv/) 和 Windows 系统。首次使用可通过 WinGet 安装 uv，然后同步锁定的依赖：

```powershell
winget install --id astral-sh.uv -e
uv sync

# 手动选择模式
uv run python main.py

# 等价的包入口
uv run python -m filekiller

# 指定目标文件
uv run python main.py "C:\path\to\your\file.txt"
```

应用运行依赖记录在 `pyproject.toml`，完整解析版本由 `uv.lock` 固定。`uv sync` 默认同时安装 `build` 组，以便打包；素材处理和 Windows UI 诊断工具按需安装：

```powershell
uv sync --group assets
uv sync --group diagnostics
```

## 自定义动画和音频

默认 Theme 是 `grandpa-stone`，资源配置位于 `config/grandpa-stone.json`。其中不包含固定的绝对路径，所有相对路径均以配置文件所在目录为基准。

配置文件管理以下资源：

| 配置项 | 用途 |
| --- | --- |
| `resources.context_menu_label` | Windows 文件右键菜单中显示的 Theme 动作名称 |
| `resources.dialog_text` | 动作完成后显示在气泡中的 Theme 问句 |
| `resources.choice_delay_ms` | 问句气泡出现后，确认按钮延迟显示的毫秒数 |
| `resources.background` | 选择界面背景图片 |
| `resources.audio.bgm` | 背景音乐及音量 |
| `resources.audio.voice` | 交互语音及音量 |
| `resources.audio.explosion` | 动作效果音或带音轨的视频文件 |
| `resources.audio.victory` | 可选的胜利语音；预览模式会播放，指定真实文件时仅在成功移入回收站后播放 |
| `resources.sprites.walk` | 移动阶段序列帧；可用 `offset_y` 调整行走轨迹高度 |
| `resources.sprites.point` | 交互阶段序列帧 |
| `resources.sprites.kick` | 主要动作序列帧 |
| `resources.sprites.explosion` | 特效序列帧 |
| `resources.sprites.arrival` | 后续入场序列帧 |
| `resources.sprites.departure` | 退场序列帧；可用 `move_duration_ms` 调整时长，`stabilize_x` 消除帧间前后晃动，`move_wave_cycles` 和 `move_wave_strength` 设置始终向前的走路速度波动 |
| `resources.animations.below_target` | 可选的目标下方附加动画组，支持多张精灵图、间距、偏移、持续时间，以及 `bounce_height`、`bounce_period_ms`、`bounce_fps` 上下跳动参数；`duration_ms: 0` 表示跟随主动画直到程序退出 |
| `resources.orbit_effect` | 可选的目标点环绕素材、数量、轨道半径、速度和 FPS |

复制默认配置并修改资源路径即可创建新主题：

```powershell
Copy-Item config\grandpa-stone.json config\my-theme.json

# 编辑 my-theme.json 后运行
uv run python main.py --config config\my-theme.json

# 同时指定目标文件
uv run python main.py --config config\my-theme.json "C:\path\to\your\file.txt"
```

也可以将配置和素材放在独立目录中：

```text
my-theme/
├── theme.json
├── background.png
├── audio/
│   ├── bgm.mp3
│   ├── voice.mp3
│   └── effect.mp3
└── sprites/
    ├── walk.png
    ├── action.png
    └── effect.png
```

然后直接加载：

```powershell
uv run python main.py --config "D:\themes\my-theme\theme.json"
```

默认的 `grandpa-stone` Theme 会播放“拾取石子并击落应用窗口”的原创动画，无需传入 `--config`：

```powershell
uv run python main.py
```

还可以通过环境变量选择配置：

```powershell
$env:MONSTER_DELETER_CONFIG = "D:\themes\my-theme\theme.json"
uv run python main.py
```

使用 `--config` 启动一次程序后，Windows 右键菜单会记住该配置文件。配置加载器会在启动阶段检查 JSON 格式、配置版本、必需字段和所有资源路径，错误会直接显示在终端中。

## 打包发布

```powershell
uv run pyinstaller --noconfirm --onefile --windowed `
  --name FileKiller `
  --add-data "assets;assets" `
  --add-data "config;config" `
  --hidden-import send2trash `
  main.py

# 将右键菜单更新为调用无控制台的 dist\FileKiller.exe
uv run python register_menu.py
```

生成文件位于 `dist/FileKiller.exe`。双击运行时默认使用已嵌入的 `grandpa-stone` Theme，无需传入 `--config`；仍可使用 `--config` 加载其他外部主题。

## 项目结构

```text
FileKiller/
├── main.py                  # 兼容入口：仍支持 python main.py
├── resource_config.py       # 兼容入口：转发到 filekiller.config
├── register_menu.py         # Windows 右键菜单安装入口
├── filekiller/
│   ├── cli.py               # 命令行解析和程序启动
│   ├── config.py            # 配置加载、校验和路径解析
│   ├── window.py            # 主窗口和动画阶段编排
│   ├── animation.py         # 精灵图切帧与资源加载
│   ├── effects.py           # 环绕效果和目标下方动画组
│   ├── media.py             # 独立音频通道及 BGM 循环
│   ├── widgets.py           # 对话气泡和选择按钮
│   ├── filesystem.py        # 移入回收站
│   └── platform_windows.py  # Windows 右键菜单注册
├── pyproject.toml           # 项目元数据与分组依赖
├── uv.lock                  # 可复现的完整依赖锁
├── config/
│   ├── default.json         # 旧版基础主题配置
│   └── grandpa-stone.json   # 默认主题配置
├── assets/                  # 默认资源及独立主题资源
├── scripts/                 # 图片处理辅助脚本
├── tests/                   # 自动化测试
└── ARCHITECTURE.md          # 面向维护者和 AI 的代码导航
```

## 开发与验证

业务实现都位于 `filekiller/`。修改时先阅读 [ARCHITECTURE.md](ARCHITECTURE.md)，其中记录了启动链、动画时序、模块边界，以及不可随意改变的行为约束。顶层 `main.py` 与 `resource_config.py` 只用于兼容旧命令和旧导入，不应继续堆放业务逻辑。

```powershell
# 运行无需桌面交互的自动化测试
uv run python -m unittest discover -v

# 检查所有 Python 文件能否编译
uv run python -m compileall -q `
  filekiller main.py resource_config.py register_menu.py
```

新增主题通常只需要添加 `config/*.json` 和 `assets/themes/<name>/`，不需要修改 Python。新增动画阶段时，则从 `filekiller/window.py` 的状态机开始，并把具体播放能力放入对应的动画、音频或效果模块。

## 许可

本项目仅供娱乐与学习使用。使用第三方图片、动画、音频或视频制作主题时，请确保拥有相应素材的使用许可。
