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

需要 Python 3 和 Windows 系统。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 手动选择模式
.\.venv\Scripts\python.exe main.py

# 指定目标文件
.\.venv\Scripts\python.exe main.py "C:\path\to\your\file.txt"
```

## 自定义动画和音频

默认资源配置位于 `config/default.json`，其中不包含固定的绝对路径。所有相对路径均以配置文件所在目录为基准。

配置文件管理以下资源：

| 配置项 | 用途 |
| --- | --- |
| `resources.background` | 选择界面背景图片 |
| `resources.audio.bgm` | 背景音乐及音量 |
| `resources.audio.voice` | 交互语音及音量 |
| `resources.audio.explosion` | 动作效果音或带音轨的视频文件 |
| `resources.audio.victory` | 可选的文件成功移入回收站后语音 |
| `resources.sprites.walk` | 移动阶段序列帧；可用 `offset_y` 调整行走轨迹高度 |
| `resources.sprites.point` | 交互阶段序列帧 |
| `resources.sprites.kick` | 主要动作序列帧 |
| `resources.sprites.explosion` | 特效序列帧 |
| `resources.sprites.arrival` | 后续入场序列帧 |
| `resources.sprites.departure` | 退场序列帧 |
| `resources.animations.below_target` | 可选的目标下方附加动画组，支持多张精灵图、间距、偏移和持续时间；`duration_ms: 0` 表示跟随主动画直到程序退出 |
| `resources.orbit_effect` | 可选的目标点环绕素材、数量、轨道半径、速度和 FPS |

复制默认配置并修改资源路径即可创建新主题：

```powershell
Copy-Item config\default.json config\my-theme.json

# 编辑 my-theme.json 后运行
.\.venv\Scripts\python.exe main.py --config config\my-theme.json

# 同时指定目标文件
.\.venv\Scripts\python.exe main.py --config config\my-theme.json "C:\path\to\your\file.txt"
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
.\.venv\Scripts\python.exe main.py --config "D:\themes\my-theme\theme.json"
```

仓库还包含一套“拾取石子并击落应用窗口”的原创示例主题：

```powershell
.\.venv\Scripts\python.exe main.py --config config\grandpa-stone.json
```

还可以通过环境变量选择配置：

```powershell
$env:MONSTER_DELETER_CONFIG = "D:\themes\my-theme\theme.json"
.\.venv\Scripts\python.exe main.py
```

使用 `--config` 启动一次程序后，Windows 右键菜单会记住该配置文件。配置加载器会在启动阶段检查 JSON 格式、配置版本、必需字段和所有资源路径，错误会直接显示在终端中。

## 打包发布

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed `
  --name FileKiller `
  --add-data "assets;assets" `
  --add-data "config;config" `
  --hidden-import send2trash `
  main.py
```

生成文件位于 `dist/FileKiller.exe`。默认配置和默认资源会被嵌入程序，也可以继续使用 `--config` 加载程序外部的主题配置和素材。

## 项目结构

```text
FileKiller/
├── main.py                  # UI、动画流程、音频播放和右键菜单注册
├── resource_config.py       # 配置加载、校验和相对路径解析
├── register_menu.py         # 旧版右键菜单注册脚本
├── requirements.txt         # Python 依赖
├── config/
│   └── default.json         # 默认动画、音频和背景配置
├── assets/                  # 默认演示资源
├── scripts/                 # 图片处理辅助脚本
└── tests/                   # 测试代码
```

## 许可

本项目仅供娱乐与学习使用。使用第三方图片、动画、音频或视频制作主题时，请确保拥有相应素材的使用许可。
