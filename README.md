# Mahjonist

A Mahjong (board game) score calculator built with Backbone.js, jQuery, Bootstrap and Flask backend.

Players input their faans (score factor) for each round of game and they will be scored according to them.

For the winner of a round, he/she obtains all the deducted scores from other players.

For others, they get score deduction calculated by - pow(2, faan - 4). Minimal score of each round is -50 (with 10+ faans lost).

When someone has a score of -200, the game is finished.

To start the server, run:

```
# Linux
python3 mahjonist.py

# Windows
python mahjonist.py
```