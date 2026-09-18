import httpx
from prompts import build_prompt
from db import get_recent_events

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
FAIR_PRICES = {"fish": 5, "bread": 4}
MAX_PRICE = 6


def call_llm(prompt):
    try:
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "temperature": 0.95,
                "max_tokens": 80,
                "stream": False
            },
            timeout=20.0
        )
        response.raise_for_status()
        data = response.json()
        dialogue = data.get("response", "...").strip()
        return dialogue if dialogue else "..."
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "..."


def generate_dialogue(agent_name, traits, mood, money, inventory, action_description, target):
    recent_events = get_recent_events(agent_name, limit=5)
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
    return call_llm(prompt)


def shift_mood(current_mood, delta):
    mood_order = ["sad", "annoyed", "neutral", "happy"]
    idx = mood_order.index(current_mood) if current_mood in mood_order else 2
    new_idx = max(0, min(len(mood_order) - 1, idx + delta))
    return mood_order[new_idx]


def decide_action(agent, other_agent, pending_offer=None):
    """Returns (action_type, details_dict)."""
    import random

    traits_lower = (agent.get("traits") or "").lower()
    is_greedy = "greedy" in traits_lower
    other_inv = other_agent.get("inventory", "") or ""

    # ---------- RESPOND TO PENDING OFFER ----------
    if pending_offer:
        offerer, item, price, side = pending_offer
        fair = FAIR_PRICES.get(item, 999)
        if price > MAX_PRICE:
            return ("REFUSE", {"offerer": offerer, "item": item, "price": price})

        if side == "buy":
            # Other agent wants to BUY from me. I'm the seller.
            # Greedy seller wants full price; friendly seller accepts fair-1.
            threshold = fair if is_greedy else fair - 1
            if price >= threshold:
                return ("ACCEPT", {"offerer": offerer, "item": item, "price": price})
            return ("REFUSE", {"offerer": offerer, "item": item, "price": price})
        else:
            # Other agent wants to SELL to me. I'm the buyer.
            # Greedy buyer wants discount; friendly buyer pays fair.
            threshold = fair - 1 if is_greedy else fair
            if price <= threshold:
                return ("ACCEPT", {"offerer": offerer, "item": item, "price": price})
            return ("REFUSE", {"offerer": offerer, "item": item, "price": price})

    # ---------- INITIATE ----------
    roll = random.random()

    # 55% - offer to buy something the other has
    if roll < 0.55:
        item = None
        if "fish" in other_inv and _count(other_inv, "fish") > 0:
            item = "fish"
        elif "bread" in other_inv and _count(other_inv, "bread") > 0:
            item = "bread"

        if item:
            fair = FAIR_PRICES[item]
            # Greedy lowballs by exactly 1. Non-greedy pays fair.
            price = max(1, fair - 1) if is_greedy else fair
            if price > MAX_PRICE:
                return ("CHAT", {})
            return ("OFFER_TRADE", {
                "item": item,
                "price": price,
                "buyer": agent["name"],
                "seller": other_agent["name"]
            })
        return ("CHAT", {})

    # 40% - chat
    if roll < 0.95:
        return ("CHAT", {})

    # 5% - ignore
    return ("IGNORE", {})


def _count(inv_str, item):
    for part in inv_str.split(","):
        tokens = part.strip().split()
        if len(tokens) >= 2 and tokens[1].lower() == item:
            try:
                return int(tokens[0])
            except ValueError:
                return 0
    return 0


def resolve_trade(action_details, buyer_name, seller_name):
    item = action_details.get("item")
    price = action_details.get("price")
    fair = FAIR_PRICES.get(item)
    if fair is None:
        return (False, "Unknown item", 0, 0, None)
    if price <= fair:
        return (True, f"Trade: {price} coins for {item}", -price, price, item)
    return (False, "Price mismatch", 0, 0, None)