AGENT_PROMPT = """You are {name}. Traits: {traits}. Current mood: {mood}.
You currently have {money} coins, {inventory_details}.
Recent memory (last 5 rounds):
{last_5_events_as_bullets}

You are about to: {action_description}
{action_rules}

Say ONE short line of dialogue to {target}, in character, matching your mood.
Max 2 sentences. No narration, no emojis, no explanation.
Do not repeat dialogue you have used in the last 5 rounds. Be creative."""

ACTION_RULES = {
    "OFFER_TRADE": "Your dialogue MUST state a specific price for a specific item. Example: 'I'll buy your fish for 4 coins.'",
    "ACCEPT": "Your dialogue MUST be a direct acceptance. Examples: 'Deal!', 'I accept.', 'Agreed.' Do NOT ask questions.",
    "REFUSE": "Your dialogue MUST be a direct rejection. Examples: 'No.', 'I refuse.', 'Not interested.'",
    "CHAT": "Your dialogue should be friendly conversation, no trade involved.",
    "IGNORE": "You may say something dismissive or stay silent."
}

def parse_inventory_details(inventory_str):
    """Parse inventory string like '3 fish' into detailed description."""
    parts = inventory_str.split()
    if len(parts) >= 2:
        count = parts[0]
        item = parts[1]
        return f"{count} {item}, and 0 of other items"
    return inventory_str

def build_prompt(name, traits, mood, money, inventory, recent_events, action_description, target):
    # Format recent events as bullet points (last 5 for anti-repetition)
    if recent_events:
        bullets = []
        for ev in recent_events[-5:]:
            dialogue_preview = ev.get('dialogue', '')[:40]
            if len(ev.get('dialogue', '')) > 40:
                dialogue_preview += "..."
            bullets.append(f"- Round {ev['round']}: {ev['actor']} {ev['action'].lower()} with {ev['target']}: \"{dialogue_preview}\"")
        last_5_events_as_bullets = "\n".join(bullets)
    else:
        last_5_events_as_bullets = "- No prior events"
    
    # Determine action type from description for rules
    # Check for specific action keywords in the description (order matters - check refuse before offer)
    action_type = "CHAT"  # default
    desc_lower = action_description.lower()
    if "refuse" in desc_lower or "refusing" in desc_lower:
        action_type = "REFUSE"
    elif "accept" in desc_lower or "accepting" in desc_lower:
        action_type = "ACCEPT"
    elif "offer" in desc_lower or "offering" in desc_lower:
        action_type = "OFFER_TRADE"
    elif "ignore" in desc_lower or "ignoring" in desc_lower:
        action_type = "IGNORE"
    
    action_rules = ACTION_RULES.get(action_type, "")
    
    # Parse inventory into detailed format
    inventory_details = parse_inventory_details(inventory)
    
    return AGENT_PROMPT.format(
        name=name,
        traits=traits,
        mood=mood,
        money=money,
        inventory_details=inventory_details,
        last_5_events_as_bullets=last_5_events_as_bullets,
        action_description=action_description,
        action_rules=action_rules,
        target=target
    )
