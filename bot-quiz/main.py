import asyncio
import json

from twitchio.ext import commands
from pathlib import Path

from utils.config import load_auth_config
from objects.lobby import Lobby
from objects.quiz import Quiz


class Bot(commands.Bot):
    MOD = ['LotekaTV']
    PODIUM = ["1er", "2ème", "3ème"]
    PATH_FILE = Path(__file__)
    PATH_TXT = PATH_FILE.parent / 'textes'
    PATH_SAVE = PATH_FILE.parent / 'save'
    MAX_PLAYER = 15

    def __init__(self):
        auth_config = load_auth_config()
        commands.Bot.__init__(self,
                              token=auth_config['token'],
                              prefix=auth_config['prefix'],
                              initial_channels=[auth_config['chan']])

        self.lobby = None
        self.quiz = None
        self.wait_answer = False
        self.response = None
        self.list_rep_all = []
        self.list_rep_good = []
        self._reset_texts()

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    @staticmethod
    def _get_message_from_command(ctx: commands.Context) -> str:
        prefix = ctx.prefix
        name_cmd = ctx.command.name
        len_cmd = len(prefix) + len(name_cmd) + 1
        return ctx.message.content[len_cmd:]

    @commands.command()
    async def set_time(self, ctx: commands.Context) -> None:
        if ctx.author.display_name not in self.MOD:
            return
        duration = self._get_message_from_command(ctx)
        self.lobby.change_question_duration(int(duration))

    def _start_party(self):
        self.lobby = Lobby()
        config_party = self.lobby.quiz_config["party"]
        self.quiz = Quiz(themes=config_party["theme"], number_question=config_party["rounds"])
        self.quiz.init_quiz()

    def _stop_party(self):
        self._reset_texts()
        self.lobby = None
        self.quiz = None

    def _reload(self):
        self._start_party()
        path_lobby = self.PATH_SAVE / 'save_lobby.json'
        with open(path_lobby) as json_file:
            data = json.load(json_file)
            self.lobby.load(data)

        path_quiz = self.PATH_SAVE / 'save_quiz.json'
        with open(path_quiz) as json_file:
            data = json.load(json_file)
            self.quiz.load(data)

    def _reset_texts(self):
        equip_names = [equip_name.lower() for equip_name in self.lobby.equips.keys()] if self.lobby else []
        print(equip_names)
        for file in self.PATH_TXT.iterdir():
            if file.stem in equip_names:
                file.unlink()
            else:
                p = self.PATH_TXT / file
                self.write_in_file(p, "")

    @commands.command()
    async def start_party(self, ctx: commands.Context) -> None:
        if ctx.author.display_name in self.MOD and not self.lobby:
            self._start_party()
            await ctx.send(f"Que le QCM commence!")

    @commands.command()
    async def reload(self, ctx: commands.Context) -> None:
        if ctx.author.display_name not in self.MOD:
            return
        self._reload()

    @commands.command()
    async def stop_party(self, ctx: commands.Context) -> None:
        if ctx.author.display_name not in self.MOD or not self.lobby:
            return
        self._stop_party()

    @commands.command()
    async def equip_choice(self, ctx: commands.Context) -> None:
        if not self.lobby:
            return
        name_player = ctx.author.display_name
        if name_player in self.lobby.players:
            return

        asked_equip = self._get_message_from_command(ctx).capitalize()
        rep = self.lobby.add_player_to_equip(name_player, asked_equip)
        await ctx.reply(rep)

    @commands.command()
    async def move(self, ctx: commands.Context) -> None:
        if ctx.author.display_name not in self.MOD or not self.lobby:
            return
        name_player, asked_equip = self._get_message_from_command(ctx).split(' ')
        rep = self.lobby.move_player(name_player, asked_equip)
        await ctx.send(f"{name_player} {rep}")

    def _reset_question(self) -> None:
        self.wait_answer = False
        self.list_rep_all = []
        self.list_rep_good = []

    @commands.command()
    async def question(self, ctx: commands.Context) -> None:
        if not self.lobby or ctx.author.display_name not in self.MOD or self.wait_answer:
            return
        self.wait_answer = True

        txt, quest = self.quiz.next_question()
        if not quest:
            return

        choices = f"A: {quest['A']} - B: {quest['B']} - C:{quest['C']} - D: {quest['D']}"
        self.response = quest['reponse']
        await self.write_questions_files(quest)
        await ctx.send(txt)
        await ctx.send(quest['question'])
        await ctx.send(choices)

        loop = asyncio.get_event_loop()
        duration = self.lobby.get_duration()
        loop.call_later(duration, lambda: asyncio.ensure_future(self.wait_time(ctx)))

    async def update_points(self):
        for equip_name, equip in self.lobby.equips.items():
            path_file = self.PATH_TXT / f'{equip_name.lower()}.txt'
            self.write_in_file(path_file, equip.points)

    async def update_ranking(self):
        ranking = self.lobby.get_ranking(reverse=True)
        txt = ""
        path_file = self.PATH_TXT / 'score.txt'

        for i, (name_player, points) in enumerate(ranking.items()):
            if i > self.MAX_PLAYER:
                break
            txt += f'{name_player}: {points} points\n'
        self.write_in_file(path_file, txt)

    async def write_questions_files(self, questions: dict) -> None:
        for txt, value in questions.items():
            path_file = self.PATH_TXT / f'{txt}.txt'
            if path_file.exists():
                self.write_in_file(path_file, value)

    @staticmethod
    def write_in_file(path_file: Path, value: str) -> None:
        path_file.write_text(str(value))

    async def wait_time(self, ctx: commands.Context) -> None:
        await ctx.send(f"Temps écoulé. La réponse était: {self.response}")
        msg = []
        for i, pos in enumerate(self.PODIUM):
            if i < len(self.list_rep_good):
                msg.append(f"{pos}: {self.list_rep_good[i]}")
        if msg:
            await ctx.send(" - ".join(msg))
        self._reset_question()
        await self.update_points()
        await self.update_ranking()
        self.quiz.valid_question()
        await self.save()

    @commands.command()
    async def rep(self, ctx: commands.Context) -> None:
        if not self.lobby or not self.wait_answer:
            return

        name_player = ctx.author.display_name
        if name_player not in self.lobby.players:
            await ctx.reply(f"Tu n'as pas choisi ton équipe!")
            return

        if name_player in self.list_rep_all:
            return

        self.list_rep_all.append(name_player)
        player = self.lobby.players[name_player]
        player.all_response += 1
        rep = self._get_message_from_command(ctx).upper()
        if rep != self.response:
            return

        self.list_rep_good.append(name_player)
        player.good_response += 1
        max_point = self.lobby.quiz_config["party"]["score_first"]
        min_point = self.lobby.quiz_config["party"]["score_last"]
        player.points += max(max_point - len(self.list_rep_good) + 1, min_point)

    @commands.command()
    async def point(self, ctx: commands.Context) -> None:
        if not self.lobby:
            return

        name_player = ctx.author.display_name
        if name_player not in self.lobby.players:
            await ctx.reply(f"Tu n'as pas choisi ton équipe!")
            return

        points, rank = self.lobby.get_player_ranking(name_player)
        await ctx.reply(f"Tu as {points} point(s), rank: {rank} !")

    @commands.command()
    async def stats(self, ctx: commands.Context) -> None:
        if not self.lobby:
            return

        name_player = ctx.author.display_name
        player = self.lobby.players.get(name_player)
        if not player:
            await ctx.reply(f"Tu n'as pas choisi ton équipe!")
            return

        points, rank = self.lobby.get_player_ranking(name_player)
        await ctx.reply(f"Points: {points}, rank: {rank}, réponses: {player.all_response} "
                        f"dont {player.good_response} bonnes réponses !")

    async def save(self):
        path_lobby = self.PATH_SAVE / 'save_lobby.json'
        with open(path_lobby, 'w', encoding='utf-8') as outfile:
            json.dump(self.lobby.save(), outfile)

        path_quiz = self.PATH_SAVE / 'save_quiz.json'
        with open(path_quiz, 'w', encoding='utf-8') as outfile:
            json.dump(self.quiz.save(), outfile)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
