from objects.player import Player


class Equip:
    def __init__(self, name: str):
        self.name = name
        self.players: dict[str, Player] = {}
        self.mean: int = 0
        self.best_player: Player = Player("", "")
        self.best_score: int = 0

    @property
    def points(self) -> int:
        total = 0
        for player in self.players.values():
            point = player.points
            if point > self.best_score:
                self.best_score = point
                self.best_player = player
            total += player.points
        self.mean = total / len(self.players) if self.players else 0
        return total

    def count_player(self) -> int:
        return len(self.players)

    def add_player(self, player: Player) -> None:
        if not self.have_player(player.name):
            self.players[player.name] = player

    def remove_player(self, player_name: str) -> None:
        if self.have_player(player_name):
            del self.players[player_name]

    def have_player(self, player_name: str) -> bool:
        return player_name in self.players

    def switch_player(self, player: Player, equip: 'Equip') -> None:
        self.remove_player(player.name)
        equip.add_player(player)

    def get_best_players(self, number: int) -> dict[str, int]:
        d = {p.name: p.points for p in self.players.values()}
        list_ord = sorted(d.items(), key=lambda x: x[1], reverse=True)
        return dict(list_ord[:number])
