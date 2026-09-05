# xmuti
## 简介
XMuti是一个基于Python的一个通用文件格式，包含了图像类型数据、文本类型数据等。
一切都以16进制，更快速便携。
## 格式
一般XMuti文件是.xmu（XRing Muti）后缀，并且具体如下：
```xmu
58 4D 55 54 49 00 01
```
这是重要的一点————文件的头部。我们逐步解析。
58 4D 55 54 49是“XMUTI”。然后00 01中的左边的00是占位符，不会被读取，但建议使用00（占位符）或20（空格）作为占位符；右侧的01是文件类型，参考以下：
01 文本类型
02 图像类型（黑白）
其他类型将会**直接导致报错**，这点请留意。
## 示例（格式）
### 文本类型
头表上面写了，不用我说了吧。我们直接来看从offset(h)00000000位置07开始看————
目前最高支持写入**无限制**个字符。
### 图片类型
```xmu
58 4D 55 54 49 00 02 00 00 00 00 00 00 00 00 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF
FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00 FF 00
```
开头我不用说了吧。开头从08到0F不会被读取。
注意事项：必须是16x16的尺寸；00是白，FF是黑。