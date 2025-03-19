# astrbot_plugin_wordle

Forked from [astrbot_plugin_wordle](https://github.com/Raven95676/astrbot_plugin_wordle)

Astrbot wordle游戏，支持指定位数——只需要单词表中存在该长度的单词。

**自定义词库和释义功能**。（修改在```/wordlist```目录下的json文件。这里使用了[nonebot-plugin-wordle](https://github.com/noneplugin/nonebot-plugin-wordle)的单词表。）

**自定义显示字体**。（在```main.py```里替换```MinecraftAE.ttf```为所需字体，字体的大小和位置可能也需要调整。）

加入了**单词拼写检查**，用户的输入的单词不存在时则不会进行下一步。（通过spellchecker库和自定词库之一即可。）

与原版相比，还优化了 “**猜单词提示**”的功能。现在用户获取提示时，如果一个正确字母都没有猜出来，插件会告诉其随机位置上的字母；如果猜出了部分字母，则插件会告知其顺序。

增加了**随机提示词**。

启动时，插件会自动尝试安装“pyspellchecker”库，但建议手动在AstrBot目录中requirements.txt添加一行“pyspellchecker”

> [!caution]
> 这个版本识别的不是指令，而是普通的对话。也就是说，你应该在移除指令前缀“/”。
> 识别的对话内容有：
> ```plain
> /猜单词
> 猜单词提示
> 猜单词结束
> ```

> [!tip]
> 本插件的图片不能通过QQ适配器发送，原因未知。所以生成的图片都经过了HTML渲染后才发送。
> 
> 但因此产生了一个问题，那就是单词提示的图片底下有一块**白边**（也许我以后会修好的）。
> 
> 如果你不使用QQ适配器就可以避免这个问题，你可以：
> 
> 在```main.py```中，把第333行改为
> 
> ```python
> Image.fromBytes(image_result_hint),
> ```
> 
> 第487行改为
> 
> ```python
> Image.fromBytes(image_result),
> ```
