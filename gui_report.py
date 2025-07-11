import os
import base64
import shutil
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QInputDialog, QColorDialog
from PyQt5.QtGui import QColor
from OCC.Core.Graphic3d import Graphic3d_BufferType
from gui_utils import MessageUtils
import sys
import subprocess
import tempfile


class ReportGenerator:
    def __init__(self, parent):
        self.parent = parent
        self.HAS_PILLOW = self.check_pillow()
        self.image_settings = {
            'width': 800,
            'height': 600,
            'background': (255, 255, 255),
            'dpi': 96,
            'text_color': (0, 0, 0),
            'font_size': 20
        }

    def check_pillow(self):
        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont
            return True
        except ImportError:
            return False

    def generateReport(self):
        if not self.parent.result_paths:
            MessageUtils.showErrorMessage(self.parent, "没有可生成报告的结果")
            return

        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("选择报告格式")
        msg_box.setText("请选择报告格式:")

        pdf_btn = msg_box.addButton("PDF格式", QMessageBox.ActionRole)
        html_btn = msg_box.addButton("HTML格式", QMessageBox.ActionRole)
        img_btn = msg_box.addButton("图片格式", QMessageBox.ActionRole)
        separate_img_btn = msg_box.addButton("单独图片", QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton("取消", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == cancel_btn:
            return
        elif msg_box.clickedButton() == pdf_btn:
            self.generatePDFReport(self.getReportFilePath("pdf"))
        elif msg_box.clickedButton() == html_btn:
            self.generateHTMLReport(self.getReportFilePath("html"))
        elif msg_box.clickedButton() == img_btn:
            self.generateImageReport(self.getReportFilePath("png"))
        elif msg_box.clickedButton() == separate_img_btn:
            self.generateSeparateImages()

    def getReportFilePath(self, extension):
        default_name = f"CAD检索报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_filter = {
            "pdf": "PDF文件 (*.pdf)",
            "html": "HTML文件 (*.html)",
            "png": "PNG图片 (*.png)"
        }.get(extension, "所有文件 (*.*)")

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "保存报告",
            f"{default_name}.{extension}",
            file_filter
        )
        return file_path

    def generateSeparateImages(self):
        if not self.HAS_PILLOW:
            MessageUtils.showErrorMessage(self.parent, "生成图片需要Pillow库，请先安装(pip install pillow)")
            return

        # 获取图片尺寸设置
        width, ok = QInputDialog.getInt(
            self.parent, "图片尺寸设置", "图片宽度(像素):",
            self.image_settings['width'], 100, 4000, 50
        )
        if not ok:
            return

        height, ok = QInputDialog.getInt(
            self.parent, "图片尺寸设置", "图片高度(像素):",
            self.image_settings['height'], 100, 4000, 50
        )
        if not ok:
            return

        self.image_settings['width'] = width
        self.image_settings['height'] = height

        # 让用户选择保存目录
        save_dir = QFileDialog.getExistingDirectory(
            self.parent,
            "选择图片保存目录",
            os.path.expanduser('~/Desktop')
        )
        if not save_dir:
            return

        if not os.access(save_dir, os.W_OK):
            MessageUtils.showErrorMessage(
                self.parent,
                f"无法写入目录: {save_dir}\n请选择有写入权限的目录"
            )
            return

        try:
            # 保存查询模型图片
            query_path = os.path.join(save_dir, "query_model.png")
            if self.saveAndResizeCanvasScreenshot(self.parent.mainCanvas, query_path):
                self.parent.logMessage(f"已保存查询模型图片: {query_path}")

            # 保存结果图片
            for i, (path, score, result_class) in enumerate(zip(
                    self.parent.result_paths, self.parent.result_scores, self.parent.result_classes)):
                canvas_idx = i % 8
                canvas = self.parent.canvases[canvas_idx]
                img_name = f"result_{i + 1}_{result_class}_{score:.2f}percent.png"
                dest_path = os.path.join(save_dir, img_name)

                if self.saveAndResizeCanvasScreenshot(canvas, dest_path):
                    self.parent.logMessage(f"已保存结果图片: {dest_path}")

            # 打开保存目录
            self.openFolder(save_dir)
            MessageUtils.showInfoMessage(self.parent, f"图片已保存到:\n{save_dir}")

        except Exception as e:
            MessageUtils.showErrorMessage(self.parent, f"保存图片时出错: {str(e)}")

    def saveAndResizeCanvasScreenshot(self, canvas, file_path):
        """保存并调整画布截图尺寸"""
        try:
            from PIL import Image as PILImage

            # 先保存原始截图
            temp_path = os.path.join(self.parent.temp_dir, "temp_screenshot.png")
            if not self.saveCanvasScreenshot(canvas, temp_path):
                return False

            # 打开并调整尺寸
            img = PILImage.open(temp_path)
            img = img.resize((self.image_settings['width'], self.image_settings['height']), PILImage.LANCZOS)
            img.save(file_path)

            # 删除临时文件
            try:
                os.remove(temp_path)
            except:
                pass

            return True
        except Exception as e:
            self.parent.logMessage(f"调整图片尺寸时出错: {str(e)}")
            return False

    def saveCanvasScreenshot(self, canvas, file_path):
        """直接保存画布截图，不添加任何额外内容"""
        max_retries = 3
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 保存截图
                view = canvas._display.View
                view.Dump(file_path, Graphic3d_BufferType.Graphic3d_BT_RGB)

                # 验证文件是否创建成功
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return True

            except Exception as e:
                if attempt == max_retries - 1:  # 最后一次尝试失败
                    self.parent.logMessage(f"无法保存图片 {file_path}: {str(e)}")
                time.sleep(retry_delay)

        return False

    def openFolder(self, path):
        """打开保存目录"""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            self.parent.logMessage(f"打开文件夹失败: {str(e)}")

    def getImageSettings(self):
        # 获取图片宽度
        width, ok = QInputDialog.getInt(
            self.parent, "图片设置", "图片宽度(像素):",
            self.image_settings['width'], 100, 4000, 50
        )
        if not ok:
            return False
        self.image_settings['width'] = width

        # 获取图片高度
        height, ok = QInputDialog.getInt(
            self.parent, "图片设置", "图片高度(像素):",
            self.image_settings['height'], 100, 4000, 50
        )
        if not ok:
            return False
        self.image_settings['height'] = height

        # 获取DPI设置
        dpi, ok = QInputDialog.getInt(
            self.parent, "图片设置", "图片DPI(分辨率):",
            self.image_settings['dpi'], 72, 600, 1
        )
        if not ok:
            return False
        self.image_settings['dpi'] = dpi

        # 获取字体大小
        font_size, ok = QInputDialog.getInt(
            self.parent, "图片设置", "文字大小:",
            self.image_settings['font_size'], 8, 72, 1
        )
        if not ok:
            return False
        self.image_settings['font_size'] = font_size

        # 获取背景颜色
        color = QColor(*self.image_settings['background'])
        color = QColorDialog.getColor(color, self.parent, "选择背景颜色")
        if not color.isValid():
            return False
        self.image_settings['background'] = (color.red(), color.green(), color.blue())

        # 获取文字颜色
        text_color = QColor(*self.image_settings['text_color'])
        text_color = QColorDialog.getColor(text_color, self.parent, "选择文字颜色")
        if not text_color.isValid():
            return False
        self.image_settings['text_color'] = (text_color.red(), text_color.green(), text_color.blue())

        return True

    def processAndSaveImage(self, src_path, dest_path, caption=""):
        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont

            # 打开原始截图
            img = PILImage.open(src_path)

            # 创建新图像
            new_img = PILImage.new(
                'RGB',
                (self.image_settings['width'], self.image_settings['height']),
                color=self.image_settings['background']
            )

            # 计算缩放比例
            img_ratio = img.width / img.height
            new_ratio = self.image_settings['width'] / self.image_settings['height']

            if img_ratio > new_ratio:
                # 以宽度为准
                new_width = self.image_settings['width'] - 40  # 留出边距
                new_height = int(new_width / img_ratio)
            else:
                # 以高度为准
                new_height = self.image_settings['height'] - 100  # 留出文字空间
                new_width = int(new_height * img_ratio)

            # 缩放图像
            resized_img = img.resize((new_width, new_height), PILImage.LANCZOS)

            # 计算位置居中
            x = (self.image_settings['width'] - new_width) // 2
            y = (self.image_settings['height'] - new_height - 60) // 2  # 为文字留出空间

            # 粘贴图像
            new_img.paste(resized_img, (x, y))

            # 添加文字说明
            if caption:
                draw = ImageDraw.Draw(new_img)
                try:
                    font = ImageFont.truetype("arial.ttf", self.image_settings['font_size'])
                except:
                    font = ImageFont.load_default()

                # 兼容新旧Pillow版本
                try:
                    # 新版本Pillow的写法
                    from PIL import ImageFont
                    bbox = draw.textbbox((0, 0), caption, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except:
                    # 旧版本Pillow的写法
                    text_width, text_height = draw.textsize(caption, font=font)

                # 分割多行文本
                lines = caption.split('\n')
                line_height = text_height // len(lines)
                total_text_height = len(lines) * line_height

                # 计算文字位置
                text_y = self.image_settings['height'] - total_text_height - 20

                # 绘制每行文字
                for i, line in enumerate(lines):
                    try:
                        # 新版本Pillow的写法
                        bbox = draw.textbbox((0, 0), line, font=font)
                        line_width = bbox[2] - bbox[0]
                    except:
                        # 旧版本Pillow的写法
                        line_width = draw.textsize(line, font=font)[0]

                    text_x = (self.image_settings['width'] - line_width) // 2
                    draw.text((text_x, text_y + i * line_height), line,
                              fill=self.image_settings['text_color'], font=font)

            # 保存图像
            new_img.save(dest_path, dpi=(self.image_settings['dpi'], self.image_settings['dpi']))
            return True

        except Exception as e:
            self.parent.logMessage(f"处理图片时出错: {str(e)}")
            import traceback
            self.parent.logMessage(traceback.format_exc())
            return False

    def generatePDFReport(self, file_path):
        if not file_path:
            return

        report_temp_dir = os.path.join(self.parent.temp_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(report_temp_dir, exist_ok=True)

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            title = Paragraph("CAD检索报告", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"<b>查询类别:</b> {self.parent.current_class}", styles['Normal']))
            story.append(Paragraph(f"<b>检索时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"<b>总结果数:</b> {len(self.parent.result_paths)}", styles['Normal']))
            story.append(Spacer(1, 12))

            try:
                temp_img_path = os.path.join(report_temp_dir, f"query_{os.getpid()}.png")
                if self.saveCanvasScreenshot(self.parent.mainCanvas, temp_img_path):
                    img = Image(temp_img_path, width=6 * inch, height=4.5 * inch)
                    story.append(img)
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph("无法生成查询模型截图", styles['Normal']))
            except Exception as e:
                self.parent.logMessage(f"生成查询模型截图时出错: {str(e)}")
                story.append(Paragraph("查询模型截图生成失败", styles['Normal']))

            story.append(Paragraph("<b>检索结果:</b>", styles['Heading2']))
            story.append(Spacer(1, 12))

            for i, (path, score, result_class) in enumerate(
                    zip(self.parent.result_paths, self.parent.result_scores, self.parent.result_classes)):
                story.append(Paragraph(f"<b>结果 {i + 1}:</b>", styles['Heading3']))
                story.append(Paragraph(f"<b>文件:</b> {os.path.basename(path)}", styles['Normal']))
                story.append(Paragraph(f"<b>相似度:</b> {score:.2f}%", styles['Normal']))
                story.append(Paragraph(f"<b>类别:</b> {result_class}", styles['Normal']))
                match_status = "匹配" if result_class == self.parent.current_class else "不匹配"
                status_color = colors.green if result_class == self.parent.current_class else colors.red
                story.append(Paragraph(f"<b>匹配状态:</b> <font color='{status_color}'>{match_status}</font>",
                                       styles['Normal']))

                try:
                    canvas_idx = i % 8
                    canvas = self.parent.canvases[canvas_idx]

                    temp_result_img_path = os.path.join(report_temp_dir, f"result_{os.getpid()}_{i}.png")
                    if self.saveCanvasScreenshot(canvas, temp_result_img_path):
                        img = Image(temp_result_img_path, width=4 * inch, height=3 * inch)
                        story.append(img)
                    else:
                        story.append(Paragraph("无法生成结果截图", styles['Normal']))
                except Exception as e:
                    self.parent.logMessage(f"生成结果截图时出错: {str(e)}")
                    story.append(Paragraph("结果截图生成失败", styles['Normal']))

                story.append(Spacer(1, 12))

                if i < len(self.parent.result_paths) - 1:
                    story.append(PageBreak())

            try:
                doc.build(story)
                self.parent.logMessage(f"PDF报告已生成: {file_path}")
            except Exception as e:
                MessageUtils.showErrorMessage(self.parent, f"生成PDF报告时出错: {str(e)}")
        finally:
            try:
                shutil.rmtree(report_temp_dir, ignore_errors=True)
            except Exception as e:
                self.parent.logMessage(f"清理临时文件时出错: {str(e)}")

    def generateHTMLReport(self, file_path):
        if not file_path:
            return

        report_temp_dir = os.path.join(self.parent.temp_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(report_temp_dir, exist_ok=True)

        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CAD检索报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    h3 {{ color: #16a085; }}
                    .result {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                    .match {{ background-color: #e8f8f5; }}
                    .no-match {{ background-color: #fdedec; }}
                    .info {{ margin-bottom: 5px; }}
                    .image-container {{ margin-top: 10px; }}
                    img {{ max-width: 600px; max-height: 450px; border: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <h1>CAD检索报告</h1>

                <div class="info"><strong>查询类别:</strong> {self.parent.current_class}</div>
                <div class="info"><strong>检索时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div class="info"><strong>总结果数:</strong> {len(self.parent.result_paths)}</div>

                <h2>查询模型</h2>
                <div class="image-container">
            """

            try:
                temp_img_path = os.path.join(report_temp_dir, f"query_{os.getpid()}.png")
                if self.saveCanvasScreenshot(self.parent.mainCanvas, temp_img_path):
                    with open(temp_img_path, 'rb') as img_file:
                        img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    html_content += f'<img src="data:image/png;base64,{img_base64}" alt="查询模型">'
                else:
                    html_content += '<p>无法生成查询模型截图</p>'
            except Exception as e:
                self.parent.logMessage(f"生成查询模型截图时出错: {str(e)}")
                html_content += '<p>查询模型截图生成失败</p>'

            html_content += """
                </div>

                <h2>检索结果</h2>
            """

            for i, (path, score, result_class) in enumerate(
                    zip(self.parent.result_paths, self.parent.result_scores, self.parent.result_classes)):
                match_class = "match" if result_class == self.parent.current_class else "no-match"

                html_content += f"""
                <div class="result {match_class}">
                    <h3>结果 {i + 1}</h3>
                    <div class="info"><strong>文件:</strong> {os.path.basename(path)}</div>
                    <div class="info"><strong>相似度:</strong> {score:.2f}%</div>
                    <div class="info"><strong>类别:</strong> {result_class}</div>
                    <div class="info"><strong>匹配状态:</strong> {'匹配' if result_class == self.parent.current_class else '不匹配'}</div>
                    <div class="image-container">
                """

                try:
                    canvas_idx = i % 8
                    canvas = self.parent.canvases[canvas_idx]

                    temp_result_img_path = os.path.join(report_temp_dir, f"result_{os.getpid()}_{i}.png")
                    if self.saveCanvasScreenshot(canvas, temp_result_img_path):
                        with open(temp_result_img_path, 'rb') as img_file:
                            img_data = img_file.read()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        html_content += f'<img src="data:image/png;base64,{img_base64}" alt="结果 {i + 1}">'
                    else:
                        html_content += '<p>无法生成结果截图</p>'
                except Exception as e:
                    self.parent.logMessage(f"生成结果截图时出错: {str(e)}")
                    html_content += '<p>结果截图生成失败</p>'

                html_content += """
                    </div>
                </div>
                """
            html_content += """
            </body>
            </html>
            """

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.parent.logMessage(f"HTML报告已生成: {file_path}")
        finally:
            try:
                shutil.rmtree(report_temp_dir, ignore_errors=True)
            except Exception as e:
                self.parent.logMessage(f"清理临时文件时出错: {str(e)}")

    def generateImageReport(self, file_path):
        if not file_path:
            return

        if not self.HAS_PILLOW:
            MessageUtils.showErrorMessage(self.parent, "生成图片报告需要Pillow库，请先安装(pip install pillow)")
            return

        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont
        except ImportError:
            MessageUtils.showErrorMessage(self.parent, "无法导入Pillow库")
            return

        try:
            report_temp_dir = os.path.join(self.parent.temp_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(report_temp_dir, exist_ok=True)

            query_img_path = os.path.join(report_temp_dir, "query.png")
            if not self.saveCanvasScreenshot(self.parent.mainCanvas, query_img_path):
                raise Exception("无法生成查询模型截图")

            result_img_paths = []
            for i, path in enumerate(self.parent.result_paths):
                canvas_idx = i % 8
                canvas = self.parent.canvases[canvas_idx]
                img_path = os.path.join(report_temp_dir, f"result_{i}.png")
                if self.saveCanvasScreenshot(canvas, img_path):
                    result_img_paths.append(img_path)

            img_width = 800
            row_height = 200
            padding = 20
            title_height = 50

            total_height = title_height + (len(self.parent.result_paths) + 1) * row_height

            final_img = PILImage.new('RGB', (img_width, total_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(final_img)

            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            title = f"CAD检索报告 - 查询: {self.parent.current_class}"
            draw.text((padding, padding), title, fill=(0, 0, 0), font=font)

            query_img = PILImage.open(query_img_path)
            query_img = query_img.resize((img_width - 2 * padding, row_height - padding))
            final_img.paste(query_img, (padding, title_height))
            draw.text((padding, title_height + row_height - 30),
                      "查询模型", fill=(0, 0, 255), font=font)

            for i, img_path in enumerate(result_img_paths):
                y_pos = title_height + (i + 1) * row_height
                result_img = PILImage.open(img_path)
                result_img = result_img.resize((img_width - 2 * padding, row_height - padding))
                final_img.paste(result_img, (padding, y_pos))

                info = (f"结果 {i + 1}: 相似度 {self.parent.result_scores[i]:.2f}% - "
                        f"类别: {self.parent.result_classes[i]} - "
                        f"{'匹配' if self.parent.result_classes[i] == self.parent.current_class else '不匹配'}")
                text_color = (0, 128, 0) if self.parent.result_classes[i] == self.parent.current_class else (255, 0, 0)
                draw.text((padding, y_pos + row_height - 30), info, fill=text_color, font=font)

            final_img.save(file_path)
            self.parent.logMessage(f"图片报告已生成: {file_path}")

        except Exception as e:
            MessageUtils.showErrorMessage(self.parent, f"生成图片报告时出错: {str(e)}")
        finally:
            try:
                shutil.rmtree(report_temp_dir, ignore_errors=True)
            except Exception as e:
                self.parent.logMessage(f"清理临时文件时出错: {str(e)}")

    def saveCanvasScreenshot(self, canvas, file_path):
        max_retries = 3
        retry_delay = 0.5

        file_path = os.path.normpath(file_path)

        for attempt in range(max_retries):
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                abs_path = os.path.abspath(file_path)

                view = canvas._display.View
                view.Dump(abs_path, Graphic3d_BufferType.Graphic3d_BT_RGB)

                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                    return True
                else:
                    self.parent.logMessage(f"截图文件创建失败: {abs_path}")

            except Exception as e:
                self.parent.logMessage(f"截图保存失败(尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        return False