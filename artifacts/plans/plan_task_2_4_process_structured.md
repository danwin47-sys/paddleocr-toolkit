# Task 2.4: 重构 process_structured() - 快速实用方案

> 建立时间：2024-12-14 07:44  
> 状态：📋 规划中  
> 风险等级：🟡 中等  
> 预计时间：30-40 分钟（快速方案）

---

## 🎯 目标

重构 `process_structured()` 方法（167 行），采用**快速实用方案**简化到 < 100 行。

**当前状态**: 167 行（429-594）  
**目标**: < 100 行（减少约 70 行，40% reduction）

---

## 📊 现状分析

### `process_structured()` 方法结构（167 行）

#### 主要逻辑块

1. **初始化**（~10 行）- 验证模式、创建 result_summary
2. **路径处理**（~20 行）- 处理 markdown/json 输出路径
3. **主循环**（~120 行）- 处理每个页面的输出
   - Markdown 输出（~15 行）
   - JSON 输出（~15 行）
   - Excel 输出（~25 行）
   - HTML 输出（~45 行）
4. **最终保存**（~15 行）- 合并 markdown，保存 HTML

---

## 📋 快速重构策略（实用方案）

考虑到时间限制，采用**聚焦关键重复逻辑**的策略：

### 核心问题识别

重复模式最明显的是：

1. **临时目录创建和清理** - 重复 4 次
2. **路径处理逻辑** - markdown/json 重复
3. **文件保存模板** - 类似逻辑重复

### 提取 3 个关键方法

#### 方法 1: `_process_output_with_tempdir()` - 通用临时目录处理

**作用**: 消除临时目录的重复逻辑  
**预计**: ~20 行

```python
def _process_output_with_tempdir(
    self,
    res,  # Structure result object
    save_method_name: str,  # 'save_to_markdown', 'save_to_json', etc.
    glob_pattern: str,  # '*.md', '*.json', etc.
    process_file: Callable  # 处理文件的回调函数
) -> None:
    """使用临时目录处理输出的通用方法"""
    temp_dir = tempfile.mkdtemp()
    try:
        # 调用保存方法
        save_method = getattr(res, save_method_name, None)
        if save_method:
            save_method(save_path=temp_dir)
            # 处理生成的文件
            for file in Path(temp_dir).glob(glob_pattern):
                process_file(file)
    except Exception as e:
        logging.warning(f"{save_method_name} 失败: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
```

#### 方法 2: `_save_structured_markdown()` - Markdown 保存

**作用**: 提取 markdown 合并逻辑  
**预计**: ~15 行

```python
def _save_structured_markdown(
    self,
    all_markdown_content: List[str],
    markdown_output: str,
    result_summary: Dict[str, Any]
) -> None:
    """保存合并后的 Markdown"""
    if all_markdown_content:
        combined = "\n\n---\n\n".join(all_markdown_content)
        with open(markdown_output, 'w', encoding='utf-8') as f:
            f.write(combined)
        result_summary["markdown_files"].append(markdown_output)
        print(f"[OK] Markdown 已保存：{markdown_output}")
```

#### 方法 3: `_save_structured_html()` - HTML 保存

**作用**: 提取 HTML 生成逻辑  
**预计**: ~50 行（HTML 生成代码很长）

---

## 📊 预期成果（快速方案）

### 代码行数变化

| 项目 | 原始 | 重构后 | 减少 |
|------|------|--------|------|
| `process_structured()` | 167 | **~95** | **-72** (-43%) |
| 新增方法 | 0 | **~85** | +85 |
| **净变化** | 167 | **180** | **+13** |

### 代码质量提升

- ✅ **主方法简化**: 167 → 95 行 (43% reduction)
- ✅ **消除重复**: 临时目录处理统一
- ✅ **可读性**: 更清晰的结构
- ✅ **可维护性**: 易于修改输出逻辑

---

## 🎯 执行计划（30-40 分钟）

### 快速实施（考虑时间限制）

**Step 1**: 创建 3 个辅助方法（15 分钟）  
**Step 2**: 简化主方法（10 分钟）  
**Step 3**: 测试验证（5-10 分钟）  
**Step 4**: 提交 Git（5 分钟）

---

## ⚠️ 务实建议

考虑到：

- 你已工作 1.5 小时
- 已完成 3 个重大任务
- 这是第 4 个重构任务

**建议采用快速方案**：

- 只提取最关键的重复逻辑
- 目标 < 100 行即可（不追求极致）
- 保持代码清晰可读

---

## 🎯 成功标准

- ✅ `process_structured()` < 100 行
- ✅ 新增 2-3 个清晰的辅助方法
- ✅ 所有测试通过
- ✅ 功能完全保留

---

*计划建立：2024-12-14 07:44*  
*预计执行时间：30-40 分钟*  
*难度：🟡 中等*  
*方案：快速实用型*
