# Connect four

Connect four game with pygame

## Bitboard representation

There are two instance variables of ConnectFourBoard to save the board state.
`current` represents the current player's stones, and `all` represents all stones.

Each bit represents the following position

```
(47) | 46 45 44 43 42 41 40
            .
            .
            .
15   | 14 13 12 11 10 9  8
7    | 6  5  4  3  2  1  0
```

There is an auxilary bit at the start of each row.


References

http://blog.gamesolver.org/solving-connect-four/06-bitboard/

https://towardsdatascience.com/creating-the-perfect-connect-four-ai-bot-c165115557b0

https://github.com/denkspuren/BitboardC4/blob/master/BitboardDesign.md
