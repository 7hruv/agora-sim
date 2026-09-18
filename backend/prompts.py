#   ===== START backend/prompts.py =====

"""
LLM Prompt Templates for Agora agents.
"""

def build_agent_prompt(name: str, traits: str, mood: str, money: int, 
                       inventory: dict, recent_events: list, action: str, 
                       target: str, action_desc: str, used_dialogues: list) -> str:
    """
    Build the LLM prompt for an agent's turn.
    
    Args:
        name: Agent name (Mira or Leo)
        traits: Comma-separated traits
        mood: Current mood string
        money: Current coin count
        inventory: Dict with item counts {'fish': 2, 'bread': 0}
        recent_events: List of last 3 events as bullet strings
        action: The action being taken (OFFER_TRADE, ACCEPT, REFUSE, IGNORE, CHAT)
        target: Target agent name
        action_desc: Description of what the action means
        used_dialogues: List of dialogues used in last 5 rounds by this agent
    """
    
    # Format inventory for display
    fish_count = inventory.get('fish', 0)
    bread_count = inventory.get('bread', 0)
    inventory_str = f"You currently have {money} coins, {fish_count} fish, and {bread_count} bread."
    
    # Format recent memory
    if recent_events:
        memory_str = "\n".join(recent_events)
    else:
        memory_str = "No recent events."
    
    # Anti-repetition instruction
    if used_dialogues:
        anti_repeat = f"Do not repeat dialogue you have used in the last 5 rounds. Be creative.\nAvoid these phrases: {', '.join(used_dialogues[:5])}"
    else:
        anti_repeat = "Do not repeat dialogue you have used in the last 5 rounds. Be creative."
    
    # Action-specific dialogue instructions
    action_instructions = {
        "OFFER_TRADE": "Your dialogue MUST state a specific price for a specific item. Example: 'I'll buy your fish for 4 coins.'",
        "ACCEPT": "Your dialogue MUST be a direct acceptance. Use phrases like 'Deal!', 'I accept.', 'Agreed.'. Do NOT ask questions.",
        "REFUSE": "Your dialogue MUST be a direct rejection. Use phrases like 'No.', 'I refuse.', 'Not interested.'",
        "IGNORE": "Your dialogue MUST be a dismissal. Use phrases like '*ignores*', '...', 'Whatever.'",
        "CHAT": "Casual conversation, no trade talk. Just friendly or neutral chat."
    }
    
    dialogue_instruction = action_instructions.get(action, "Say something in character.")
    
    prompt = f"""You are {name}. Traits: {traits}. Current mood: {mood}.
{inventory_str}
Recent memory:
{memory_str}

You are about to: {action_desc}
{dialogue_instruction}
{anti_repeat}

Say ONE short line of dialogue to {target}, in character, matching your mood.
Max 2 sentences. No narration, no emojis, no explanation.
Only output the dialogue text, nothing else."""

    return prompt


def get_action_description(action: str, item: str = None, price: int = None, 
                           target: str = None) -> str:
    """Get a human-readable description of the action for the prompt."""
    
    descriptions = {
        "OFFER_TRADE": f"Offer to trade: {'buy' if target else 'sell'} {item} for {price} coins",
        "ACCEPT": f"Accept the offer for {item} at {price} coins",
        "REFUSE": f"Refuse the offer for {item} at {price} coins",
        "IGNORE": "Ignore the other agent",
        "CHAT": "Have a casual conversation"
    }
    
    return descriptions.get(action, action)

#   ===== END backend/prompts.py =====