from db import get_agents
from agents import decide_action

agents = get_agents()
for a in agents:
    print(f"Agent: {a['name']} | traits: {a['traits']} | inventory: {repr(a['inventory'])} | money: {a['money']} | mood: {a['mood']}")

print()
mira = next(a for a in agents if a['name'] == 'Mira')
leo = next(a for a in agents if a['name'] == 'Leo')

print("Simulating 10 decision rolls for Mira:")
for i in range(10):
    act, det = decide_action(mira, leo, pending_offer=None)
    print(f"  {i+1}. {act} {det}")

print()
print("Simulating 10 decision rolls for Leo:")
for i in range(10):
    act, det = decide_action(leo, mira, pending_offer=None)
    print(f"  {i+1}. {act} {det}")