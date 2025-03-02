import os
import random
import json
from io import BytesIO

from PIL import Image as ImageW
from PIL import ImageDraw, ImageFont

from astrbot.api.all import *  # noqa: F403
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register

try:
    os.system("pip install pyspellchecker")
    logger.log("Wordle已尝试安装pyspellchecker库")
except:
    logger.warning("Wordle未自动安装pyspellchecker库")
    logger.warning("这可能导致拼写检查的失败，请手动在AstrBot目录中requirements.txt添加一行“pyspellchecker”，如已安装请忽略")

from spellchecker import SpellChecker

class WordleGame:
    def __init__(self, answer: str):
        self.answer = answer.upper()
        self.length = len(answer)
        self.max_attempts = self.length + 1
        self.guesses: list[str] = []
        self.feedbacks: list[list[int]] = []

        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
        self.font_file = os.path.join(self.plugin_dir, "MinecraftAE.ttf")   # 这里可以修改字体为自定义字体

        self._font = ImageFont.truetype(self.font_file, 40)  #设定字体、字号、字重

    async def gen_image(self) -> bytes:
        CELL_COLORS = {
            2: (106, 170, 100),
            1: (201, 180, 88),
            0: (120, 124, 126),
            -1: (211, 214, 218),
        }
        BACKGROUND_COLOR = (255, 255, 255)
        TEXT_COLOR = (255, 255, 255)

        CELL_SIZE = 60
        CELL_MARGIN = 5
        GRID_MARGIN = 5

        cell_stride = CELL_SIZE + CELL_MARGIN
        width = GRID_MARGIN * 2 + cell_stride * self.length - CELL_MARGIN
        height = GRID_MARGIN * 2 + cell_stride * self.max_attempts - CELL_MARGIN

        image = ImageW.new("RGB", (width, height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        for row in range(self.max_attempts):
            y = GRID_MARGIN + row * cell_stride

            for col in range(self.length):
                x = GRID_MARGIN + col * cell_stride

                if row < len(self.guesses) and col < len(self.guesses[row]):
                    letter = self.guesses[row][col].upper()
                    feedback_value = self.feedbacks[row][col]
                    cell_color = CELL_COLORS[feedback_value]
                else:
                    letter = ""
                    cell_color = CELL_COLORS[-1]

                draw.rectangle(
                    [x, y, x + CELL_SIZE, y + CELL_SIZE], fill=cell_color, outline=None
                )

                if letter:
                    text_bbox = draw.textbbox((0, 0), letter, font=self._font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    letter_x = x + (CELL_SIZE - text_width) // 2 + 2
                    letter_y = y + (CELL_SIZE - text_height) // 2 + 1

                    draw.text((letter_x, letter_y), letter, fill=TEXT_COLOR, font=self._font)

        with BytesIO() as output:
            image.save(output, format="PNG")
            return output.getvalue()

    async def guess(self, word: str) -> bytes:
        word = word.upper()
        self.guesses.append(word)

        feedback = [0] * self.length
        answer_char_counts: dict[str, int] = {}
        
        for i in range(self.length):
            if word[i] == self.answer[i]:
                feedback[i] = 2
            else:
                answer_char_counts[self.answer[i]] = answer_char_counts.get(self.answer[i], 0) + 1
        
        for i in range(self.length):
            if feedback[i] != 2:
                char = word[i]
                if char in answer_char_counts and answer_char_counts[char] > 0:
                    feedback[i] = 1
                    answer_char_counts[char] -= 1
        
        self.feedbacks.append(feedback)
        result = await self.gen_image()

        return result
    
    @property
    def is_game_over(self):
        if not self.guesses:
            return False
        return len(self.guesses) >= self.max_attempts

    @property
    def is_won(self):
        return self.guesses and self.guesses[-1].upper() == self.answer


@register(
    "astrbot_plugin_wordle",
    "Raven95676",
    "Astrbot wordle游戏，支持指定位数",
    "1.0.0",
    "https://github.com/Raven95676/astrbot_plugin_wordle",
)
class PluginWordle(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.game_sessions: dict[str, WordleGame] = {}

    @staticmethod
    async def get_answer(length):
        try:
            wordlist_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "wordlist"
            )

            if not os.path.exists(wordlist_path):
                logger.error("词表文件不存在")
                return None

            # 获取单词文件
            word_file_list = os.listdir(wordlist_path)
            global word_dict
            word_dict = {}
            # 遍历单词表，并用字典接收内容
            for word_file in word_file_list:
                with open(os.path.join(wordlist_path,word_file),"r",encoding="utf-8") as f:
                    word_dict.update(json.load(f)) 
                    # 只保留长度为length的单词
                    for word in list(word_dict.keys()):
                        if len(word) != length:
                            del word_dict[word]

            # 随机选一个单词
            word = random.choice(list(word_dict.keys()))
            global explanation
            explanation = word_dict[word]["中释"]

            logger.info(f"选择了{word}单词，长度{length}，释义为{explanation}")

            return word.upper()
        
        except Exception as e:
            logger.error(f"加载词表失败: {e!s}")
            return None

    @command("束")  # type: ignore  # 指令唤醒词为“猜单词结”，指令为“束”，即用户输入“猜单词结束”时触发
    async def stop_wordle(self, event: AstrMessageEvent):
        """中止Wordle游戏"""
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
            yield event.plain_result("猜单词已结束。")
        else:
            yield event.plain_result("游戏还没开始，输入“/猜单词”来开始游戏吧！")

    @command("示")  # type: ignore  # 指令唤醒词为“猜单词提”，指令为“示”
    async def give_hint(self, event: AstrMessageEvent):
        """获取提示（第一个字母）"""
        session_id = event.unified_msg_origin
        if session_id not in self.game_sessions:
            yield event.plain_result("游戏还没开始，输入“/猜单词”来开始游戏吧！")
            return
        game = self.game_sessions[session_id]
        i = random.randint(0,len(game.answer)-1)
        hint = f"提示：第{i+1}个字母是 {game.answer[i]}"
        yield event.plain_result(hint)
        return
    
    @command("单词")  # noqa: F405    # 指令唤醒词为“/猜”，指令为“单词”，即用户输入“/猜单词”时触发
    async def start_wordle(self, event: AstrMessageEvent, length: str = "5"):
        if length == "":
            length_ok = True
        try:
            length = int(length)
            length_ok = True
        except:
            yield event.plain_result(f"指令有点错误哦。\n输入“/猜单词 + 单词长度”可以开始游戏，输入“猜单词结束”“猜单词提示”分别可以结束游戏和获取提示。")
            length_ok = False
        """开始Wordle游戏"""
        answer = await self.get_answer(length)
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
        if not answer:
            if length_ok:
                random_text = random.choice([
                    f"{length}字母长度的单词，我没找到啊……",
                    f"{length}个字母的单词好像有点稀有哦，换一个吧！",
                    "没找到这么长的单词，换一个吧！"
                ])
                yield event.plain_result(random_text)
        else:
            game = WordleGame(answer)
            self.game_sessions[session_id] = game
            logger.debug(f"答案是：{answer}")
            random_text = random.choice([
                    f"游戏开始！请输入长度为{length}的单词。",
                    f"游戏开始了！请输入长度为{length}的单词。",
                    f"游戏开始了！请输入长度为{length}的单词。"
                ])
            yield event.plain_result(random_text)
        pass

    @event_message_type(EventMessageType.ALL)  # noqa: F405
    async def on_all_message(self, event: AstrMessageEvent):
        msg = event.get_message_str()
        logger.info(msg)
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions and event.is_at_or_wake_command:
            game = self.game_sessions[session_id]

            if msg.startswith("单词") or msg.startswith("示"):
                return
            else:
                length = game.length
                if len(msg) != length:
                    yield event.plain_result(f"单词长度不正确🌀！应该是{length}个字母。")
                    return
            
            # 单词拼写检查
            if not(msg.startswith("单词")):
                spellcheck = SpellChecker()
                if not (
                    msg in list(word_dict.keys())
                    or spellcheck.known((msg,))
                    ):
                    random_text = random.choice([
                    "拼写错误😉！",
                    "试试重新拼写一下单词吧！",
                    "单词拼写不正确！"
                    ])
                    yield event.plain_result(random_text)
                    return

                if not msg.isalpha():
                    random_text = random.choice([
                    "你要输入英文才行啊😉！",
                    "语言不正确哦，要输入英语单词。",
                    "我以后就可以用其他语言猜单词了，不过现在还是用英语吧！"
                    "Try in English💬!", 
                    "需要英文单词～🔡",  
                    "Alphabet Only!🔤", 
                    "外星挑战：地球英文输入🛸。", 
                    "符号错误🔣，需要纯字母。", 
                    "❗Error: Expected ENGLISH :("
                ])
                    yield event.plain_result(random_text)
                    return

            image_result = await game.guess(msg)

            if game.is_won:
                sender_info = event.get_sender_name() if event.get_sender_name() else event.get_sender_id()
                random_text = random.choice([
                    "恭喜你猜对了😉！",
                    "Cool🎉！",
                    "答案正确✅！"
                    "太棒了🎉！", 
                    "猜中啦🎯！",  
                    "冠军🥇！", 
                    "天才🌟！", 
                    "胜利🏆！", 
                    "满分💯！", 
                    "王者👑！", 
                    "绝了🤩！"
                ])
                if random.randint(1,22) == 1:
                    random_text = "🔠🥳语言神，启动🔠🥳！"
                game_status = f"{random_text}“{game.answer}”的意思是“{explanation}”"
                del self.game_sessions[session_id]
            elif game.is_game_over:
                game_status = f"没有人猜出答案啊Σ(°△°|||)︴\n正确答案是“{game.answer}”，意思是“{explanation}”"
                del self.game_sessions[session_id]
            else:
                game_status = f"已猜测 {len(game.guesses)}/{game.max_attempts} 次"
                logger.info(f"已猜测 {len(game.guesses)}/{game.max_attempts} 次")

            chain = [
                Image.fromBytes(image_result),  # noqa: F405
                Plain(game_status),  # noqa: F405
            ]

            yield event.chain_result(chain)
