# DEERUN

**DEERUN** je 2D arkádová hra vytvorená v knižnici PyGame. Hráč ovláda jeleňa, preskakuje prichádzajúce vozidlá a snaží sa nahrať čo najvyššie skóre.

## Ukážka hry

![Ukážka hry](assets/images/ukazka.png)

## Pointa hry

Cieľom hry je prežiť čo najdlhšie v premávke a získať čo najvyššie skóre.

* Hráč ovláda postavu jeleňa.
* Hlavnou úlohou je vyhýbať sa dopravným prostriedkom.
* Hra obsahuje levely, ktoré postupne zvyšujú rýchlosť a náročnosť.
* Body sa získavajú za úspešne preskočené vozidlá.
* Po kolízii sa zobrazí Game Over obrazovka s aktuálnym skóre.
* Najlepšie výsledky sa zobrazujú v hlavnom menu.

## Funkcionality

### Hotové

* **Singleplayer režim** so základnou hernou slučkou.
* **OOP štruktúra** rozdelená do samostatných tried `Dino`, `Obstacle`, `Background` a `Game`.
* **Animovaná postava** s behom a skokom.
* **Rôzne typy vozidiel** s rozdielnymi rozmermi a rýchlosťami.
* **Nekonečne rolujúce pozadie**.
* **Dynamická obtiažnosť** podľa skóre a levelu.
* **Zvukový systém** s hudbou na pozadí a efektmi pre skok a kolíziu.
* **Nastavenia hlasitosti** ukladané do `settings.json`.
* **Highscore systém** ukladaný do `highscores.json` a zobrazovaný v hlavnom menu.
* **Menu** so singleplayerom, nastaveniami a pripravenou multiplayer sekciou.

### Plánované

* **Multiplayer v lokálnej sieti**. Menu už obsahuje obrazovky pre vytvorenie servera a pripojenie, ale samotná sieťová hra zatiaľ nie je implementovaná.

## Ovládanie

| Klávesa | Akcia |
| :-- | :-- |
| **Medzerník (Space)** | Skok |
| **R** | Reštart hry po kolízii |
| **ESC v hre** | Ukončí aktuálnu hru alebo návrat do menu po Game Over |
| **ESC v menu** | Návrat o úroveň späť alebo ukončenie z hlavného menu |
| **+ / - v nastaveniach** | Úprava hlasitosti hudby a efektov |

## Spustenie

1. Nainštaluj závislosti:

```bash
pip install -r requirements.txt
```

2. Spusti hru:

```bash
python main.py
```

## Štruktúra projektu

```text
Dino_run/
├── assets/
│   └── images/          # Textúry vozidiel, pozadia a animácie postavy
├── game/
│   ├── background.py    # Nekonečné rolovanie pozadia
│   ├── dino.py          # Logika a animácie hlavnej postavy
│   ├── game.py          # Herná slučka, kolízie, skóre a zvuky
│   ├── obstacle.py      # Definícia a správanie vozidiel
│   └── paths.py         # Stabilné cesty k súborom projektu
├── sounds/              # Hudba na pozadí a zvukové efekty
├── highscores.json      # Uložené najlepšie skóre
├── settings.json        # Uložené nastavenia hlasitosti
├── main.py              # Vstupný bod hry
├── start_menu.py        # Menu a nastavenia
└── README.md            # Dokumentácia projektu
```

## Použité zdroje

### Grafické podklady

* Background: https://sk.pinterest.com/pin/108930884731084699/
* Orange car: https://sk.pinterest.com/pin/237776055322046224/
* Red car: https://sk.pinterest.com/pin/567594359321722798/
* Yellow Taxi: https://sk.pinterest.com/pin/439523244906444352/
* Green car: https://sk.pinterest.com/pin/69172544272333071/
* Truck: https://sk.pinterest.com/pin/412360909650699110/
* Blue car: https://sk.pinterest.com/pin/83246293107216356/

### Hudba a zvuky

* Pixel Drift - Uppbeat: https://uppbeat.io/track/pecan-pie/pixel-drift
* Deer Jump Effect - Freesound: https://freesound.org/people/Bastianhallo/sounds/462958/
* Collision / Crash Effect - Freesound: https://freesound.org/people/squareal/sounds/237375/
