import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re


class BitmapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("OLED 位图编辑器 (最大128x64)")
        self.root.resizable(True, True)

        # 默认分辨率
        self.width = 128
        self.height = 64
        self.pixel_size = 8  # 每个像素的绘制大小

        # 存储图像数据（二维列表：0=灭, 1=亮）
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]

        self.setup_ui()

    def setup_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 分辨率输入（仅保留输入框）
        tk.Label(control_frame, text="分辨率:").pack(side=tk.LEFT)
        tk.Label(control_frame, text="宽:").pack(side=tk.LEFT)
        self.custom_width = tk.StringVar(value="128")
        tk.Entry(control_frame, textvariable=self.custom_width, width=5).pack(side=tk.LEFT)
        tk.Label(control_frame, text="高:").pack(side=tk.LEFT)
        self.custom_height = tk.StringVar(value="64")
        tk.Entry(control_frame, textvariable=self.custom_height, width=5).pack(side=tk.LEFT)

        # 设置按钮
        tk.Button(control_frame, text="应用分辨率", command=self.apply_resolution).pack(side=tk.LEFT, padx=5)

        # 控制按钮
        tk.Button(control_frame, text="清屏", command=self.clear_screen).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="反转", command=self.invert_pixels).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)

        # 画布区域
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # 缓存拖动状态
        self.last_x = None
        self.last_y = None
        self.is_drawing = False

        # 初始化画布
        self.redraw_canvas()

    def apply_resolution(self):
        try:
            w = int(self.custom_width.get())
            h = int(self.custom_height.get())
            if not (1 <= w <= 128 and 1 <= h <= 64):
                raise ValueError("宽应在 1~128，高应在 1~64")
            # 确保高度是8的倍数
            if h % 8 != 0:
                new_h = (h // 8) * 8
                if new_h == 0:
                    new_h = 8
                messagebox.showinfo("提示", f"高度自动调整为 {new_h} (必须为8的倍数)")
                h = new_h
                self.custom_height.set(str(h))

            # 保存当前像素数据
            old_pixels = self.pixels
            old_width = self.width
            old_height = self.height

            # 创建新的像素矩阵（初始化为0/黑色）
            new_pixels = [[0 for _ in range(w)] for _ in range(h)]

            # 复制重叠区域的像素
            for y in range(min(h, old_height)):
                for x in range(min(w, old_width)):
                    new_pixels[y][x] = old_pixels[y][x]

            # 更新属性
            self.width = w
            self.height = h
            self.pixels = new_pixels

            self.redraw_canvas()
        except Exception as e:
            messagebox.showerror("输入错误", f"无效的分辨率: {e}")

    def redraw_canvas(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        # 计算合适的像素尺寸
        if cw <= 1 or ch <= 1:
            return

        px = cw // self.width
        py = ch // self.height
        self.pixel_size = min(px, py, 20)
        self.pixel_size = max(self.pixel_size, 1)

        # 居中偏移
        offset_x = (cw - self.width * self.pixel_size) // 2
        offset_y = (ch - self.height * self.pixel_size) // 2

        for y in range(self.height):
            for x in range(self.width):
                color = "white" if self.pixels[y][x] else "black"
                self.canvas.create_rectangle(
                    offset_x + x * self.pixel_size,
                    offset_y + y * self.pixel_size,
                    offset_x + (x + 1) * self.pixel_size,
                    offset_y + (y + 1) * self.pixel_size,
                    fill=color,
                    outline="gray20",
                    tags=f"pixel_{x}_{y}"
                )

    def on_canvas_click(self, event):
        self.is_drawing = True
        self.update_pixel(event)

    def on_canvas_drag(self, event):
        if self.is_drawing:
            self.update_pixel(event)

    def on_drag_stop(self, event):
        self.is_drawing = False
        self.last_x = None
        self.last_y = None

    def update_pixel(self, event):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        offset_x = (cw - self.width * self.pixel_size) // 2
        offset_y = (ch - self.height * self.pixel_size) // 2

        x = (event.x - offset_x) // self.pixel_size
        y = (event.y - offset_y) // self.pixel_size

        if 0 <= x < self.width and 0 <= y < self.height:
            # 避免重复绘制同一位置
            if self.last_x == x and self.last_y == y:
                return
            self.last_x, self.last_y = x, y

            # 设置为当前画笔状态（toggle）
            new_val = 1 if self.pixels[y][x] == 0 else 0
            self.pixels[y][x] = new_val

            # 更新显示
            color = "white" if new_val else "black"
            self.canvas.itemconfig(f"pixel_{x}_{y}", fill=color)

    def on_canvas_resize(self, event):
        self.redraw_canvas()

    def clear_screen(self):
        self.pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.redraw_canvas()

    def invert_pixels(self):
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[y][x] ^= 1
        self.redraw_canvas()

    def pixels_to_c_array(self):
        """将二维像素数据转换为 C 数组（纵向扫描，每列8像素）
        像素从上至下对应字节的bit0到bit7
        """
        # 计算页数 (高度/8)
        pages = self.height // 8

        data = []
        # 按页处理 (垂直方向)
        for page in range(pages):
            # 每页的起始行
            start_row = page * 8

            # 按列处理 (水平方向)
            for col in range(self.width):
                byte_val = 0
                # 每列8个像素，从上到下
                for bit in range(8):
                    row = start_row + bit
                    if row < self.height and col < self.width:
                        if self.pixels[row][col]:
                            # bit0 (LSB) 对应页的顶部像素，bit7对应底部像素
                            byte_val |= (1 << bit)
                data.append(byte_val)

        return data

    def c_array_to_pixels(self, data, width, height):
        """将C数组数据转换为像素矩阵（纵向扫描）
        像素从上至下对应字节的bit0到bit7
        """
        # 计算页数
        pages = height // 8

        # 验证数据长度
        expected_length = pages * width
        if len(data) < expected_length:
            messagebox.showwarning("警告", f"数据长度不足。期望 {expected_length} 字节，实际 {len(data)} 字节。")

        # 初始化像素矩阵
        pixels = [[0 for _ in range(width)] for _ in range(height)]

        # 按页处理
        for page in range(pages):
            start_row = page * 8

            # 按列处理
            for col in range(width):
                idx = page * width + col
                if idx < len(data):
                    byte_val = data[idx]

                    # 每列8个像素，从上到下
                    for bit in range(8):
                        row = start_row + bit
                        if row < height and col < width:
                            # 检查对应位是否为1 (bit0对应顶部像素)
                            if byte_val & (1 << bit):
                                pixels[row][col] = 1
                            else:
                                pixels[row][col] = 0
                else:
                    # 数据不足，剩余像素设为0
                    for bit in range(8):
                        row = start_row + bit
                        if row < height and col < width:
                            pixels[row][col] = 0

        return pixels

    def export_data(self):
        data = self.pixels_to_c_array()
        hex_strs = [f"0x{b:02x}" for b in data]
        lines = []
        for i in range(0, len(hex_strs), 12):  # 每行12个字节，美观换行
            lines.append(", ".join(hex_strs[i:i + 12]) + ",")
        result = "\n".join(lines)
        if result.endswith(","):
            result = result[:-1]  # 去掉最后一个逗号

        # 新窗口显示并允许复制
        export_window = tk.Toplevel(self.root)
        export_window.title("导出的 C 数组")
        export_window.geometry("600x400")

        text_area = scrolledtext.ScrolledText(export_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_area.insert(tk.END, f"const uint8_t bitmapData[] = {{\n{result}\n}};")
        text_area.config(state=tk.NORMAL)  # 允许选择和复制

        # 添加复制按钮
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(f"const uint8_t bitmapData[] = {{\n{result}\n}};")
            messagebox.showinfo("已复制", "数据已复制到剪贴板")

        button_frame = tk.Frame(export_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="复制到剪贴板", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关闭", command=export_window.destroy).pack(side=tk.RIGHT, padx=5)

    def import_data(self):
        import_window = tk.Toplevel(self.root)
        import_window.title("导入 C 数组数据")
        import_window.geometry("650x320")
        import_window.transient(self.root)
        import_window.grab_set()

        # 分辨率输入区域
        res_frame = tk.Frame(import_window)
        res_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(res_frame, text="数据分辨率:").pack(side=tk.LEFT, padx=5)

        tk.Label(res_frame, text="宽:").pack(side=tk.LEFT, padx=2)
        width_entry = tk.Entry(res_frame, width=5)
        width_entry.pack(side=tk.LEFT, padx=2)
        width_entry.insert(0, "96")

        tk.Label(res_frame, text="高:").pack(side=tk.LEFT, padx=2)
        height_entry = tk.Entry(res_frame, width=5)
        height_entry.pack(side=tk.LEFT, padx=2)
        height_entry.insert(0, "64")

        # 数据输入区域
        text_frame = tk.Frame(import_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10)
        text_area.pack(fill=tk.BOTH, expand=True)

        # 按钮区域
        btn_frame = tk.Frame(import_window)
        btn_frame.pack(pady=5, fill=tk.X, padx=10)

        def do_import():
            try:
                # 获取分辨率
                width = int(width_entry.get())
                height = int(height_entry.get())

                if not (1 <= width <= 128):
                    raise ValueError("宽度必须在 1~128 之间")

                # 高度必须是8的倍数
                if height % 8 != 0:
                    new_height = (height // 8) * 8
                    if new_height == 0:
                        new_height = 8
                    messagebox.showinfo("提示", f"高度已调整为 {new_height} (必须为8的倍数)")
                    height = new_height
                    height_entry.delete(0, tk.END)
                    height_entry.insert(0, str(height))

                if not (1 <= height <= 64):
                    raise ValueError("高度必须在 1~64 之间，且为8的倍数")

                # 获取并解析数据
                raw = text_area.get("1.0", tk.END)
                hex_values = re.findall(r"0x[0-9a-fA-F]{1,2}", raw)

                if not hex_values:
                    raise ValueError("未找到有效的十六进制数据 (格式应为 0x00, 0xFF 等)")

                bytes_data = [int(x, 16) for x in hex_values]

                # 验证数据长度
                expected_length = (height // 8) * width
                if len(bytes_data) != expected_length:
                    if messagebox.askyesno("警告",
                                           f"数据长度不匹配！\n期望: {expected_length} 字节\n实际: {len(bytes_data)} 字节\n是否继续尝试导入？"):
                        # 如果用户确认继续，使用尽可能多的有效数据
                        pass
                    else:
                        return

                # 转换数据为像素矩阵
                pixels = self.c_array_to_pixels(bytes_data, width, height)

                # 更新主界面
                self.width = width
                self.height = height
                self.pixels = pixels
                self.custom_width.set(str(width))
                self.custom_height.set(str(height))

                self.redraw_canvas()
                import_window.destroy()
                messagebox.showinfo("成功", f"成功导入 {width}x{height} 的位图数据")

            except Exception as e:
                messagebox.showerror("导入错误", str(e))

        # 按钮（使用默认样式）
        tk.Button(btn_frame, text="确定", command=do_import, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=import_window.destroy, width=10).pack(side=tk.RIGHT, padx=5)


# 启动程序
if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapEditor(root)
    root.geometry("800x500")
    root.mainloop()