import pygame
import numpy as np
import sys
import os
import soundfile as sf
import tkinter as tk
from tkinter import filedialog

# ---------- 配置 ----------
WIDTH, HEIGHT = 1280, 720
FPS = 165
FFT_N = 2048
BARS = 128
SCALE_FACTOR = 75  # 频柱缩放
EXPONENT = 0.5  # 指数参数
# -------------------------

root = tk.Tk()
root.withdraw()

FILE_PATH = filedialog.askopenfilename(
    title="选择音乐文件",
    filetypes=[("音频文件", "*.mp3 *.wav *.ogg *.flac"), ("所有文件", "*.*")]
)
if not FILE_PATH:
    print("未选择文件，程序退出")
    sys.exit(0)

if not os.path.exists(FILE_PATH):
    print(f"错误：找不到 {FILE_PATH}")
    sys.exit(1)

data, samplerate = sf.read(FILE_PATH, dtype='float32')  # 预加载
if data.ndim == 2:
    data = data.mean(axis=1)  # 平均声道

total_samples = len(data)
chunk_size = int(samplerate / FPS)  # 每帧样本数

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("简单音频可视化")
clock = pygame.time.Clock()

pygame.mixer.music.load(FILE_PATH)  # 播放
pygame.mixer.music.play()

running = True
paused = False
current_pos = 0  # 当前样本位置

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                if paused:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
                paused = not paused

    if not pygame.mixer.music.get_busy() and not paused:
        running = False

    # ========== 获取当前帧音频样本 ==========
    if not paused:
        start = current_pos
        end = min(start + FFT_N, total_samples)
        frame_data = data[start:end]

        if len(frame_data) < FFT_N: # 补零
            frame_data = np.pad(frame_data, (0, FFT_N - len(frame_data)))

        current_pos += chunk_size
        if current_pos >= total_samples:
            current_pos = total_samples  # 防越界

        fft_data = np.fft.rfft(frame_data)  # fft
        mag = np.abs(fft_data)[:FFT_N//2]

        step = len(mag) // BARS # 分桶
        bars = [mag[i*step:(i+1)*step].mean() if step > 0 else 0 for i in range(BARS)]

    else:
        bars = [0] * BARS  # 暂停时清零

    # ========== 绘制 ==========
    screen.fill((0, 0, 0))

    bar_width = WIDTH // BARS
    for i, h in enumerate(bars):
        #height = int(h * SCALE_FACTOR)  # 线性缩放
        height = int((h ** EXPONENT) * SCALE_FACTOR)  # 指数缩放
        height = min(height, HEIGHT - 20)  # 限高
        x = i * bar_width
        y = HEIGHT - height
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width - 1, height))
    pygame.display.flip()
    clock.tick(FPS)

pygame.mixer.music.stop()   #清理
pygame.quit()