"""
Meta Strategy Poker Bot - FIXED VERSION
========================
An exploitative poker bot that adapts to opponent behavior patterns.
Designed to beat predictable bots by exploiting their weaknesses.

Key Fixes:
- Removed contradictory bet-then-fold logic
- Simplified decision tree with clear win probability thresholds
- Strong hands never fold unless facing massive all-in
- Consistent aggression levels
"""

from typing import List, Tuple, Dict
from collections import defaultdict
from player import Player, PlayerAction, PlayerStatus
from card import Card, Rank, Suit, Deck
from hand_evaluator import HandEvaluator, HandRank
import random
from itertools import combinations


class OpponentType:
    """Classification of opponent playing styles"""
    ALL_IN_BOT = "all_in"
    RAISE_BOT = "aggressive"
    PASSIVE_BOT = "passive"
    BLUFF_BOT = "bluff"
    RANDOM_BOT = "random"
    UNKNOWN = "unknown"


class OpponentProfile:
    """Tracks statistics for opponent modeling"""
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.total_actions = 0
        self.fold_count = 0
        self.call_count = 0
        self.raise_count = 0
        self.all_in_count = 0
        self.check_count = 0
        self.bet_count = 0
        
        self.classified_type = OpponentType.UNKNOWN
    
    def update(self, action: str, phase: str):
        """Update statistics based on observed action"""
        self.total_actions += 1
        
        if action == "fold":
            self.fold_count += 1
        elif action == "call":
            self.call_count += 1
        elif action == "raise":
            self.raise_count += 1
        elif action == "all-in":
            self.all_in_count += 1
        elif action == "check":
            self.check_count += 1
        elif action == "bet":
            self.bet_count += 1
    
    def get_aggression_frequency(self) -> float:
        """Calculate how often opponent takes aggressive actions"""
        if self.total_actions == 0:
            return 0.0
        aggressive = self.raise_count + self.bet_count + self.all_in_count
        return aggressive / self.total_actions
    
    def get_fold_frequency(self) -> float:
        """Calculate fold frequency"""
        if self.total_actions == 0:
            return 0.0
        return self.fold_count / self.total_actions
    
    def get_all_in_frequency(self) -> float:
        """Calculate all-in frequency"""
        if self.total_actions == 0:
            return 0.0
        return self.all_in_count / self.total_actions
    
    def classify(self) -> str:
        """Classify opponent based on observed behavior"""
        if self.total_actions < 3:
            return OpponentType.UNKNOWN
        
        all_in_freq = self.get_all_in_frequency()
        aggression_freq = self.get_aggression_frequency()
        fold_freq = self.get_fold_frequency()
        
        # All-In Bot: Goes all-in frequently (>30% of actions)
        if all_in_freq > 0.3:
            self.classified_type = OpponentType.ALL_IN_BOT
            return OpponentType.ALL_IN_BOT
        
        # Passive Bot: Rarely raises/bets, mostly checks/calls
        if aggression_freq < 0.2 and fold_freq < 0.4:
            self.classified_type = OpponentType.PASSIVE_BOT
            return OpponentType.PASSIVE_BOT
        
        # Raise Bot: High aggression, low fold
        if aggression_freq > 0.5 and fold_freq < 0.3:
            self.classified_type = OpponentType.RAISE_BOT
            return OpponentType.RAISE_BOT
        
        # Bluff Bot: High aggression but also folds when pressured
        if aggression_freq > 0.4 and fold_freq > 0.3:
            self.classified_type = OpponentType.BLUFF_BOT
            return OpponentType.BLUFF_BOT
        
        # Random Bot: Mixed behavior, no clear pattern
        self.classified_type = OpponentType.RANDOM_BOT
        return OpponentType.RANDOM_BOT


class HandStrength:
    """Hand strength categories"""
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    DRAW = "draw"


class MetaPokerBot(Player):
    """
    Meta Strategy Poker Bot - FIXED VERSION
    
    Implements exploitative poker strategy by:
    1. Modeling opponents dynamically
    2. Simulating win probability with Monte Carlo
    3. Adapting strategy based on opponent type
    4. CONSISTENT betting - no contradictory bet-then-fold
    """
    
    def __init__(self, name: str, stack: int, simulation_count: int = 500):
        super().__init__(name, stack)
        self.simulation_count = simulation_count
        self.opponent_profiles: Dict[str, OpponentProfile] = {}
        self.hands_played = 0
    
    def action(self, game_state: list[int], action_history: list) -> Tuple[PlayerAction, int]:
        self.hands_played += 1

        # Parse game state
        my_cards = self._parse_hole_cards(game_state[0:2])
        community_cards = self._parse_community_cards(game_state[2:7])
        pot = game_state[7]
        current_bet = game_state[8]
        big_blind = game_state[9]
        num_players = game_state[11]
        stacks = game_state[12:12+num_players]

        # Update opponent models
        self._update_opponent_models(action_history)

        # Calculate call amount
        call_amount = max(0, current_bet - self.bet_amount)

        # Evaluate hand
        hand_strength_category, hand_rank = self._evaluate_hand_strength(my_cards, community_cards)

        # Simulate win probability
        win_probability = self._simulate_win_probability(
            my_cards, community_cards, num_players - 1
        )

        # Get active opponents
        active_opponents = self._get_active_opponents(action_history, num_players)
        phase = self._determine_phase(len(community_cards))

        # Make decision (FIXED - no contradictions)
        decision = self._decide_action(
            hand_strength_category,
            hand_rank,
            win_probability,
            pot,
            current_bet,
            call_amount,
            self.stack,
            stacks,
            big_blind,
            phase,
            active_opponents,
            community_cards,
            action_history
        )

        return decision
    
    def _parse_hole_cards(self, card_indices: List[int]) -> List[Card]:
        """Convert card indices to Card objects"""
        cards = []
        for idx in card_indices:
            if idx == 0:
                continue
            rank_val = (idx % 13) + 2
            suit_val = idx // 13
            
            rank = Rank(rank_val)
            suit = Suit(suit_val)
            cards.append(Card(rank, suit))
        return cards
    
    def _parse_community_cards(self, card_indices: List[int]) -> List[Card]:
        """Convert community card indices to Card objects"""
        return self._parse_hole_cards(card_indices)
    
    def _update_opponent_models(self, action_history: list):
        """Update opponent profiles based on action history"""
        for phase, player_name, action, amount in action_history:
            if player_name == self.name:
                continue
            
            if player_name not in self.opponent_profiles:
                self.opponent_profiles[player_name] = OpponentProfile(player_name)
            
            self.opponent_profiles[player_name].update(action, phase)
            self.opponent_profiles[player_name].classify()
    
    def _evaluate_hand_strength(self, hole_cards: List[Card], community_cards: List[Card]) -> Tuple[str, HandRank]:
        """Evaluate hand strength and categorize"""
        if not hole_cards or len(hole_cards) < 2:
            return HandStrength.WEAK, HandRank.HIGH_CARD
        
        # Pre-flop: Use starting hand strength
        if not community_cards:
            return self._preflop_hand_strength(hole_cards)
        
        # Post-flop: Evaluate actual hand
        all_cards = hole_cards + community_cards
        if len(all_cards) >= 5:
            result = HandEvaluator.evaluate_hand(hole_cards, community_cards)
            
            # Categorize based on hand rank
            if result.hand_rank.value >= HandRank.STRAIGHT.value:
                return HandStrength.STRONG, result.hand_rank
            elif result.hand_rank.value >= HandRank.TWO_PAIR.value:
                return HandStrength.MEDIUM, result.hand_rank
            else:
                # Check for draws
                if self._has_draw(hole_cards, community_cards):
                    return HandStrength.DRAW, result.hand_rank
                return HandStrength.WEAK, result.hand_rank
        
        return HandStrength.WEAK, HandRank.HIGH_CARD
    
    def _preflop_hand_strength(self, hole_cards: List[Card]) -> Tuple[str, HandRank]:
        """Evaluate pre-flop hand strength"""
        if len(hole_cards) != 2:
            return HandStrength.WEAK, HandRank.HIGH_CARD
        
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.value, card2.rank.value
        
        # Pocket pairs
        if rank1 == rank2:
            if rank1 >= 10:  # TT+
                return HandStrength.STRONG, HandRank.PAIR
            elif rank1 >= 7:  # 77-99
                return HandStrength.MEDIUM, HandRank.PAIR
            else:
                return HandStrength.WEAK, HandRank.PAIR
        
        # High cards
        high, low = max(rank1, rank2), min(rank1, rank2)
        
        # Premium hands (AK, AQ, AJ, KQ)
        if high == 14:  # Ace
            if low >= 11:  # AJ+
                return HandStrength.STRONG, HandRank.HIGH_CARD
            elif low >= 10:  # AT
                return HandStrength.MEDIUM, HandRank.HIGH_CARD
        
        if high == 13 and low >= 11:  # KQ, KJ
            return HandStrength.MEDIUM, HandRank.HIGH_CARD
        
        # Suited connectors and high suited cards
        if card1.suit == card2.suit:
            if high - low <= 2:  # Suited connectors
                return HandStrength.MEDIUM, HandRank.HIGH_CARD
            if high >= 11:  # High suited
                return HandStrength.MEDIUM, HandRank.HIGH_CARD
        
        return HandStrength.WEAK, HandRank.HIGH_CARD
    
    def _has_draw(self, hole_cards: List[Card], community_cards: List[Card]) -> bool:
        """Check if hand has flush or straight draw potential"""
        all_cards = hole_cards + community_cards
        
        # Flush draw (4 of same suit)
        suit_counts = defaultdict(int)
        for card in all_cards:
            suit_counts[card.suit] += 1
            if suit_counts[card.suit] >= 4:
                return True
        
        # Straight draw
        ranks = sorted([card.rank.value for card in all_cards])
        unique_ranks = sorted(set(ranks))
        
        # Check for 4-card sequences
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] <= 4:
                return True
        
        return False
    
    def _simulate_win_probability(self, hole_cards: List[Card], community_cards: List[Card], num_opponents: int) -> float:
        """Monte Carlo simulation to estimate win probability"""
        if not hole_cards or len(hole_cards) < 2:
            return 0.0
        
        wins = 0
        ties = 0
        simulations = self.simulation_count
        
        # Cards already in play
        known_cards = set()
        for card in hole_cards + community_cards:
            known_cards.add((card.rank, card.suit))
        
        for _ in range(simulations):
            # Create fresh deck without known cards
            deck = [Card(rank, suit) for rank in Rank for suit in Suit]
            deck = [c for c in deck if (c.rank, c.suit) not in known_cards]
            random.shuffle(deck)
            
            # Deal remaining community cards
            remaining_community = 5 - len(community_cards)
            simulated_community = community_cards + deck[:remaining_community]
            deck = deck[remaining_community:]
            
            # Evaluate our hand
            our_result = HandEvaluator.evaluate_hand(hole_cards, simulated_community)
            
            # Simulate opponent hands
            opponent_results = []
            for _ in range(num_opponents):
                if len(deck) < 2:
                    break
                opp_cards = deck[:2]
                deck = deck[2:]
                opp_result = HandEvaluator.evaluate_hand(opp_cards, simulated_community)
                opponent_results.append(opp_result)
            
            # Compare hands
            our_value = (our_result.hand_rank.value, our_result.hand_value)
            
            best_opponent = None
            for opp in opponent_results:
                opp_value = (opp.hand_rank.value, opp.hand_value)
                if best_opponent is None or opp_value > best_opponent:
                    best_opponent = opp_value
            
            if best_opponent is None:
                wins += 1
            elif our_value > best_opponent:
                wins += 1
            elif our_value == best_opponent:
                ties += 1
        
        return (wins + ties * 0.5) / simulations
    
    def _get_active_opponents(self, action_history: list, num_players: int) -> List[str]:
        """Get list of active opponents who haven't folded"""
        folded = set()
        for phase, player_name, action, amount in action_history:
            if action == "fold":
                folded.add(player_name)
        
        active = []
        for player_name in self.opponent_profiles.keys():
            if player_name not in folded:
                active.append(player_name)
        
        return active
    
    def _determine_phase(self, num_community_cards: int) -> str:
        """Determine current betting phase"""
        if num_community_cards == 0:
            return "pre-flop"
        elif num_community_cards == 3:
            return "flop"
        elif num_community_cards == 4:
            return "turn"
        elif num_community_cards == 5:
            return "river"
        return "unknown"
    
    def _decide_action(self, hand_strength_category, hand_rank,
                    win_probability, pot, current_bet,
                    call_amount, my_stack, stacks,
                    big_blind, phase, active_opponents,
                    community_cards, action_history):

        opponent_types = {
            opp: self.opponent_profiles[opp].classified_type
            for opp in active_opponents
            if opp in self.opponent_profiles
        }
        dominant_type = self._get_dominant_opponent_type(opponent_types)

        # ===== TIER 1: MONSTER HANDS (65%+) =====
        if win_probability > 0.65:
            return PlayerAction.ALL_IN, my_stack

        # ===== TIER 2: STRONG HANDS (50–65%) =====
        if win_probability > 0.50:
            if call_amount == 0:
                bet_size = max(int(pot * 0.8), big_blind * 3)
                return PlayerAction.BET, min(bet_size, my_stack)

            elif call_amount < my_stack * 0.8:
                if random.random() < 0.4:  # add aggression
                    return PlayerAction.ALL_IN, my_stack
                return PlayerAction.CALL, call_amount

            else:
                return PlayerAction.ALL_IN, my_stack

        # ===== TIER 3: MEDIUM-STRONG (35–50%) =====
        if win_probability > 0.35:
            if call_amount == 0:
                bet_size = max(int(pot * 0.7), big_blind * 3)
                return PlayerAction.BET, min(bet_size, my_stack)

            elif call_amount < my_stack * 0.6:
                return PlayerAction.CALL, call_amount

            elif win_probability > 0.38:
                return PlayerAction.ALL_IN, my_stack

            else:
                # occasional bluff instead of pure fold
                if call_amount == 0 and random.random() < 0.3:
                    return PlayerAction.BET, max(big_blind * 3, int(pot * 0.7))
                return PlayerAction.FOLD, 0

        # ===== TIER 4: MEDIUM-WEAK (20–35%) =====
        if win_probability > 0.20:

            # 🔥 Exploit passive players
            if dominant_type == OpponentType.PASSIVE_BOT:
                if call_amount == 0 and random.random() < 0.65:
                    return PlayerAction.BET, max(big_blind * 3, int(pot * 0.7))

            # 🔥 Call wider vs bluff bots
            if dominant_type == OpponentType.BLUFF_BOT:
                if call_amount < pot * 0.9:
                    return PlayerAction.CALL, call_amount

            # 🔥 General semi-bluffing
            if call_amount == 0:
                if random.random() < 0.50:
                    return PlayerAction.BET, max(big_blind * 3, int(pot * 0.65))
                return PlayerAction.CHECK, 0

            elif call_amount < pot * 0.8:
                return PlayerAction.CALL, call_amount

            else:
                # 🔥 occasional aggression instead of folding
                if random.random() < 0.25:
                    return PlayerAction.ALL_IN, my_stack
                return PlayerAction.FOLD, 0

        # ===== TIER 5: WEAK HANDS (<20%) =====
        if call_amount == 0:

            # 🔥 Blind stealing
            if dominant_type == OpponentType.PASSIVE_BOT and random.random() < 0.55:
                return PlayerAction.BET, max(big_blind * 3, int(pot * 0.6))

            if phase == "pre-flop" and random.random() < 0.35:
                return PlayerAction.BET, big_blind * 3

            return PlayerAction.CHECK, 0

        else:
            if call_amount <= big_blind * 2:
                return PlayerAction.CALL, call_amount

            return PlayerAction.FOLD, 0
    
    def _get_dominant_opponent_type(self, opponent_types: Dict[str, str]) -> str:
        """Determine the dominant opponent type at the table"""
        if not opponent_types:
            return OpponentType.UNKNOWN
        
        type_counts = defaultdict(int)
        for opp_type in opponent_types.values():
            type_counts[opp_type] += 1
        
        return max(type_counts, key=type_counts.get)


# ============================================
# GAME RUNNER
# ============================================

if __name__ == "__main__":
    from game import PokerGame, GamePhase
    from baseplayers import RaisePlayer, FoldPlayer
    import time
    
    print("=" * 60)
    print("🃏  META POKER BOT TOURNAMENT  🃏")
    print("=" * 60)
    print("\nPlayers:")
    print("  1. MetaBot (Smart AI) - Adapts to opponent patterns")
    print("  2. AggroBot (Aggressive) - Raises aggressively")
    print("  3. RaiseBot2 (Aggressive) - Another raise bot")
    print("  4. FoldBot (Passive) - Folds often")
    print("\n" + "=" * 60)
    
    # Create players
    meta_bot = MetaPokerBot("MetaBot", 1000, simulation_count=100)  # Reduced from 300
    aggro_bot1 = RaisePlayer("AggroBot", 1000)
    aggro_bot2 = RaisePlayer("RaiseBot2", 1000)
    fold_bot = FoldPlayer("FoldBot", 1000)
    
    players = [meta_bot, aggro_bot1, aggro_bot2, fold_bot]
    
    # Create game
    game = PokerGame(players, big_blind=20)
    
    # Play multiple hands
    num_hands = 10  # Reduced from 15
    
    for hand_num in range(num_hands):
        print(f"\n{'='*60}")
        print(f"🎲  HAND #{hand_num + 1}")
        print(f"{'='*60}")
        
        # Start new hand
        if not game.start_new_hand():
            print("\n⚠️  Not enough active players. Game over!")
            break
        
        # Show initial stacks
        print("\n💰 Stacks:")
        for player in players:
            status = "💀 BROKE" if player.stack == 0 else f"${player.stack}"
            print(f"   {player.name}: {status}")
        
        # Play until hand completes
        max_actions = 100
        actions = 0
        
        while game.phase != GamePhase.SHOWDOWN and actions < max_actions:
            # Check if only one player left
            if game.num_active_players() == 1:
                active_player = game.players[game.active_player_index]
                if active_player.bet_amount == game.current_bet:
                    game.advance_game_phase()
                    game.display_game_state()
                    continue
            
            # Get current player
            current_player = game.players[game.active_player_index]
            
            # Get player action
            try:
                is_successful = game.get_player_input()
                if not is_successful:
                    # Force fold if action fails
                    game.player_action(PlayerAction.FOLD, 0)
                actions += 1
            except Exception as e:
                print(f"❌ Error with {current_player.name}: {e}")
                game.player_action(PlayerAction.FOLD, 0)
                actions += 1
            
            time.sleep(0.3)  # Small delay for readability
        
        # Show hand result
        print("\n" + "="*60)
        print("🏆  HAND COMPLETE")
        print("="*60)
        time.sleep(1)
    
    # Final results
    print("\n" + "="*60)
    print("🎊  TOURNAMENT RESULTS  🎊")
    print("="*60)
    
    print("\n📊 Final Stacks:")
    sorted_players = sorted(players, key=lambda p: p.stack, reverse=True)
    for i, player in enumerate(sorted_players, 1):
        profit = player.stack - 1000
        profit_str = f"+${profit}" if profit > 0 else f"-${abs(profit)}"
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "💀"
        print(f"   {emoji} {i}. {player.name:12} ${player.stack:4}  ({profit_str})")
    
    # MetaBot statistics
    print("\n🤖 MetaBot Analysis:")
    print(f"   Hands Played: {meta_bot.hands_played}")
    print(f"   Opponents Classified:")
    for opp_name, profile in meta_bot.opponent_profiles.items():
        if profile.total_actions > 0:
            print(f"      • {opp_name:12} → {profile.classified_type:15} "
                  f"(Aggression: {profile.get_aggression_frequency():.1%}, "
                  f"Fold: {profile.get_fold_frequency():.1%})")
    
    # Winner announcement
    winner = sorted_players[0]
    print("\n" + "="*60)
    if winner.name == "MetaBot":
        print("🎉  METABOT WINS THE TOURNAMENT! 🎉")
    else:
        print(f"🏆  {winner.name.upper()} WINS THE TOURNAMENT!")
    print("="*60)