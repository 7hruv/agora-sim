import httpx
from prompts import build_prompt
from db import get_recent_events, update_agent

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def call_llm(prompt):
    """Call Ollama LLM with timeout and fallback."""
    try:
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "temperature": 0.9,
                "max_tokens": 80,
                "stream": False
            },
            timeout=15.0
        )
        response.raise_for_status()
        data = response.json()
        dialogue = data.get("response", "...").strip()
        return dialogue if dialogue else "..."
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "..."

def generate_dialogue(agent_name, traits, mood, money, inventory, action_description, target):
    """Generate dialogue for an agent using LLM."""
    recent_events = get_recent_events(agent_name, limit=3)
    prompt = build_prompt(
        name=agent_name,
        traits=traits,
        mood=mood,
        money=money,
        inventory=inventory,
        recent_events=recent_events,
        action_description=action_description,
        target=target
    )
    dialogue = call_llm(prompt)
    return dialogue

def shift_mood(current_mood, delta):
    """Shift mood by delta (-2 to +2)."""
    mood_order = ["sad", "annoyed", "neutral", "happy"]
    idx = mood_order.index(current_mood) if current_mood in mood_order else 2
    new_idx = max(0, min(len(mood_order) - 1, idx + delta))
    return mood_order[new_idx]

def decide_action(agent, other_agent, pending_offer=None):
    """
    RULES-based decision for what action to take.
    Returns: (action_type, details)
    
    Actions: OFFER_TRADE, ACCEPT, REFUSE, IGNORE, CHAT
    """
    import random
    
    # If there's a pending offer from the other agent, respond to it
    if pending_offer:
        offerer, item, price = pending_offer
        
        # Simple rule: accept if price is fair or better
        fair_prices = {"fish": 5, "bread": 4}
        
        if item == "fish":
            if price <= 5:
                return ("ACCEPT", {"offerer": offerer, "item": item, "price": price})
            else:
                return ("REFUSE", {"offerer": offerer, "item": item, "price": price})
        elif item == "bread":
            if price <= 4:
                return ("ACCEPT", {"offerer": offerer, "item": item, "price": price})
            else:
                return ("REFUSE", {"offerer": offerer, "item": item, "price": price})
    
    # No pending offer - decide own action
    roll = random.random()
    
    # 40% chance to offer trade
    if roll < 0.4:
        # Decide what to buy based on inventory
        if agent["inventory"] == "3 fish":
            # Mira has fish, wants bread
            return ("OFFER_TRADE", {"item": "bread", "price": 4, "buyer": agent["name"], "seller": other_agent["name"]})
        elif agent["inventory"] == "3 bread":
            # Leo has bread, wants fish
            return ("OFFER_TRADE", {"item": "fish", "price": 5, "buyer": agent["name"], "seller": other_agent["name"]})
        else:
            # Mixed inventory - still interested in what other has
            if other_agent["inventory"].find("fish") >= 0:
                return ("OFFER_TRADE", {"item": "fish", "price": 5, "buyer": agent["name"], "seller": other_agent["name"]})
            elif other_agent["inventory"].find("bread") >= 0:
                return ("OFFER_TRADE", {"item": "bread", "price": 4, "buyer": agent["name"], "seller": other_agent["name"]})
    
    # 30% chance to chat
    elif roll < 0.7:
        return ("CHAT", {})
    
    # 30% chance to ignore (do nothing meaningful)
    else:
        return ("IGNORE", {})

def resolve_trade(action_details, buyer_name, seller_name):
    """
    Resolve a trade between buyer and seller.
    Returns: (success: bool, message: str, buyer_delta_money, seller_delta_money, item_transferred)
    """
    item = action_details["item"]
    price = action_details["price"]
    
    prices = {"fish": 5, "bread": 4}
    
    # Check if price matches fixed price
    if price == prices.get(item):
        # Trade succeeds at fixed price
        return (True, f"Trade: {price} coins for {item}", -price, price, item)
    elif price == prices.get(item) - 1:
        # Haggle succeeded
        return (True, f"Trade (haggled): {price} coins for {item}", -price, price, item)
    else:
        return (False, "Price mismatch", 0, 0, None)
