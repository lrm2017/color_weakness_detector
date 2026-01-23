# OCR答案提取工具使用说明

## 概述

这套工具用于从色弱检测图像中自动识别左下角的答案文字，解决了原始图像被遮挡的问题。通过从网络下载原始图像并使用OCR技术识别答案。

## 工具列表

### 1. 依赖安装工具
- `install_ocr_dependencies.sh` - 安装OCR相关依赖
- `simple_ocr_test.py` - 简单OCR功能测试

### 2. OCR处理工具
- `universal_ocr_tool.py` - **推荐使用** 通用OCR答案提取工具
- `final_ocr_processor.py` - 针对李春慧新编优化的OCR工具
- `smart_ocr_extractor.py` - 智能OCR提取工具

### 3. 验证和分析工具
- `validate_ocr_accuracy.py` - 验证OCR准确性
- `ocr_summary.py` - OCR处理结果总结
- `extract_clean_answers.py` - 手动提取清理答案

## 使用步骤

### 第一步：安装依赖

```bash
# 安装系统依赖
./install_ocr_dependencies.sh

# 安装Python依赖
pip install requests pytesseract opencv-python pillow
```

### 第二步：测试OCR功能

```bash
# 测试OCR是否正常工作
python simple_ocr_test.py
```

### 第三步：处理答案文件

```bash
# 使用通用工具处理任意版本的answers.json
python universal_ocr_tool.py "downloaded_images/版本名称/answers.json"

# 例如：
python universal_ocr_tool.py "downloaded_images/李春慧新编/answers.json"
python universal_ocr_tool.py "downloaded_images/俞自萍第六版/answers.json"
```

### 第四步：查看处理结果

```bash
# 查看处理结果总结
python ocr_summary.py "downloaded_images/版本名称/answers.json"
```

## 工具参数说明

### universal_ocr_tool.py 参数

```bash
python universal_ocr_tool.py <json_path> [选项]

参数：
  json_path          answers.json文件路径

选项：
  --no-update       不更新文件，只显示识别结果
  --debug           显示调试信息，包括候选答案
```

### validate_ocr_accuracy.py 参数

```bash
python validate_ocr_accuracy.py <json_path> [选项]

参数：
  json_path          answers.json文件路径

选项：
  --count N         测试前N个已知答案（默认10个）
```

## 处理流程

1. **下载原始图像**：从answers.json中的original_url下载未遮挡的原始图像
2. **图像预处理**：提取左下角区域，应用多种二值化和增强算法
3. **OCR识别**：使用中英文OCR引擎识别文字
4. **答案提取**：从OCR结果中提取可能的答案
5. **答案选择**：基于已知答案模式和出现频次选择最佳答案
6. **结果保存**：更新answers.json文件并备份原文件

## 支持的答案类型

### 动物类
熊猫、兔子、老虎、狼、骆驼、马、牛、羊、金鱼、蝴蝶、蜻蜓、鹅、燕子等

### 物品类
手枪、冲锋枪、军舰、卡车、摩托车、拖拉机、剪刀、壶、高射炮等

### 数字
1-4位数字，如：326、6475、890等

### 字母组合
2-6位大写字母，如：ABC、UN、WHO、CHNA等

### 几何图形
五角星、三角形、圆形、正方形、△、○、□等

### 特殊描述
单色图-红色、单色图-黄色、两颗星星等

## 处理结果

### 成功案例（李春慧新编）
- 总图像数量：60
- 识别完成率：100%
- 动物类：14个
- 物品类：8个  
- 数字类：24个
- 字母类：5个
- 中文词汇：9个

### 文件备份
工具会自动备份原始answers.json文件：
- `.json.backup` - 第一次备份
- `.json.backup2` - 第二次备份
- `.json.backup_final` - 最终处理备份
- `.json.backup_universal` - 通用工具备份

## 故障排除

### 1. OCR识别率低
- 检查原始图像质量
- 尝试不同的预处理参数
- 使用debug模式查看候选答案

### 2. 下载失败
- 检查网络连接
- 验证original_url是否有效
- 增加重试机制

### 3. 依赖问题
```bash
# 重新安装tesseract
sudo apt install tesseract-ocr tesseract-ocr-chi-sim

# 检查语言包
tesseract --list-langs
```

## 扩展使用

### 处理新版本
1. 准备包含original_url的answers.json文件
2. 运行通用OCR工具
3. 根据结果调整答案词典

### 批量处理
```bash
# 处理所有版本
for dir in downloaded_images/*/; do
    if [ -f "$dir/answers.json" ]; then
        echo "处理 $dir"
        python universal_ocr_tool.py "$dir/answers.json"
    fi
done
```

## 注意事项

1. **网络要求**：需要稳定的网络连接下载原始图像
2. **处理时间**：每个图像需要5-10秒处理时间
3. **存储空间**：原始图像会保存在original_images目录中
4. **准确率**：基于测试，准确率约为80-90%
5. **手动验证**：建议对重要答案进行人工验证

## 技术细节

### OCR引擎配置
- 使用Tesseract 5.x版本
- 支持中文简体(chi_sim)和英文(eng)
- 多种PSM模式：6(统一文本块)、7(单行)、8(单词)、13(原始行)

### 图像预处理
- 多区域提取：左下角、右下角、底部中央
- 多种二值化：OTSU、自适应阈值
- 图像增强：高斯模糊、形态学操作
- 多倍放大：3x、4x、5x

### 答案匹配
- 已知答案优先匹配
- 频次统计选择
- 长度和格式验证
- 特殊符号处理