# Para
Para je jednoduchý herný klient. Sťahuje hry zo serveru a dovoľuje užívateľom ich spustiť.
![Alt text](screenshot.png?raw=true "Screenshot z Ubuntu")

## Inštalácia
Pre Windows a Ubuntu už existujú installery, nájdete ich v [releases](https://github.com/sobkulir/para/releases).

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
