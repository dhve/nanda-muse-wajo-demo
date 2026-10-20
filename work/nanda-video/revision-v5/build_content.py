from pathlib import Path
import json
P=Path(__file__).resolve().parent
rows=[
('goal','Alice and Bob use different apps',"Alice runs a bakery using Muse. Bob is her customer and uses Wajo. They already know who they want to contact. Let's see how their agents connect, including when the bakery contacts Bob.","Alice stays on the left in blue. Bob stays on the right in green. Label every screen as an illustration."),
('connect_alice','1. Alice sets up her agent',"Alice pastes the setup prompt into Muse, using her bakery email. Her agent follows the website instructions and prepares its AgentBox.","Show Alice's complete setup prompt, then the expected email verification request."),
('connect_bob','2. Bob sets up his agent',"Bob does the same in Wajo with his own email. His agent can run in a different app from Alice's.","Show Bob's complete setup prompt, then the expected email verification request."),
('verify','3. Each person verifies their email',"Each person enters the code sent to their own inbox. The code proves control of that email account. The example code on screen is fictional.","Show the setup email and a masked credential. Paste the illustrative code. Use your own code in a real setup."),
('known','4. Bob contacts a bakery he knows',"Bob already knows bakery dot com. He asks his agent, 'Ask at bakery dot com: What cakes are available?'", "Show Bob's exact known-domain prompt in Wajo. No query for unknown businesses."),
('domain','The bakery publishes its contact details',"In this example, the bakery has published its agent's contact details on its website. Bob's agent uses that direct path. An index lookup isn't needed here.","Show bakery.com leading directly to the published contact endpoint. This is an assumed, domain-authorized publication, separate from Alice's email verification."),
('menu','5. Alice replies with the menu',"AgentBox carries Bob's question to Alice. She checks her inbox and replies, 'We have chocolate and vanilla cakes.' Bob's agent receives the menu.","Show question moving right to left through AgentBox, Alice's check and reply prompts, then the menu moving left to right."),
('later','Later, the bakery starts a new message',"Later, after Bob has placed an order and agreed to updates, Alice starts a new message. She asks her agent to tell Bob that his cake is ready.","Show the later-time label and Bob's consent. Alice enters the exact update prompt in Muse. The order itself is outside the walkthrough."),
('resolve','6. Resolve Bob’s known agent ID',"Alice knows Bob's registered ID, bob at gmail dot com. Bob doesn't own gmail dot com or need a website. Her agent asks the index to resolve his ID to his hosted agent card.","Index sits above the agents. The request is bob@gmail.com. Index returns a pointer to Bob's hosted card, not a list of agents."),
('card','Read the card and check permissions',"Alice's agent verifies the link between Bob's ID and his card. The card provides the current endpoint, where his agent can be contacted. The sending agent checks the required permissions before proceeding.","Show known ID, hosted card, contact endpoint and permission check in order. Card hosts can be separate from Index and the agent runtime."),
('deliver','7. AgentBox delivers the update',"AgentBox delivers the update to Bob. The index handles identity resolution, while AgentBox carries the message between their agents.","Show the update moving left to right through AgentBox. Keep Index above and outside the message path."),
('reply','8. Bob replies to Alice',"Bob checks his inbox and replies, 'Thanks. I'll collect it at two p.m.' Alice receives his reply in Muse, completing the exchange.","Show Bob's inbox and exact reply prompt, then the reply moving right to left. Alice checks her inbox and receives it."),
('roles','Known ID → card → contact endpoint',"Both people keep their own apps. The index connects a known identity to the agent's current contact details, including for people who don't control a domain. Permission still governs every connection.","Show Index resolving the ID above a horizontal AgentBox message path. Do not imply that resolving an ID authorizes delivery."),
('end','Try it with your own agent',"You can read the matching prompts in the guide. Open the setup page to connect your own agent, and try a message.","Hold the readable QR and links to the setup page, Index and AgentBox. QR points to nandaindex.org.")]
prompts=[
('setup_alice','Alice in Muse',"Set up Alice's Bakery at my.nandaindex.org using alice@bakery.com. We offer birthday cakes."),
('setup_bob','Bob in Wajo','Set me up at my.nandaindex.org using bob@gmail.com.'),
('verify','Each person in their own app','My code is 123456.'),
('ask','Bob in Wajo','Ask @bakery.com: What cakes are available?'),
('check_alice','Alice in Muse','Check my AgentBox.'),
('menu_reply','Alice in Muse','Reply: We have chocolate and vanilla cakes.'),
('check_bob','Bob in Wajo','Check my AgentBox.'),
('update','Alice in Muse','Message bob@gmail.com: Your cake is ready.'),
('reply','Bob in Wajo',"Reply: Thanks. I'll collect it at 2 pm.")]
scene_prompts={'connect_alice':['setup_alice'],'connect_bob':['setup_bob'],'verify':['verify'],'known':['ask'],'menu':['check_alice','menu_reply','check_bob'],'later':['update'],'deliver':['check_bob'],'reply':['reply','check_alice']}
scenes=[]; t=0
for id,title,narration,screen in rows:
    dur=round(max(8,len(narration.split())/2.45+.5),2)
    scenes.append(dict(id=id,title=title,narration=narration,screen=screen,duration=dur,start=round(t,2),prompts=scene_prompts.get(id,[])))
    t+=dur
(P/'scenes.json').write_text(json.dumps({'version':5,'timing':'provisional until voice alignment','scenes':scenes},indent=2)+'\n')
(P/'prompts.json').write_text(json.dumps({'version':5,'illustrative':True,'prompts':[dict(id=a,app=b,text=c) for a,b,c in prompts]},indent=2)+'\n')
(P/'narration.txt').write_text('\n\n'.join(s['narration'] for s in scenes)+'\n')
print({'words':sum(len(s['narration'].split()) for s in scenes),'estimated_seconds':round(t,2),'prompts':len(prompts)})
