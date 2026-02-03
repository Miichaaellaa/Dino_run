# DEERUN

**DEERUN** je 2D arkádová hra vytvorená v knižnici PyGame, v ktorej sa hráč vžije do role jeleňa snažiaceho sa prežiť v nebezpečnej premávke.

## Ukážka hry

![Ukážka hry](assets/images/ukazka.png)

## Pointa hry

Cieľom hry je získať čo najvyššie skóre a vyhnúť sa zrážke s prichádzajúcimi vozidlami.

* Hráč ovláda postavu jeleňa.
* Hlavnou úlohou je **vyhýbať sa dopravným prostriedkom** (autá, taxi, dodávky).
* Hra obsahuje **systém levelov**, ktoré postupne zvyšujú rýchlosť a náročnosť.
* Získavaš body za každé úspešne preskočené vozidlo.
* Hra končí stavom *Game Over* pri kolízii, po ktorom je možné hru reštartovať.

## Funkcionality

### Modelovanie dát pomocou tried (OOP)

Projekt je postavený na objektovo orientovanom programovaní s rozdelením logiky do modulov:

* **`Dino` (Jeleň)**: Správa fyziky, gravitácie a animácií (8-frejmový run cycle).
* **`Obstacle`**: Inteligentný generátor prekážok s rôznymi vlastnosťami pre červené, modré, zelené autá, taxíky a dodávky.
* **`Background`**: Realizácia nekonečného rolovania pozadia pre plynulý efekt pohybu.
* **`Game`**: Hlavný manažér hry, ktorý riadi hernú slučku, kolízie, zvuky a náročnosť.

### Herná logika a UI

* **Dynamická obtiažnosť**: Automatické zvyšovanie rýchlosti (`game_speed`) a frekvencie prekážok na základe skóre.
* **Zvukový systém**: Implementácia hudby na pozadí a zvukových efektov s možnosťou úpravy hlasitosti.
* **Top 15 Skóre**: Systém zaznamenávania a zobrazovania najlepších dosiahnutých výsledkov.
* **Interaktívne menu**: Prehľadná obrazovka Game Over s možnosťou reštartu klávesou `R`.

## Ovládanie

| Klávesa               | Akcia                              |
| :-------------------- | :--------------------------------- |
| **Medzerník (Space)** | Skok (vyhnutie sa prekážke)        |
| **R**                 | Reštart hry po kolízii             |
| **ESC**               | Okamžité ukončenie celého programu |
| **Šípky / +/-**       | Úprava hlasitosti hudby a zvukov   |

## Štruktúra projektu

```text
Dino_run/
├── assets/
│   └── images/       # Textúry vozidiel, pozadia a animácie postavy
├── game/
│   ├── background.py # Nekonečné rolovanie cesty/pozadia
│   ├── dino.py       # Logika a animácie hlavnej postavy
│   ├── game.py       # Engine hry a správa stavov
│   ├── init.py       # Inicializácia balíka
│   └── obstacle.py   # Definícia a správanie vozidiel
├── sounds/           # Hudba na pozadí a zvukové efekty (crash, jump)
├── main.py           # Vstupný bod (spúšťač hry)
└── README.md         # Dokumentácia projektu
```

---

## Použité zdroje (Assets & Credits)

### Grafické podklady – BackGround
* Pinterest – **background**
https://sk.pinterest.com/pin/108930884731084699/

### Grafické podklady – Pixel Art Vozidlá

* Pinterest – **Orange car**
  [https://sk.pinterest.com/pin/237776055322046224/](https://sk.pinterest.com/pin/237776055322046224/)

* Pinterest – **Red car**
  [https://sk.pinterest.com/pin/567594359321722798/](https://sk.pinterest.com/pin/567594359321722798/)

* Pinterest – **Yellow Taxi**
  [https://sk.pinterest.com/pin/439523244906444352/](https://sk.pinterest.com/pin/439523244906444352/)

* Pinterest – **Green car**
  [https://sk.pinterest.com/pin/69172544272333071/](https://sk.pinterest.com/pin/69172544272333071/)

* Pinterest – **Truck**
  [https://sk.pinterest.com/pin/412360909650699110/](https://sk.pinterest.com/pin/412360909650699110/)

* Pinterest – **Blue car**
  [https://sk.pinterest.com/pin/83246293107216356/](https://sk.pinterest.com/pin/83246293107216356/)

### Hudba na pozadí

* **Pixel Drift** – Uppbeat
  [https://uppbeat.io/track/pecan-pie/pixel-drift](https://uppbeat.io/track/pecan-pie/pixel-drift)

### Zvukové efekty

* **Deer Jump Effect** – Freesound (Bastianhallo)
  [https://freesound.org/people/Bastianhallo/sounds/462958/](https://freesound.org/people/Bastianhallo/sounds/462958/)

* **Collision / Crash Effect** – Freesound (squareal)
  [https://freesound.org/people/squareal/sounds/237375/](https://freesound.org/people/squareal/sounds/237375/)
