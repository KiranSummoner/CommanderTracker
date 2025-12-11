import flet as ft
import json
import os
from datetime import datetime

# Dateinamen
DATA_PLAYERS = "players.json"
DATA_HISTORY = "history.json"
DATA_RULES = "rules.json"
DATA_SEASONS = "seasons.json"


class CommanderApp:
    def __init__(self):
        # Daten laden
        self.players = self.load_json(DATA_PLAYERS, {})
        self.history = self.load_json(DATA_HISTORY, [])
        self.seasons = self.load_json(DATA_SEASONS, {})

        # Regeln laden und 'X' durch einen Standardwert ersetzen (z.B. +1), um Fehler zu vermeiden
        # Flet-Dialoge sind komplexer, daher wird hier temporär +1 gesetzt.
        self.rules = self.load_json(DATA_RULES, {
            "Win a game": 1,  # Geändert von 'X' zu 1, für einfache Punktvergabe
            "Sol-Ring Turn One": -1,
            "Turn longer than 5 min": -1,
            "Last place": -1,
            "Monarch for more than 3 Turns": 1,
            "Killing everyone in the same Turn": -1,
            "First Blood with combat Dmg": 1,
            "One shot a player with one creature": -1,
        })
        self.save_json(DATA_RULES, self.rules)

    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # --- Hauptprogramm ---
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Commander Tracker"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 10
        page.scroll = "adaptive"

        # --- UI ELEMENTE ---

        # 1. Scoreboard Elemente
        self.score_list = ft.Column(scroll="adaptive")

        # 2. History Elemente
        self.dd_player = ft.Dropdown(label="Spieler wählen", options=[])
        self.dd_rule = ft.Dropdown(label="Regel wählen", options=[ft.dropdown.Option(k) for k in self.rules.keys()])
        self.history_list = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=False)

        # 3. Player Management Elemente
        self.txt_new_player = ft.TextField(label="Neuer Spieler Name", expand=True)

        # 4. Rules Elemente
        self.rules_list = ft.ListView(expand=True, spacing=10, padding=10)

        # 5. Archive Elemente
        self.archive_list = ft.ListView(expand=True, spacing=10, padding=10)

        # --- LAYOUT BAUEN (TABS) ---
        t = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Scoreboard",
                    icon="list",
                    content=ft.Column([
                        ft.Container(height=10),
                        self.score_list
                    ], scroll="adaptive")
                ),
                ft.Tab(
                    text="History",
                    icon="history",
                    content=ft.Column([
                        ft.Container(height=10),
                        self.dd_player,
                        self.dd_rule,
                        ft.ElevatedButton("Regel anwenden", on_click=self.apply_rule, width=200),
                        ft.Divider(),
                        ft.Text("Game Log:", size=16, weight="bold"),
                        ft.Container(content=self.history_list, height=300)
                    ])
                ),
                ft.Tab(
                    text="Spieler",
                    icon="person_add",
                    content=ft.Column([
                        ft.Container(height=20),
                        ft.Row([self.txt_new_player, ft.IconButton("add", on_click=self.add_player_click)]),
                        ft.Divider(),
                        ft.Text("Steuerung:", size=16),
                        ft.ElevatedButton("Neue Saison starten & Punkte archivieren", on_click=self.save_season_click,
                                          color="blue"),
                        ft.ElevatedButton("Punkte Reset (0)", on_click=self.reset_points_click, color="red"),
                    ])
                ),
                ft.Tab(
                    text="Rules",
                    icon="info",
                    content=ft.Column([
                        ft.Text("Aktive Regeln:", size=18, weight="bold"),
                        self.rules_list
                    ])
                ),
                ft.Tab(
                    text="Archive",
                    icon="archive",
                    content=ft.Column([
                        ft.Text("Gespeicherte Saisons:", size=18, weight="bold"),
                        self.archive_list
                    ], scroll="adaptive")
                ),
            ],
            expand=1,
        )

        page.add(t)

        # Initiales Laden
        self.update_ui()

    # --- LOGIK & UI UPDATES ---

    def update_ui(self):
        """Aktualisiert alle Listen, Dropdowns und Tabs"""

        # 1. Dropdown updaten
        self.dd_player.options = [ft.dropdown.Option(p) for p in self.players.keys()]
        if not self.dd_player.value and self.players:
            self.dd_player.value = list(self.players.keys())[0]

        # 2. Scoreboard neu bauen (Karten-Design für Mobile)
        self.score_list.controls.clear()
        sorted_players = sorted(self.players.items(), key=lambda item: item[1], reverse=True)

        for name, score in sorted_players:
            card = ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(name, size=18, weight="bold"),
                            ft.Text(f"{score} Punkte", size=14, color="grey")
                        ], expand=True),
                        ft.IconButton("remove", on_click=lambda e, n=name: self.modify_score(n, -1)),
                        ft.IconButton("add", on_click=lambda e, n=name: self.modify_score(n, 1)),
                        ft.IconButton("delete_outline", icon_color="red",
                                      on_click=lambda e, n=name: self.delete_player(n)),
                    ], alignment="spaceBetween")
                )
            )
            self.score_list.controls.append(card)

        # 3. History Liste updaten
        self.history_list.controls.clear()
        for entry in self.history:
            self.history_list.controls.insert(0, ft.Text(entry))

            # 4. Rules Tab updaten
        self.rules_list.controls.clear()
        for rule, points in self.rules.items():
            self.rules_list.controls.append(ft.Text(f"• {rule}: {points} Punkte", size=14))

        # 5. Archive Tab updaten
        self.archive_list.controls.clear()
        sorted_seasons = sorted(self.seasons.items(), key=lambda item: item[0], reverse=True)

        if not self.seasons:
            self.archive_list.controls.append(ft.Text("Noch keine Saisons archiviert."))
        else:
            for season_name, players_data in sorted_seasons:
                player_texts = []
                sorted_p = sorted(players_data.items(), key=lambda item: item[1], reverse=True)
                for name, points in sorted_p:
                    player_texts.append(f"{name}: {points}")

                self.archive_list.controls.append(ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(season_name, size=16, weight="bold"),
                            ft.Text("\n".join(player_texts), size=12)
                        ])
                    )
                ))

        self.page.update()

    # --- EVENT HANDLER ---

    def add_player_click(self, e):
        name = self.txt_new_player.value.strip()
        if name and name not in self.players:
            self.players[name] = 0
            self.save_json(DATA_PLAYERS, self.players)
            self.txt_new_player.value = ""
            self.update_ui()
            self.page.show_snack_bar(ft.SnackBar(ft.Text(f"{name} hinzugefügt!")))
        self.page.update()

    def modify_score(self, name, amount):
        if name in self.players:
            self.players[name] += amount
            self.save_json(DATA_PLAYERS, self.players)
            self.update_ui()

    def delete_player(self, name):
        if name in self.players:
            del self.players[name]
            self.save_json(DATA_PLAYERS, self.players)
            self.update_ui()

    def reset_points_click(self, e):
        def close_dialog(e):
            self.page.close(dialog)
            if e.control.text == "Ja":
                for p in self.players:
                    self.players[p] = 0
                self.save_json(DATA_PLAYERS, self.players)
                self.update_ui()
                self.page.show_snack_bar(ft.SnackBar(ft.Text("Punkte zurückgesetzt.")))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Punkte zurücksetzen"),
            content=ft.Text("Sollen alle Punkte auf 0 gesetzt werden?"),
            actions=[
                ft.TextButton("Nein", on_click=close_dialog),
                ft.TextButton("Ja", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def save_season_click(self, e):
        # 1. Abbruch bei leeren Spielern
        if not self.players:
            self.page.show_snack_bar(ft.SnackBar(ft.Text("Bitte zuerst Spieler hinzufügen!")))
            self.page.update()
            return

        # Variablen für den Dialog vorbereiten
        now = datetime.now().strftime("%Y-%m-%d")
        season_name = f"Season {len(self.seasons) + 1} ({now})"

        def close_dialog(e):
            self.page.close(dialog)

            # NEUE, ZUVERLÄSSIGE PRÜFUNG: Wenn der geklickte Control ein Elevated Button ist (also "Speichern & Reset")
            if isinstance(e.control, ft.ElevatedButton):

                # --- WICHTIG: ARCHIVIERUNG STARTET HIER, NUR WENN BESTÄTIGT ---

                # 1. Archivieren (Speichern der aktuellen Punkte in seasons)
                self.seasons[season_name] = self.players.copy()
                self.save_json(DATA_SEASONS, self.seasons)

                # 2. Reset (Punkte in players auf 0 setzen)
                for p in self.players:
                    self.players[p] = 0
                self.save_json(DATA_PLAYERS, self.players)
                self.history = []
                self.save_json(DATA_HISTORY, self.history)

                # 3. Update und Benachrichtigung
                self.update_ui()
                self.page.show_snack_bar(ft.SnackBar(ft.Text(f"{season_name} archiviert & Punkte zurückgesetzt!")))

        # Dialog-Definition
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Saison archivieren"),
            content=ft.Text(f"Saison als '{season_name}' speichern und Punkte zurücksetzen?"),
            actions=[
                ft.TextButton("Abbrechen", on_click=close_dialog),
                ft.ElevatedButton("Speichern & Reset", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Dialog öffnen
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def apply_rule(self, e):
        player = self.dd_player.value
        rule = self.dd_rule.value

        if not player or not rule:
            self.page.show_snack_bar(ft.SnackBar(ft.Text("Bitte Spieler und Regel wählen!")))
            return

        points = self.rules[rule]

        # Punkte sind in der Regel schon integer, da wir 'X' entfernt haben
        points = int(points)
        self.players[player] += points
        self.save_json(DATA_PLAYERS, self.players)

        log = f"{player} -> {rule} ({points} Pts)"
        self.history.insert(0, log)  # Fügt Eintrag am Anfang der Liste ein
        self.save_json(DATA_HISTORY, self.history)

        self.update_ui()
        self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Regel angewendet: {points} Pkt")))


# App Start
# Ändere ganz unten im Code
if __name__ == "__main__":
    app_logic = CommanderApp()
    # Flet startet jetzt im Vollbildmodus
    ft.app(target=app_logic.main, view=ft.AppView.FLET_APP_HIDDEN)