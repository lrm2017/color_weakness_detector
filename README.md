# 色弱图谱识别程序

一个基于 PySide6 和 OpenCV 的色弱测试图谱识别工具，可以识别图片中的冷暖色块，帮助色弱人群进行色觉测试练习。

## 功能特点

- **图库选择**：下拉菜单快速切换不同版本的测试图库
- **图片导航**：上一张、下一张、随机切换
- **练习模式**：支持顺序练习和随机练习两种模式
- **答案验证**：输入答案后自动判断对错，正确自动跳转下一题
- **错题库**：答案错误自动加入错题库，方便针对性复习
- **统计功能**：实时显示正确数、错误数、正确率
- **冷暖色识别**：自动识别图片中的暖色和冷色，圈出少数派颜色块
- **答案遮挡**：内置工具遮挡图片上的答案区域

## 安装

### 1. 克隆项目

```bash
git clone git@github.com:lrm2017/color_weakness_detector.git
cd color_weakness_detector
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动 GUI 程序

```bash
source venv/bin/activate
python gui_app.py
```

**操作说明**：
1. 从下拉菜单选择测试图库
2. 选择练习模式（顺序/随机）
3. 在输入框输入答案，按回车或点击"提交答案"
4. 答案正确自动跳转下一题，错误会显示正确答案并自动加入错题库
5. 可随时点击"显示答案"查看标准答案
6. 点击"重置统计"清空正确/错误计数

### 命令行模式

```bash
python color_detector.py <图片路径> [-o 输出路径] [--min-area 最小面积] [--show]
```

参数说明：
- `-o, --output`：指定输出文件路径
- `--min-area`：最小色块面积（默认100像素），用于过滤噪点
- `--show`：显示结果窗口

### 下载测试图片

```bash
python image_crawler.py
```

下载后使用遮挡工具处理答案区域：

```bash
python mask_fixed.py
```

## 项目结构

```
color_weakness_detector/
├── gui_app.py           # PySide6 图形界面主程序
├── color_detector.py    # 命令行版本
├── image_crawler.py     # 图片爬虫脚本
├── mask_fixed.py        # 答案区域遮挡工具
├── requirements.txt     # Python 依赖
├── downloaded_images/   # 下载的测试图片
│   ├── 俞自萍第五版/
│   ├── 俞自萍第六版/
│   ├── 王克长第二版/
│   ├── 王克长第三版/
│   ├── 汪润芳第三版/
│   ├── 汪润芳第四版/
│   ├── 李春慧新编/
│   ├── 吴乐正版/
│   ├── 贾永源版/
│   ├── 石原忍版/
│   ├── 空后版/
│   ├── 英文版/
│   └── 错题库/          # 自动收集的错题
└── test_images/         # 本地测试图片
```

## 识别原理

程序使用 HSV 色彩空间进行颜色识别：

**暖色范围**：
- 红色：H 0-10 和 160-180
- 橙色：H 10-25
- 黄色：H 25-40

**冷色范围**：
- 绿色：H 40-80
- 青色：H 80-100
- 蓝色：H 100-130
- 紫色：H 130-160

程序会统计暖色和冷色像素数量，然后：
- 如果暖色居多，用蓝色框圈出冷色块
- 如果冷色居多，用红色框圈出暖色块

## 依赖

- Python 3.8+
- PySide6
- OpenCV (opencv-python)
- NumPy
- requests
- beautifulsoup4

## License

MIT License
