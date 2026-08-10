# FileKiller 架构说明

本文是维护者和 AI 的首要代码导航。目标是让改动者先找到正确边界，再阅读少量相关文件，而不是从一个大型入口文件推断全部行为。

## 启动链

```text
python main.py
  -> filekiller.cli.run()
  -> ResourceConfig.load()
  -> register_context_menu()
  -> QApplication
  -> FileKillerWindow
```

`main.py` 和 `resource_config.py` 是兼容层。现有命令、旧类名 `MonsterDeleter` 以及旧配置导入仍受支持，但新代码应直接导入 `filekiller` 中的模块。

## 模块职责

| 模块 | 唯一职责 | 常见修改 |
| --- | --- | --- |
| `filekiller/cli.py` | 参数解析、配置选择、Qt 启动 | 新增 CLI 参数或启动策略 |
| `filekiller/config.py` | JSON 校验、默认值、资源路径解析 | 扩展主题 schema |
| `filekiller/window.py` | 用户交互与动画阶段编排 | 改流程、位置、时序 |
| `filekiller/animation.py` | 精灵图切帧和配置到播放器的转换 | 改序列帧播放能力 |
| `filekiller/effects.py` | 卫星轨道和目标下方动画组 | 新增可复用视觉效果 |
| `filekiller/media.py` | BGM、语音、爆炸、胜利语音通道 | 改音频播放规则 |
| `filekiller/widgets.py` | 对话气泡和按钮的绘制 | 改对话 UI |
| `filekiller/filesystem.py` | 将目标移入回收站 | 改文件处理策略 |
| `filekiller/platform_windows.py` | Windows 注册表集成 | 改右键菜单 |
| `filekiller/runtime.py` | 导入 QtMultimedia 前的环境设置 | 改平台运行时兼容性 |

依赖方向保持单向：`cli -> window -> animation/effects/media/widgets/filesystem`。配置对象可以被各能力模块读取；能力模块不应反向调用窗口的阶段方法。

## 主流程状态机

`FileKillerWindow` 的公开阶段方法保留了原项目命名，便于追踪历史和兼容已有调用：

```text
选择目标点
  -> 卫星开始环绕
  -> start_phase1_walk（BGM、目标下方动画、行走）
  -> start_phase2_point（交互语音、指向动画）
  -> show_dialog（确认）
  -> start_phase3_kick
  -> trigger_explosion（停止卫星、爆炸、移入回收站、成功语音）
  -> start_phase4_leo
  -> start_phase5_fly
  -> on_app_exit（停止全部资源并退出）
```

## 必须保持的行为约束

- 文件只通过 `send2trash` 移入回收站，不做永久删除。
- 只有成功移入回收站后才播放可选的 `victory` 语音。
- 卫星从选定目标点后开始，在爆炸触发时消失。
- `below_target.duration_ms` 为 `0` 时，附加动画持续到主角色退场；大于 `0` 时按配置停止。
- 精灵图的相对资源路径以其 JSON 配置文件所在目录为基准。
- Windows 上必须在导入 `PyQt6.QtMultimedia` 前设置媒体后端；相关顺序集中在 `runtime.py` 和 `media.py`。
- 顶层 `python main.py`、`from main import MonsterDeleter` 和 `from resource_config import ResourceConfig` 均为兼容接口。
- 爆炸目前由动作帧索引 `5` 触发；若主题需要不同帧，优先把该值扩展到配置，而不是加入主题名称判断。

## 如何扩展

### 新主题

复制一份配置，把素材放进独立主题目录，调整路径和精灵图参数。配置加载器会在窗口创建前校验所有文件。仅新增主题时不应修改 `window.py`。

### 新资源字段

先在 `config.py` 中校验并返回不可变副本，再由具体能力模块消费；同步更新 README、示例配置和配置测试。

### 新动画阶段

在 `window.py` 中只写阶段切换和坐标/时序。若涉及通用播放逻辑，把它实现于 `animation.py`、`effects.py` 或 `media.py`，窗口只调用明确的方法。

## 验证

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v

.\.venv\Scripts\python.exe -m compileall -q `
  filekiller main.py resource_config.py register_menu.py
```

自动化测试不删除真实文件。完整的桌面交互仍应使用一个临时测试文件手动验证，因为目标点、音频设备和 Windows 回收站属于系统集成边界。
