import re
from typing import List, Tuple
import os,sys
from rich.panel import Panel
from rich.console import Console

console = Console()

def parse_time(time_str: str) -> float:
    """将时间字符串转换为秒数"""
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def format_time(seconds: float) -> str:
    """将秒数转换为SRT格式的时间字符串"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_subtitle(subtitle: str, min_length: int = 5) -> List[Tuple[str, float]]:
    """分割中文字幕文本，并记录分割位置的相对百分比"""
    def chinese_char_count(s: str) -> int:
        return len(re.findall(r'[\u4e00-\u9fff]', s))

    def is_chinese_char(char: str) -> bool:
        return '\u4e00' <= char <= '\u9fff'

    result = []
    current = []
    total_length = len(subtitle)
    current_position = 0

    words = subtitle.split()
    for i, word in enumerate(words):
        if i > 0:
            prev_char = words[i-1][-1]
            next_char = word[0]
            if is_chinese_char(prev_char) and is_chinese_char(next_char):
                if (chinese_char_count(''.join(current + [word])) > min_length and 
                    chinese_char_count(' '.join(current)) >= min_length):
                    result.append((' '.join(current), current_position / total_length))
                    current = [word]
                    current_position += len(' '.join(current)) + 1  # +1 for space
                    continue

        current.append(word)
        if i < len(words) - 1:
            current_position += len(word) + 1  # +1 for space
        else:
            current_position += len(word)

    if current:
        result.append((' '.join(current), 1.0))
    
    return result if len(result) > 1 else [(subtitle, 1.0)]



def split_english_subtitle(subtitle: str, split_percentages: List[float]) -> List[str]:
    """根据相对百分比位置切割英文字幕，确保不切断单词"""
    words = subtitle.split()
    result = []
    current = []
    word_index = 0
    total_length = len(subtitle)
    current_length = 0

    for percentage in split_percentages:
        target_length = int(total_length * percentage)
        while word_index < len(words) and current_length < target_length:
            current.append(words[word_index])
            current_length += len(words[word_index]) + 1  # +1 for space
            word_index += 1
        
        if current:
            result.append(' '.join(current))
            current = []

    if current or word_index < len(words):
        result.append(' '.join(current + words[word_index:]))

    return result

def process_srt(chinese_file: str, english_file: str, output_chinese: str, output_english: str):
    with open(chinese_file, 'r', encoding='utf-8') as f:
        chinese_content = f.read()
    with open(english_file, 'r', encoding='utf-8') as f:
        english_content = f.read()

    subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n', re.DOTALL)
    chinese_subtitles = subtitle_pattern.findall(chinese_content)
    english_subtitles = subtitle_pattern.findall(english_content)

    new_chinese_subtitles = []
    new_english_subtitles = []
    subtitle_index = 1

    for (c_index, c_start, c_end, c_text), (e_index, e_start, e_end, e_text) in zip(chinese_subtitles, english_subtitles):
        start_time = parse_time(c_start)
        end_time = parse_time(c_end)
        duration = end_time - start_time

        split_chinese_texts = split_subtitle(c_text.strip())
        
        if len(split_chinese_texts) == 1:
            new_chinese_subtitles.append((subtitle_index, c_start, c_end, split_chinese_texts[0][0]))
            new_english_subtitles.append((subtitle_index, e_start, e_end, e_text.strip()))
            subtitle_index += 1
        else:
            time_per_part = duration / len(split_chinese_texts)
            split_percentages = [percentage for _, percentage in split_chinese_texts[:-1]]  # Exclude the last 1.0
            split_english_texts = split_english_subtitle(e_text.strip(), split_percentages)
            
            for i, ((c_part, _), e_part) in enumerate(zip(split_chinese_texts, split_english_texts)):
                part_start = format_time(start_time + i * time_per_part)
                part_end = format_time(start_time + (i + 1) * time_per_part)
                new_chinese_subtitles.append((subtitle_index, part_start, part_end, c_part))
                new_english_subtitles.append((subtitle_index, part_start, part_end, e_part))
                subtitle_index += 1

    with open(output_chinese, 'w', encoding='utf-8') as f:
        for index, start, end, text in new_chinese_subtitles:
            f.write(f"{index}\n{start} --> {end}\n{text}\n\n")

    with open(output_english, 'w', encoding='utf-8') as f:
        for index, start, end, text in new_english_subtitles:
            f.write(f"{index}\n{start} --> {end}\n{text}\n\n")

# 使用示例
def optimize():
    chinese_file = f'output/trans_subtitles.srt'
    english_file = f'output/src_subtitles.srt'
    output_chinese = f'output/trans_subtitles_optimize.srt'
    output_english = f'output/src_subtitles_optimize.srt'
    
    process_srt(chinese_file, english_file, output_chinese, output_english)
    console.print(Panel("[bold green]🎉📝 中英文分割优化版本 - 字幕生成完成！请在 `output` 文件夹中检查 👀[/bold green]"))
    
if __name__ == "__main__":
    Name = input("测试文件:")
    optimize(Name)

