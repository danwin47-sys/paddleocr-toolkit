# CLI Commands Documentation

## 可用命令

PaddleOCR Toolkit v1.2.0提供以下CLI命令：

---

## paddleocr init

初始化PaddleOCR Toolkit项目。

### 用法

```bash
paddleocr init [directory]
```

### 参数

- `directory`: 项目目录（可选，默认为当前目录）

### 示例

```bash
# 在当前目录初始化
paddleocr init

# 在指定目录初始化
paddleocr init my_ocr_project
```

### 创建内容

- `input/` - 输入文件目录
- `output/` - 输出结果目录
- `config/` - 配置文件目录
- `logs/` - 日志文件目录
- `config/default.yaml` - 默认配置
- `README.md` - 项目说明
- `.gitignore` - Git忽略文件

---

## paddleocr config

交互式配置向导。

### 用法

```bash
paddleocr config [--show CONFIG_FILE]
```

### 选项

- `--show CONFIG_FILE`: 显示指定配置文件的内容

### 示例

```bash
# 启动配置向导
paddleocr config

# 显示配置文件
paddleocr config --show config/default.yaml
```

### 配置项

- **OCR设置**: mode, device, dpi, lang
- **输出设置**: format, directory
- **性能设置**: batch_size, max_workers, enable_cache
- **日志设置**: level, file

---

## paddleocr process

处理文件或目录。

### 用法

```bash
paddleocr process INPUT [options]
```

### 参数

- `INPUT`: 输入文件或目录

### 选项

- `--mode {basic,hybrid,structure}`: OCR模式（默认: hybrid）
- `--output DIR`: 输出目录
- `--format FORMAT`: 输出格式（默认: md）

### 示例

```bash
# 处理单个PDF
paddleocr process document.pdf

# 指定模式和输出
paddleocr process document.pdf --mode structure --output results/

# 批量处理
paddleocr process documents/ --format json
```

---

## paddleocr benchmark

性能基准测试。

### 用法

```bash
paddleocr benchmark PDF [--output REPORT]
```

### 参数

- `PDF`: 测试PDF文件

### 选项

- `--output REPORT`: 报告输出路径（可选）

### 示例

```bash
# 运行基准测试
paddleocr benchmark test.pdf

# 保存报告
paddleocr benchmark test.pdf --output benchmark_report.json
```

### 测试场景

1. Basic (DPI 150)
2. Basic (DPI 200)
3. Hybrid (DPI 150)
4. Hybrid (DPI 200)

### 输出

- 处理时间
- 速度（秒/页）
- 内存使用
- JSON格式报告

---

## paddleocr validate

验证OCR结果准确率。

### 用法

```bash
paddleocr validate OCR_RESULTS GROUND_TRUTH
```

### 参数

- `OCR_RESULTS`: OCR结果JSON文件
- `GROUND_TRUTH`: 真实文本TXT文件

### 示例

```bash
paddleocr validate output.json ground_truth.txt
```

### 指标

- **字符准确率**: 字符级别的准确度
- **词准确率**: 词级别的准确度
- **编辑距离**: Levenshtein距离
- **综合评分**: 整体评级

### 输出

```
字符准确率: 95.2%
词准确率: 92.8%
编辑距离: 45
综合准确率: 94.0%
评级: +++ 优秀
```

---

## 全局选项

所有命令都支持以下全局选项：

- `--version`: 显示版本信息
- `--help`: 显示帮助信息

---

## 示例工作流

### 1. 创建新项目

```bash
# 初始化
paddleocr init my_project
cd my_project

# 配置
paddleocr config

# 处理文件
cp ~/document.pdf input/
paddleocr process input/document.pdf

# 查看结果
cat output/document.md
```

### 2. 性能测试

```bash
# 测试性能
paddleocr benchmark test.pdf --output report.json

# 查看报告
cat report.json
```

### 3. 质量验证

```bash
# 处理文件
paddleocr process document.pdf --format json --output results/

# 验证准确率
paddleocr validate results/document.json ground_truth.txt
```

---

## 配置文件示例

`config/default.yaml`:

```yaml
ocr:
  mode: hybrid
  device: gpu
  dpi: 200
  lang: ch
  use_angle_cls: true

output:
  format: md
  directory: ./output

performance:
  batch_size: 8
  max_workers: 4
  enable_cache: true

logging:
  level: INFO
  file: ./logs/paddleocr.log
```

---

## 常见问题

### Q: 如何更改OCR语言？

A: 使用`config`命令或编辑配置文件中的`ocr.lang`。

### Q: 如何提升处理速度？

A:

1. 使用GPU (`device: gpu`)
2. 降低DPI (`dpi: 150`)
3. 启用缓存 (`enable_cache: true`)
4. 增加批次大小 (`batch_size: 16`)

### Q: 支持哪些输出格式？

A: md, json, html, txt, xlsx

---

**更多信息**: [完整文档](https://github.com/danwin47-sys/paddleocr-toolkit)
