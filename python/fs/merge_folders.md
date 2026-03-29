## 功能

文件整理工具：将文件按修改日期分类移动，视频文件单独文件夹。

## 依赖

- Python 3.10+
- 标准库：`os`, `shutil`, `pathlib`, `datetime`, `sys`
- 使用 `uv` 运行（无需额外安装依赖）

## 配置

编辑脚本顶部的配置变量：

```python
src_pattern = r"D:\_images\iPad*"   # 源文件夹模式
dest_base = r"F:\_images\iPad"       # 图片目标文件夹
dest_base_video = r"F:\_videos"  # 视频目标文件夹
```

## 使用方法

### 交互模式

```bash
uv run python merge_folders.py
```

显示菜单后选择操作：
```
1. Copy files (Step 1)
2. Analyze folders (Step 2) - 3 reports
3. Move videos from YYYYMM to video folder (tmp)
4. Move files (Step 4 - remove source if exists)
5. Run Step 1 + 2 (Copy + Analyze)
0. Exit
```

### 命令行模式

```bash
uv run python merge_folders.py 5    # (1 + 2)
```

## 输出文件

Step 2 生成的报告保存在目标文件夹的父目录：

| 文件名 | 说明 |
|--------|------|
| `iPad_by_name.txt` | 按文件夹名称排序 |
| `iPad_by_file_count.txt` | 按文件数量降序排列 |
| `iPad_by_folder_size.txt` | 按文件夹大小降序排列 |

报告内容示例：
```
Folder                        Size    Files  Avg Size/File
----------------------------------------------------------------------
202510                   18.00 GB     4046         4.7 KB
202205                    1.85 GB      228         8.5 KB
202204                    1.13 GB      526         2.2 KB
...
----------------------------------------------------------------------
TOTAL                    27.00 GB     8202         3.4 KB
```

