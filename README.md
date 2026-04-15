MetaPokerBot 🃏
An exploitative poker AI that dynamically models opponents and adapts its strategy to beat predictable bots.

Overview
MetaPokerBot is a Python-based poker agent built for competitive bot-vs-bot poker tournaments. Instead of following a fixed strategy, it observes opponent behavior over time, classifies their playing style, and exploits their weaknesses.
It uses Monte Carlo simulation to estimate win probability each hand and makes decisions across a tiered decision tree based on hand strength, pot odds, and the classified opponent type at the table.

Features

Opponent Modeling — Tracks fold rate, aggression frequency, and all-in frequency for each opponent across hands
Automatic Classification — Labels opponents as Passive, Aggressive, Bluff, All-In, or Random bots
Monte Carlo Win Estimation — Simulates hundreds of random runouts to estimate win probability in real time
Exploitative Decision Tree — Adapts bet sizing, bluff frequency, and call thresholds based on opponent type
Draw Detection — Identifies flush draws and open-ended straight draws to inform semi-bluff decisions
Pre-flop Hand Strength — Evaluates starting hands (pocket pairs, suited connectors, premium broadway hands) before community cards are dealt


Opponent Types
TypeBehaviorExploitation StrategyALL_IN_BOTGoes all-in frequently (>30% of actions)Wait for strong hands, call downRAISE_BOTHigh aggression, rarely foldsTighten ranges, value bet bigPASSIVE_BOTChecks and calls, rarely raisesBet frequently, steal potsBLUFF_BOTAggressive but folds to pressureCall wider, re-raise to punishRANDOM_BOTNo clear patternPlay standard GTO-adjacent strategy

Decision Tiers
MetaPokerBot makes decisions across five win probability tiers:
Win ProbabilityAction> 65%All-in50–65%Bet or raise; occasional all-in aggression35–50%Bet or call; fold only to massive pressure20–35%Semi-bluff; exploit passives; call vs bluffers< 20%Check or fold; blind steal vs passives

Project Structure
.
├── metabot.py          # Main bot logic (MetaPokerBot, OpponentProfile)
├── player.py           # Base Player class and PlayerAction definitions
├── card.py             # Card, Rank, Suit, and Deck abstractions
├── hand_evaluator.py   # HandEvaluator and HandRank logic
├── game.py             # PokerGame engine and GamePhase management
├── baseplayers.py      # Reference bots (RaisePlayer, FoldPlayer, etc.)
└── README.md

Getting Started
Prerequisites

Python 3.10+
No external dependencies — uses only the standard library

Running a Tournament
bashpython metabot.py
This runs a 10-hand tournament between MetaPokerBot and three reference bots (two RaisePlayers and one FoldPlayer), then prints final stacks and MetaBot's opponent classifications.
Using MetaPokerBot in Your Own Game
pythonfrom metabot import MetaPokerBot
from game import PokerGame

bot = MetaPokerBot("MetaBot", stack=1000, simulation_count=500)
game = PokerGame([bot, ...], big_blind=20)
The simulation_count parameter controls Monte Carlo accuracy vs. speed. 500 is a good default; reduce to 100–200 for faster games with more players.

How It Works
1. Parsing Game State
Each turn, the bot receives a flat game_state list:
[card1, card2, community1..5, pot, current_bet, big_blind, ..., num_players, stack1..N]
Cards are encoded as integers (rank % 13 + 2, suit = idx // 13) and converted to Card objects.
2. Opponent Modeling
Every entry in action_history is parsed each turn:
pythonfor phase, player_name, action, amount in action_history:
    self.opponent_profiles[player_name].update(action, phase)
    self.opponent_profiles[player_name].classify()
Classification requires at least 3 observed actions per opponent.
3. Monte Carlo Simulation
Win probability is estimated by simulating N random completions of the board:

Remove known cards from the deck
Deal remaining community cards randomly
Deal two random hole cards to each opponent
Compare hands using HandEvaluator
Return (wins + 0.5 * ties) / simulations

4. Decision Making
The bot calls _decide_action() with win probability, call amount, pot size, stack sizes, phase, and the dominant opponent type. Opponent-specific adjustments are applied in Tiers 4 and 5 (medium-weak and weak hands).

Configuration
ParameterDefaultDescriptionsimulation_count500Monte Carlo iterations per decisionstack1000Starting chip stack
Lower simulation_count values (e.g. 100) significantly improve speed at the cost of win probability accuracy, which is acceptable in multi-player games where approximations are sufficient.

Limitations

Opponent classification requires several hands of history — early decisions against unknown opponents default to standard thresholds
Monte Carlo simulation scales with the number of opponents; accuracy drops in large fields unless simulation_count is increased
No persistent memory across sessions — opponent profiles reset each run
Position-aware play is not currently implemented


License
MIT
