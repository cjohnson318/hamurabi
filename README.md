# Multiplayer Hamurabi

This is a multiplayer version of the classic Hamurabi. It is not an exact copy
of Hamurabi, rather a loose interpretation. In this implementation, you can
have multiple city states that can buy and sell land through a central market,
and attack each other asymmetrically in a greater world.

In the future I want to the market to buy and sell according to actual orders
placed by different city states, rather than just having a "market price" that
simulates demand. I'd also like to have actual distances between city states,
so that armies have to pay more in order to travel further.

```bash
uv run main.py <rounds>
```