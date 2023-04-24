from random import choice

from objects.player import Player
from objects.equip import Equip

from utils.config import load_quiz_config


class Lobby:
    THEME = {
        "default": "l'équipe",
        "harry potter": "la maison",
    }

    def __init__(self):
        self.players: dict[str, Player] = {}
        self.equips: dict[str, Equip] = {}
        self.quiz_config = self.set_quiz_config()
        self.theme = self.get_theme()

    def get_theme(self):
        quiz_theme = self.quiz_config["equip"].get("theme", "default")
        return self.THEME[quiz_theme]

    def set_quiz_config(self) -> dict:
        config = load_quiz_config()
        for name in config["equip"]["names"]:
            self.equips[name] = Equip(name)
        return config

    def get_equip_with_less_players(self) -> Equip:
        less_players = None
        less_equip = []
        for equip in self.equips.values():
            count_player = len(equip.players)
            if not less_equip or count_player < less_players:
                less_equip = [equip]
                less_players = count_player
            elif count_player == less_players:
                less_equip.append(equip)
        return choice(less_equip)

    def get_equip(self, asked_equip: str) -> Equip:
        if asked_equip in self.equips:
            return self.equips[asked_equip]

        first_car = asked_equip[:4]
        for equip_name, equip in self.equips.items():
            if equip_name.startswith(first_car):
                return equip

    def add_player_to_equip(self, name_player: str, name_equip: str) -> str:
        if not name_equip:
            equip = self.get_equip_with_less_players()
        else:
            equip = self.get_equip(name_equip)
            if not equip:
                return f"{self.theme.capitalize()} {name_equip} n'existe pas!"

        player = Player(name_player, equip.name)
        self.players[name_player] = player
        equip.add_player(player)
        return f"Bienvenue chez les {equip.name}!"

    def move_player(self, name_player: str, name_equip: str) -> str:
        player = self.players.get(name_player)
        if not player:
            return self.add_player_to_equip(name_player, name_equip)

        current_equip = player.name_equip
        if current_equip == name_equip:
            return f"est déjà dans {self.theme} {name_equip}."

        equip = self.equips[current_equip]
        equip.remove_player(name_player)
        new_equip = self.equips[name_equip]
        new_equip.add_player(player)
        player.name_equip = name_equip
        return f"est maintenant dans {self.theme} {name_equip}."

    def change_question_duration(self, value: int) -> None:
        self.quiz_config["party"]["rep_time"] = value

    def get_duration(self) -> int:
        return self.quiz_config["party"]["rep_time"]

    def save(self) -> dict:
        config = {
            'theme': self.theme,
            'quiz_config': self.quiz_config,
            'equips': {},
            'players': {},
        }

        for player_name, player in self.players.items():
            config['players'][player_name] = {
                'equip': player.name_equip,
                'points': player.points,
                'all_response': player.all_response,
                'good_response': player.good_response,
            }

        for equip_name, equip in self.equips.items():
            config['equips'][equip_name] = {
                'points': equip.points,
            }
        return config

    def load(self, config: dict) -> None:
        self.theme = config['theme']
        self.quiz_config = config['quiz_config']

        for equip_name, config_equip in config['equips'].items():
            equip = Equip(equip_name)
            self.equips[equip_name] = equip

        for player_name, config_player in config['players'].items():
            name_equip = config_player['equip']
            player = Player(player_name, name_equip)
            player.add_points(config_player['points'])
            player.all_response = config_player['all_response']
            player.good_response = config_player['good_response']

            self.players[player_name] = player
            equip = self.get_equip(name_equip)
            equip.add_player(player)

        # For reload all values linked to points
        for equip in self.equips.values():
            _ = equip.points

    def get_ranking(self, reverse=False) -> dict[str, int]:
        list_points = {player_name: player.points for player_name, player in self.players.items()}
        return dict(sorted(list_points.items(), key=lambda i: i[1], reverse=reverse))

    def get_player_ranking(self, name_player) -> tuple[int, int]:
        rank = self.get_ranking()
        points = rank[name_player]
        rank = list(rank.keys()).index(name_player)
        return points, rank + 1
