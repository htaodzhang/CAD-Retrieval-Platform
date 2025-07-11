# CAD Retrieval Platform / CAD模型检索平台

This is a professional CAD engineering model retrieval system developed based on PyQt5 and PythonOCC. Its core functionality enables intelligent 3D model search through feature file (.npy) comparison. The system supports STEP format files.

这是一个基于PyQt5和PythonOCC开发的专业CAD工程模型检索系统，主要功能是通过特征文件(.npy)比对实现三维模型的智能搜索。系统支持STEP格式文件。

![image-20250701095628547](https://github.com/BrepMaster/CAD-Retrieval-Platform/raw/main/1.png)

📦 Download (Windows EXE version):
链接: https://pan.baidu.com/s/1Zlv-a_pnKLEtgZ8jZM9IzA?pwd=ab8a
提取码: ab8a

**温馨提示**
如果本项目对您有所帮助，欢迎点击右上角⭐Star支持！
如需在学术或商业用途中使用本项目，请注明出处。

## Table of Contents / 目录

- [Overview / 概述](#overview--概述)
- [Key Features / 核心功能](#key-features--核心功能)  
- [Usage Guide / 使用指南](#usage-guide--使用指南)
- [Report Generation / 报告生成](#report-generation--报告生成)
- [Project Structure / 项目结构](#project-structure--项目结构)
- [Contribution / 参与贡献](#contribution--参与贡献)
- [License / 许可证](#license--许可证)

## Overview / 概述

A professional CAD model retrieval system developed with PyQt5 and PythonOCC, supporting similarity search based on geometric features with comprehensive visualization and reporting capabilities.

基于PyQt5和PythonOCC开发的专业CAD模型检索系统，支持基于几何特征的相似度搜索，提供完整的可视化与报告生成功能。

## Key Features / 核心功能

### Core Functionality / 核心功能

| Feature           | Description                         | 功能描述            |
| ----------------- | ----------------------------------- | ------------------- |
| Bilingual UI      | Seamless EN/CN language switching   | 无缝中英文界面切换  |
| Model Support     | Full STEP file format support       | 完整STEP格式支持    |
| Advanced Search   | Euclidean/Cosine similarity metrics | 欧式/余弦相似度度量 |
| Flexible Database | Single file or directory mode       | 单文件/目录双模式   |

### Visualization & Reporting / 可视化与报告

```text
✅ Interactive 3D Viewer - Real-time model inspection
✅ Smart Pagination - Browse results efficiently  
✅ Color Coding - Instant visual feedback on matches
✅ Multi-format Reports - PDF/HTML/Image exports
✅ Search History - Replay previous queries

✅ 交互式3D查看器 - 实时模型检视
✅ 智能分页系统 - 高效浏览结果
✅ 颜色编码 - 匹配结果视觉反馈
✅ 多格式报告 - PDF/HTML/图片导出
✅ 检索历史 - 重现过往查询
```

## Usage Guide / 使用指南

### Basic Workflow / 基本流程

1. **Upload Model** - Load STEP file  
   **上传模型** - 加载STEP文件
2. **Load Features** - Provide feature vector  
   **加载特征** - 提供特征向量
3. **Configure Database** - Set search parameters  
   **配置数据库** - 设置搜索参数
4. **Execute Search** - Run similarity analysis  
   **执行检索** - 运行相似度分析
5. **Generate Report** - Export results  
   **生成报告** - 导出结果

### Advanced Features / 高级功能

- **Color Customization**: Adjust match/mismatch colors  
  **颜色定制**: 调整匹配/不匹配颜色
- **Display Modes**: Switch between 3D/text views  
  **显示模式**: 3D/文本视图切换
- **Batch Processing**: Handle multiple queries  
  **批处理**: 多查询处理

## Report Generation / 报告生成

### Supported Formats / 支持格式

| Format | Features                                 | 特性             |
| ------ | ---------------------------------------- | ---------------- |
| PDF    | Professional layout with vector graphics | 专业排版矢量图形 |
| HTML   | Interactive web format                   | 交互式网页格式   |
| PNG    | High-res image export                    | 高分辨率图片导出 |

## Project Structure / 项目结构

```
├── gui_core.py           # Main application logic / 主应用逻辑
├── gui_report.py         # Report generation / 报告生成
├── gui_utils.py          # UI utilities / UI工具
├── gui_widgets.py        # Custom widgets / 自定义组件
├── similarity_calculator.py # Core algorithms / 核心算法
├── main.py               # Entry point / 程序入口
└── README.md             # Documentation / 说明文档
```

## Contribution / 参与贡献

We welcome contributions through:  
欢迎通过以下方式参与贡献：

1. **Issue Reporting** - Bug reports and suggestions  
   **问题反馈** - 错误报告与建议
2. **Code Contributions** - Fork and submit PRs  
   **代码贡献** - Fork并提交PR
3. **Documentation** - Improve docs and translations  
   **文档完善** - 改进文档与翻译

## License / 许可证

MIT License

---

> For technical support or commercial inquiries, please contact the development team.  
> 如需技术支持或商业合作，请联系开发团队。
