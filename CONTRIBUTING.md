# Contributing to PaddleOCR Toolkit

感谢你考虑为 PaddleOCR Toolkit 做贡献！

---

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发设置](#开发设置)
- [提交指南](#提交指南)
- [代码规范](#代码规范)
- [测试要求](#测试要求)

---

## 行为准则

本项目采用 [Contributor Covenant](CODE_OF_CONDUCT.md) 行为准则。参与本项目即表示你同意遵守其条款。

---

## 如何贡献

### 报告Bug

在提交Bug报告前，请先搜索现有的Issues，确保问题尚未被报告。

**Bug报告应包含**:

- 清晰的标题
- 详细的描述
- 重现步骤
- 预期行为
- 实际行为
- 环境信息（Python版本、操作系统等）
- 错误日志

### 建议功能

我们欢迎新功能建议！请在Issue中：

- 描述功能的用途
- 解释为什么需要这个功能
- 提供使用范例

### 提交Pull Request

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 开发设置

### 环境要求

- Python 3.8+
- Git
- 虚拟环境工具

### 安装开发环境

```bash
# 克隆仓库
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行带覆盖率的测试
pytest tests/ --cov=paddleocr_toolkit --cov-report=html

# 运行特定测试
pytest tests/test_ocr_engine.py -v
```

---

## 提交指南

### Commit消息格式

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具变更

**范例**:

```
feat(ocr): add support for formula recognition

Implement PP-FormulaNet integration for mathematical
formula recognition in documents.

Closes #123
```

---

## 代码规范

### Python代码风格

遵循 [PEP 8](https://pep8.org/) 规范，使用以下工具：

```bash
# 代码格式化
black paddleocr_toolkit/ tests/

# 导入排序
isort paddleocr_toolkit/ tests/

# 代码检查
flake8 paddleocr_toolkit/

# 类型检查
mypy paddleocr_toolkit/
```

### 文档字符串

使用Google风格的docstrings：

```python
def process_image(image_path: str, dpi: int = 150) -> List[OCRResult]:
    """处理单张图片
    
    Args:
        image_path: 图片文件路径
        dpi: 解析度，默认150
        
    Returns:
        OCR结果列表
        
    Raises:
        FileNotFoundError: 图片文件不存在时
        
    Example:
        >>> results = process_image("doc.jpg", dpi=200)
        >>> print(len(results))
        10
    """
    pass
```

### 类型提示

所有公共函数都应该有类型提示：

```python
from typing import List, Optional, Dict

def get_config(path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    pass
```

---

## 测试要求

### 单元测试

所有新功能都必须包含测试：

```python
def test_new_feature():
    """测试新功能"""
    tool = PaddleOCRTool(mode="basic")
    result = tool.new_feature()
    
    assert result is not None
    assert len(result) > 0
```

### 测试覆盖率

- 目标覆盖率：85%+
- 新增代码覆盖率：90%+

```bash
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
```

### 集成测试

对于重要功能，提供端到端测试：

```python
def test_complete_workflow():
    """测试完整工作流程"""
    tool = PaddleOCRTool()
    results, _ = tool.process_pdf("test.pdf")
    text = tool.get_text(results)
    assert len(text) > 0
```

---

## Pull Request检查清单

提交PR前，请确认：

- [ ] 代码通过所有测试
- [ ] 新功能有相应测试
- [ ] 测试覆盖率不降低
- [ ] 代码已格式化 (black, isort)
- [ ] 通过代码检查 (flake8, mypy)
- [ ] 更新了相关文档
- [ ] 添加了docstrings
- [ ] Commit消息符合规范
- [ ] 没有合并冲突

---

## 代码审查流程

1. 自动化检查（CI/CD）
2. 代码审查（至少1人）
3. 测试验证
4. 文档更新确认
5. 合并到主分支

---

## 发布流程

1. 更新版本号
2. 更新CHANGELOG
3. 创建发布标签
4. 触发自动发布

---

## 问题与帮助

- 📧 提交Issue
- 💬 GitHub Discussions
- 📖 查看文档

---

**感谢你的贡献！** 🎉
