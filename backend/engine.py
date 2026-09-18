#   ===== START backend/engine.py =====

"""
Trade engine for Agora - handles round logic, trade resolution, and mood updates.
"""

# Fixed prices
FISH_PRICE = 5
BREAD_PRICE = 4
MAX_OFFER_PRICE = 6  # Price cap enforcement


def get_item_price(item: str) -> int:
    """Get the base price of an item."""
    if item == "fish":
        return FISH_PRICE
    elif item == "bread":
        return BREAD_PRICE
    return 0


def enforce_price_cap(action: str, item: str, price: int) -> tuple:
    """
    Fix #5: If any agent tries to offer more than 6 coins for bread or fish,
    convert the action to REFUSE.
    
    Returns: (adjusted_action, adjusted_price)
    """
    if action == "OFFER_TRADE" and item in ["fish", "bread"]:
        if price > MAX_OFFER_PRICE:
            return "REFUSE", price
    return action, price


def calculate_greedy_offer(item: str) -> int:
    """
    Fix #4: When Mira (greedy) initiates OFFER_TRADE, her offered price
    must be item value minus 1 or 2 coins (never more than item value).
    """
    base_price = get_item_price(item)
    # Greedy: offer 1-2 coins less than value
    import random
    discount = random.choice([1, 2])
    return max(1, base_price - discount)


def decide_action(actor_name: str, actor_data: dict, target_data: dict, 
                  pending_offers: list, round_num: int) -> dict:
    """
    Rule-based action decision (not LLM).
    Returns dict with action, item, price, target.
    """
    traits = actor_data.get("traits", "")
    inventory = actor_data.get("inventory", {})
    money = actor_data.get("money", 0)
    mood = actor_data.get("mood", "neutral")
    
    other_name = target_data.get("name", "other")
    other_inventory = target_data.get("inventory", {})
    other_money = target_data.get("money", 0)
    
    # Check for pending offers from other agent
    pending_from_other = [o for o in pending_offers if o.get("from") == other_name]
    
    # Default action
    action = "CHAT"
    item = None
    price = None
    target = other_name
    
    # If there's a pending offer, consider responding
    if pending_from_other:
        offer = pending_from_other[0]
        offer_item = offer.get("item")
        offer_price = offer.get("price")
        offer_type = offer.get("type")  # "buy" or "sell"
        
        # Decide whether to accept, refuse, or haggle
        if "friendly" in traits.lower() or "honest" in traits.lower():
            # More likely to accept fair deals
            if offer_type == "buy" and offer_price >= get_item_price(offer_item):
                action = "ACCEPT"
                item = offer_item
                price = offer_price
            elif offer_type == "sell" and offer_price <= get_item_price(offer_item):
                action = "ACCEPT"
                item = offer_item
                price = offer_price
            else:
                # Unfair offer
                if "cautious" in traits.lower():
                    action = "REFUSE"
                else:
                    action = "REFUSE"
                item = offer_item
                price = offer_price
        elif "greedy" in traits.lower():
            # Greedy agents haggle or refuse unfair deals
            if offer_type == "buy" and offer_price < get_item_price(offer_item):
                # They're offering too little - refuse or haggle
                action = "REFUSE"
                item = offer_item
                price = offer_price
            elif offer_type == "sell":
                # They're selling - greedy wants it cheap
                if offer_price <= get_item_price(offer_item) - 1:
                    action = "ACCEPT"
                    item = offer_item
                    price = offer_price
                else:
                    action = "REFUSE"
                    item = offer_item
                    price = offer_price
        else:
            # Default: accept if fair, refuse otherwise
            if offer_price == get_item_price(offer_item):
                action = "ACCEPT"
                item = offer_item
                price = offer_price
            else:
                action = "REFUSE"
                item = offer_item
                price = offer_price
    
    # No pending offer - decide to initiate something
    else:
        # Greedy agents initiate trades more often
        if "greedy" in traits.lower():
            action = "OFFER_TRADE"
            # Look for items the other has
            if other_inventory.get("fish", 0) > 0:
                item = "fish"
                # Fix #4: Greedy offers less than value
                price = calculate_greedy_offer(item)
            elif other_inventory.get("bread", 0) > 0:
                item = "bread"
                price = calculate_greedy_offer(item)
            else:
                # No items to buy, maybe sell own items
                if inventory.get("fish", 0) > 0:
                    item = "fish"
                    price = get_item_price(item)  # Ask full price when selling
                elif inventory.get("bread", 0) > 0:
                    item = "bread"
                    price = get_item_price(item)
                else:
                    action = "CHAT"
        
        elif "friendly" in traits.lower():
            # Friendly agents chat more
            import random
            if random.random() < 0.6:
                action = "CHAT"
            else:
                action = "OFFER_TRADE"
                if other_inventory.get("fish", 0) > 0:
                    item = "fish"
                    price = get_item_price(item)  # Fair price
                elif inventory.get("bread", 0) > 0:
                    item = "bread"
                    price = get_item_price(item)
        
        elif "cautious" in traits.lower():
            # Cautious agents rarely initiate
            import random
            if random.random() < 0.3:
                action = "OFFER_TRADE"
                if other_inventory.get("fish", 0) > 0:
                    item = "fish"
                    price = get_item_price(item) - 1  # Slightly cautious on price
                elif inventory.get("bread", 0) > 0:
                    item = "bread"
                    price = get_item_price(item)
            else:
                action = "CHAT"
        else:
            # Default behavior
            import random
            choice = random.random()
            if choice < 0.4:
                action = "CHAT"
            elif choice < 0.7:
                action = "OFFER_TRADE"
                if other_inventory.get("fish", 0) > 0:
                    item = "fish"
                    price = get_item_price(item)
                elif inventory.get("bread", 0) > 0:
                    item = "bread"
                    price = get_item_price(item)
    
    # Fix #5: Enforce price cap
    action, price = enforce_price_cap(action, item, price) if item else (action, price)
    
    return {
        "action": action,
        "item": item,
        "price": price,
        "target": target
    }


def resolve_trade(action: str, actor: str, target: str, item: str, price: int,
                  actor_data: dict, target_data: dict) -> dict:
    """
    Resolve a trade action and return results.
    Returns dict with success, new_actor_data, new_target_data, mood changes.
    """
    result = {
        "success": False,
        "actor_data": actor_data.copy(),
        "target_data": target_data.copy(),
        "mood_actor": actor_data.get("mood", "neutral"),
        "mood_target": target_data.get("mood", "neutral"),
        "description": ""
    }
    
    actor_inv = actor_data.get("inventory", {}).copy()
    actor_money = actor_data.get("money", 0)
    target_inv = target_data.get("inventory", {}).copy()
    target_money = target_data.get("money", 0)
    
    if action == "ACCEPT":
        # Find the pending offer and execute trade
        # For simplicity, assume the target had made an offer to buy/sell
        
        # Determine trade direction based on who has the item
        if actor_inv.get(item, 0) > 0:
            # Actor sells to target
            if target_money >= price:
                actor_inv[item] -= 1
                actor_money += price
                target_inv[item] = target_inv.get(item, 0) + 1
                target_money -= price
                result["success"] = True
                result["mood_actor"] = "happy"
                result["mood_target"] = "happy"
                result["description"] = f"{actor} sold {item} to {target} for {price} coins"
            else:
                result["description"] = f"{target} cannot afford {item}"
                result["mood_actor"] = "annoyed"
                result["mood_target"] = "sad"
                
        elif target_inv.get(item, 0) > 0:
            # Target sells to actor
            if actor_money >= price:
                target_inv[item] -= 1
                target_money += price
                actor_inv[item] = actor_inv.get(item, 0) + 1
                actor_money -= price
                result["success"] = True
                result["mood_actor"] = "happy"
                result["mood_target"] = "happy"
                result["description"] = f"{actor} bought {item} from {target} for {price} coins"
            else:
                result["description"] = f"{actor} cannot afford {item}"
                result["mood_actor"] = "sad"
                result["mood_target"] = "annoyed"
        else:
            result["description"] = f"No one has {item} to trade"
            result["mood_actor"] = "neutral"
            result["mood_target"] = "neutral"
    
    elif action == "REFUSE":
        result["description"] = f"{actor} refused the offer"
        result["mood_actor"] = "annoyed"
        result["mood_target"] = "sad"
    
    elif action == "IGNORE":
        result["description"] = f"{actor} ignored {target}"
        result["mood_actor"] = "neutral"
        result["mood_target"] = "neutral"
    
    elif action == "CHAT":
        result["description"] = f"{actor} chatted with {target}"
        # Friendly chat drifts toward happy
        if actor_data.get("mood") in ["sad", "annoyed"]:
            result["mood_actor"] = "neutral"
        elif actor_data.get("mood") == "neutral":
            result["mood_actor"] = "happy"
        else:
            result["mood_actor"] = "happy"
            
        if target_data.get("mood") in ["sad", "annoyed"]:
            result["mood_target"] = "neutral"
        elif target_data.get("mood") == "neutral":
            result["mood_target"] = "happy"
        else:
            result["mood_target"] = "happy"
    
    elif action == "OFFER_TRADE":
        result["description"] = f"{actor} offered to trade {item} for {price} coins"
        result["mood_actor"] = actor_data.get("mood", "neutral")
        result["mood_target"] = target_data.get("mood", "neutral")
    
    result["actor_data"]["inventory"] = actor_inv
    result["actor_data"]["money"] = actor_money
    result["target_data"]["inventory"] = target_inv
    result["target_data"]["money"] = target_money
    
    return result


def update_mood(current_mood: str, event_mood: str) -> str:
    """Update mood based on event, with some inertia."""
    mood_order = ["sad", "annoyed", "neutral", "happy"]
    
    current_idx = mood_order.index(current_mood) if current_mood in mood_order else 2
    event_idx = mood_order.index(event_mood) if event_mood in mood_order else 2
    
    # Move halfway toward the event mood
    diff = event_idx - current_idx
    if abs(diff) <= 1:
        return event_mood
    else:
        new_idx = current_idx + (1 if diff > 0 else -1)
        return mood_order[new_idx]


#   ===== END backend/engine.py =====