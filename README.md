# 色弱图谱识别程序

一个基于 PySide6 和 OpenCV 的色弱测试图谱识别工具，可以识别图片中的冷暖色块，帮助色弱人群进行色觉测试练习。

## 功能特点

- **图库浏览**：支持设置图库路径，浏览目录下的所有图片
- **图片导航**：上一张、下一张、随机切换
- **冷暖色识别**：自动识别图片中的暖色（红、橙、黄）和冷色（绿、青、蓝、紫）
- **智能标注**：根据冷暖色比例，自动圈出少数派颜色块
- **答案显示**：支持加载答案文件，点击按钮显示/隐藏答案
- **图片爬虫**：内置爬虫脚本，可从色弱测试网站下载测试图片

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
python image_crawler.py -o ./downloaded_images
```

## 项目结构

```
color_weakness_detector/
├── gui_app.py           # PySide6 图形界面主程序
├── color_detector.py    # 命令行版本
├── image_crawler.py     # 图片爬虫脚本
├── create_test_images.py # 测试图片生成脚本
├── requirements.txt     # Python 依赖
├── downloaded_images/   # 下载的测试图片
│   ├── yuziping5/
│   │   ├── *.jpg
│   │   └── answers.json
│   └── yuziping6/
│       ├── *.jpg
│       └── answers.json
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
