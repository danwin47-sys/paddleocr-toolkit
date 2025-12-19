# Shell 自動補全

PaddleOCR Toolkit 支援 Bash 和 Zsh 的命令列自動補全。

---

## 📦 安裝

### Bash

#### 方法1：系統級安裝

```bash
sudo cp completion/paddleocr-completion.bash /etc/bash_completion.d/
```

#### 方法2：使用者級安裝

在 `~/.bashrc` 中加入：

```bash
source /path/to/paddleocr-toolkit/completion/paddleocr-completion.bash
```

然後重新載入：

```bash
source ~/.bashrc
```

---

### Zsh

#### 方法1：系統級安裝

```bash
sudo cp completion/_paddleocr /usr/share/zsh/site-functions/
```

#### 方法2：使用者級安裝

在 `~/.zshrc` 中加入：

```bash
fpath=(~/path/to/paddleocr-toolkit/completion $fpath)
autoload -U compinit && compinit
```

然後重新載入：

```bash
source ~/.zshrc
```

---

## ✨ 功能

### 命令補全

輸入 `paddleocr` 後按 `Tab`：

```bash
$ paddleocr [Tab]
init       config     process    benchmark  validate   --version  --help
```

---

### 選項補全

#### Process 命令

```bash
$ paddleocr process --mode [Tab]
basic    hybrid    structure

$ paddleocr process --format [Tab]
md    json    html    txt    xlsx
```

#### Benchmark 命令

```bash
$ paddleocr benchmark [Tab]
# 自動補全 .pdf 檔案
document.pdf    report.pdf    test.pdf
```

#### Validate 命令

```bash
$ paddleocr validate [Tab]
# 自動補全 .json 檔案
result.json    ocr_output.json

$ paddleocr validate result.json [Tab]
# 自動補全 .txt 檔案
ground_truth.txt    reference.txt
```

---

### 檔案路徑補全

所有命令都支援智慧檔案路徑補全：

```bash
$ paddleocr init [Tab]
# 補全目錄名稱
my_project/    documents/    output/

$ paddleocr process [Tab]
# 補全所有檔案
file.pdf    image.png    document.docx
```

---

## 🔧 自訂補全

### 新增自訂模式

編輯補全指令碼，在 `modes` 陣列中新增：

```bash
local modes="basic hybrid structure custom_mode"
```

### 新增自訂格式

編輯補全指令碼，在 `formats` 中新增：

```bash
local formats="md json html txt xlsx csv xml"
```

---

## 🐛 疑難排解

### Bash 補全不工作

1. 確認 `bash-completion` 已安裝：

   ```bash
   apt-get install bash-completion  # Debian/Ubuntu
   brew install bash-completion@2   # macOS
   ```

2. 檢查補全是否啟用：

   ```bash
   type _comp
   ```

### Zsh 補全不工作

1. 確認 `compinit` 已載入：

   ```bash
   # 在 ~/.zshrc 中
   autoload -U compinit && compinit
   ```

2. 清除補全快取：

   ```bash
   rm -f ~/.zcompdump*
   compinit
   ```

---

## 📝 支援的命令

| 命令 | 補全內容 |
|------|---------|
| `init` | 目錄名稱 |
| `config` | `--show` 選項和設定檔 |
| `process` | `--mode`, `--format`, 檔案 |
| `benchmark` | PDF檔案, `--output` |
| `validate` | JSON檔案, TXT檔案 |

---

**更多資訊**: [CLI 命令檔案](CLI_COMMANDS.md)
