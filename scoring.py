from collections import Counter

def calculate_hand_score(hand_list, joker_list, run_discards):
    """ 
    Calculates the score for the current hand, applying all card modifiers
    and Joker effects.
    """
    if not hand_list: 
        return 0, 1, [], 0

    base_sum = sum(c.value for c in hand_list)
    additive_mult = 1
    final_multiplier = 1
    coin_bonus = 0 
    bonus_points = 0
    breakdown = []

    # 1. Analyze Hand Rank (Pair, Flush, etc.)
    ranks = [c.rank for c in hand_list]
    rank_counts = Counter(ranks).values()
    
    has_pair = False
    has_trip = False
    
    if 4 in rank_counts:
        additive_mult += 8
        breakdown.append("Quad(+8)")
    elif 3 in rank_counts:
        additive_mult += 3
        breakdown.append("Trip(+3)")
        has_trip = True
    
    pair_count = list(rank_counts).count(2)
    if pair_count > 0:
        bonus = pair_count * 2
        additive_mult += bonus
        breakdown.append(f"{pair_count} Pair(+{bonus})")
        has_pair = True

    suits = [c.suit for c in hand_list]
    if 5 in Counter(suits).values():
        additive_mult += 3
        breakdown.append("Flush(+3)")

    colors = [c.color_type for c in hand_list]
    if 5 in Counter(colors).values():
        additive_mult += 2
        breakdown.append("Color(+2)")

    # Straights
    sorted_ranks = sorted([c.value for c in hand_list])
    unique_ranks = sorted(list(set(sorted_ranks)))
    has_3_straight = False
    consecutive = 0
    for i in range(len(unique_ranks) - 1):
        if unique_ranks[i+1] == unique_ranks[i] + 1:
            consecutive += 1
            if consecutive >= 2: has_3_straight = True
        else: consecutive = 0
    # Ace low straight check (A, 2, 3)
    if {14, 2, 3}.issubset(set(unique_ranks)): has_3_straight = True

    # 2. Card Modifiers
    for card in hand_list:
        if card.modifier == "bonus_chips":
            bonus_points += 10
            breakdown.append("Bonus(+10)")
        elif card.modifier == "mult_plus":
            additive_mult += 4
            breakdown.append("Mult(+4)")

    # 3. Joker Effects
    for joker in joker_list:
        if joker.key == "pear_up" and (has_pair or has_trip): 
            additive_mult += 8
            breakdown.append("PearUp(+8)")
        if joker.key == "triple_treat" and has_trip:
            additive_mult += 12
            breakdown.append("TripTreat(+12)")
        if joker.key == "inflation" and len(hand_list) <= 4:
            additive_mult += 12
            breakdown.append("Inflation(+12)")
        if joker.key == "the_regular":
            additive_mult += 4
            breakdown.append("Regular(+4)")
        if joker.key == "waste_management":
            wm_bonus = run_discards // 3
            if wm_bonus > 0:
                additive_mult += wm_bonus
                breakdown.append(f"WasteMan(+{wm_bonus})")
        if joker.key == "diamond_geezer":
            diamond_count = sum(1 for c in hand_list if c.suit == 'Diamonds')
            if diamond_count > 0:
                dg_bonus = diamond_count * 4
                additive_mult += dg_bonus
                breakdown.append(f"Geezer(+{dg_bonus})")
        if joker.key == "wishing_well":
            wish_hits = sum(1 for c in hand_list if c.value in [14, 2, 3]) 
            if wish_hits > 0:
                coin_bonus += wish_hits
                breakdown.append(f"Wish(+${wish_hits})")
    
    # 4. Final Multipliers
    for joker in joker_list:
        if joker.key == "multi_python" and has_3_straight:
            final_multiplier *= 2
            breakdown.append("Python(x2)")

    total_mult = additive_mult * final_multiplier
    total_base = base_sum + bonus_points
    
    return total_base, total_mult, breakdown, coin_bonus