---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
audio_url: ""
level: "B1"
target: "Listening & Vocabulary"
duration: ""
description: ""
difficulty: "intermediate"
topic: "BBC Learning English"
summary_zh: ""
tags: ["BBC", "Listening", "B1"]
author: "BBC Learning English"
source_url: ""
---

# 【BBC 听力】{{ .Name | title }}

**来源**: BBC Learning English  
**等级**: B1 (Intermediate)  
**时长**: {{ .Params.duration }}  
**学习目标**: {{ .Params.target }}

---

## 课程简介
{{ .Params.description }}

---

## 播放音频

{{< audio "{{ .Params.audio_url }}" >}}

*点击播放按钮收听音频*

---

## 听力原文（Transcript）

<!-- Insert transcript here -->

---

## 重点词汇与短语

| English | 中文释义 | 词性 | 例句 |
|---------|---------|------|------|
| word | 中文 | n./v./adj. | *Context: example sentence from transcript* |

---

## 中文总结
{{ .Params.summary_zh }}

---

## 练习题

1. 根据听力内容，回答以下问题：
   
2. 词汇匹配：将左侧的英语单词与右侧的中文释义连线。

3. 填空练习：根据听到的内容，补全下面的句子。

---

## 学习提示

- 建议先完整听一遍音频，获取整体理解
- 第二遍听时，关注重点词汇和表达方式
- 对照原文检查理解程度
- 模仿语音语调，提升口语表达

---

**标签**: {{ delimit .Params.tags ", " }}
