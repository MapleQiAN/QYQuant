# QYS CLI 参考

`qys` 是 QYSP 的命令行入口，当前提供 6 个子命令：`init`、`validate`、`build`、`migrate`、`backtest`、`import`。

如果脚本没有加入 PATH，可以把 `qys` 替换成：

```bash
py -3.11 -m qysp.cli.main
```

## 1. `qys --help`

```bash
qys --help
```

用途：

- 查看 CLI 总览
- 确认当前版本包含哪些子命令

你应该在输出中看到这 6 个命令：

```text
init
validate
build
migrate
backtest
import
```

## 2. `qys init <name> [--template]`

创建一个新的策略目录。

```bash
qys init my-strategy --template trend-following
```

参数：

- `name`：策略目录名，必须以字母或数字开头，只允许字母、数字、`.`、`-`、`_`
- `--template`：内置模板，当前可选值为：
  - `trend-following`
  - `mean-reversion`
  - `momentum`
  - `multi-indicator`

输出示例：

```text
Strategy project 'my-strategy' created successfully (template: trend-following)
```

失败场景：

- 目录已存在：退出码 `1`
- 名称不合法：退出码 `1`

## 3. `qys validate <path>`

验证策略目录或 `.qys` 包。

```bash
qys validate docs/strategy-format/examples/GoldStepByStep/
qys validate GoldStepByStep.qys
```

行为：

- 传入目录：只验证 `strategy.json` 是否符合 Schema
- 传入 `.qys`：额外验证 `integrity` 清单和包结构

成功输出：

```text
Validation passed
```

退出码：

- `0`：验证通过
- `1`：验证失败
- `2`：路径不存在

常见错误：

- `strategy.json` 缺失
- 必填字段缺失
- `id` 不是合法 UUID
- `.qys` 中 `integrity.files` 与真实文件不一致

## 4. `qys build <source_dir> [--output]`

把策略目录打包为 `.qys` 文件。

```bash
qys build my-strategy
qys build my-strategy --output dist/my-strategy.qys
```

行为：

1. 检查 `strategy.json` 和 `src/strategy.py` 是否存在
2. 遍历目录并排除无关文件
3. 自动生成 `integrity.files`
4. 写出 `.qys` ZIP 包
5. 对产物执行一次 `validate`

默认排除项：

- 目录：`__pycache__`、`.git`、`.svn`、`.hg`、`.venv`、`node_modules`
- 后缀：`.pyc`、`.pyo`
- 文件名：`.DS_Store`、`Thumbs.db`、`.gitignore`

成功输出：

```text
Package built: my-strategy.qys
```

失败场景：

- 缺少 `strategy.json`：退出码 `1`
- 缺少 `src/strategy.py`：退出码 `1`
- 构建完成但产物校验失败：退出码 `1`

## 5. `qys migrate <path>`

把策略目录、`strategy.json` 文件或 `.qys` 包迁移到当前 Schema 版本。

```bash
qys migrate my-strategy
qys migrate my-strategy/strategy.json
qys migrate my-strategy.qys
```

当前版本：

```text
1.0
```

当前实现很保守，只处理 `schemaVersion` 升级：

- 已经是 `1.0`：输出 `Already latest schema version (1.0)`
- 旧版本：把 `schemaVersion` 改写为 `1.0`，然后输出 `Migration completed`

退出码：

- `0`：迁移成功或已经是最新版本
- `1`：输入结构不合法
- `2`：路径不存在

## 6. `qys backtest <path>`

```bash
qys backtest my-strategy.qys
```

当前状态：

- 这是一个占位命令
- 会输出一条说明消息并正常退出

示例输出：

```text
Backtest command will be integrated in a later version (Epic 3).
```

## 7. `qys import <path>`

```bash
qys import my-strategy.qys
```

当前状态：

- 这是一个占位命令
- 会输出一条说明消息并正常退出

示例输出：

```text
Import command will be integrated in a later version (Epic 5).
```

## 8. 推荐工作流

```bash
qys init my-strategy --template trend-following
qys validate my-strategy
qys build my-strategy --output my-strategy.qys
qys validate my-strategy.qys
```

这个流程覆盖了从模板生成、Schema 检查到最终打包的完整闭环。
