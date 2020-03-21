# Para
Para je jednoduchý herný klient. Sťahuje hry zo serveru a dovoľuje užívateľom ich spustiť.

## Inštalácia
Existujú installery, zatiaľ iba pre Windowsy a Debiany:
* Windows: [para_installer_win.exe](https://people.ksp.sk/~faiface/osp_games/para_installer_win.exe)
* Linux Debian: [para-deb-1-0-1.deb](https://people.ksp.sk/~faiface/osp_games/para-deb-1-0-1.deb)

## Spustenie zo zdrojákov
Treba stiahnuť repozitár pomocou `git clone https://github.com/sobkulir/para`. Potom sa postup líši na win/linux kvôli aktivovaniu `virtualenv`.

Pre Windowsy:
```
python -m venv venv
call venv\Scripts\activate

pip install -r requirements.txt
fbs run
```

Pre Linuxy:
```
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
fbs run
```

## Spravenie installeru
Ak chcete spraviť installer, odporúčam prečítať si [tutoriál k fbs](https://github.com/mherrmann/fbs-tutorial). V skratke treba:
* Python 3.5 alebo 3.6
* Nainštalovať nejakú libku závislú na platforme
* Pustiť `fbs install`