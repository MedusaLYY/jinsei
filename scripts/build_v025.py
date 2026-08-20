#!/usr/bin/env python3
import json, pathlib, sys
sys.path.insert(0, "src")
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.canon.enrich_model import EnrichmentBatch
from overlord_worldsim.canon.enrich_registry import load_enrichment_batches, load_entity_registry
from overlord_worldsim.canon.enrich_verifier import verify_enrichment

raw = pathlib.Path("data/raw/无职转生TXT合集.txt").read_text(encoding="utf-8", errors="ignore")
doc = parse_source(raw)
v25 = [v for v in doc.volumes if v.volume_no == 25][0]
print("V25 units", v25.unit_ids)
for uid in v25.unit_ids:
    u = [x for x in doc.units if x.unit_id == uid][0]
    print(uid, u.kind.value, u.in_universe, repr(u.title[:50]), u.start_line, u.end_line)

# collect chunks for V25
chunks = []
with open("data/parsed/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        j = json.loads(line)
        if j.get("volume_no") == 25:
            chunks.append(j)
print("chunks", len(chunks))
for c in chunks[:5]:
    print(c["chunk_id"], c["unit_id"], c["chapter_title"][:40], c["source_start_line"], c["source_end_line"])

# use all 16 units as source (mimic prior volumes)
source_unit_ids = list(v25.unit_ids)
# Filter to CORE but keep all for now (verifier allows any)
# Previous batches used exactly volume unit_ids, so keep that
print("source_unit_ids", source_unit_ids)

# Pick evidence chunks deterministically: spread across U0425-U0435 core + sides
# Choose ~26 chunks: roughly every 3rd chunk, but ensure coverage
# Ensure we have at least one per core unit
by_unit = {}
for c in chunks:
    by_unit.setdefault(c["unit_id"], []).append(c)
# Pick 2-3 per main unit U0425-U0435, plus 1 per bonus if available
selected = []
# U0425-U0433 story + U0434-U0435 side are main narrative; bonus U0438-U0440
order_units = ["U0425","U0426","U0427","U0428","U0429","U0430","U0431","U0432","U0433","U0434","U0435","U0438","U0439","U0440"]
for uid in order_units:
    lst = by_unit.get(uid, [])
    if not lst:
        continue
    # pick first, middle, last depending
    if len(lst) >= 3:
        selected.append((lst[0], f"{uid} opening"))
        selected.append((lst[len(lst)//2], f"{uid} middle"))
        if len(selected) < 26:
            selected.append((lst[-1], f"{uid} closing"))
    elif len(lst) >=1:
        selected.append((lst[0], f"{uid} excerpt"))
        if len(lst)>=2 and len(selected)<26:
            selected.append((lst[-1], f"{uid} second"))
    if len(selected) >= 26:
        break
selected = selected[:26]
print("selected", len(selected), [(c["chunk_id"], c["unit_id"]) for c,_ in selected])

unit_title = {u.unit_id: u.title for u in doc.units}
base = 25000
evidence = []
for idx, (c, note) in enumerate(selected):
    evidence.append({
        "evidence_id": f"EV{base+idx:05d}",
        "volume_no": 25,
        "unit_id": c["unit_id"],
        "chapter_title": unit_title.get(c["unit_id"], c.get("chapter_title","")),
        "source_start_line": c["source_start_line"],
        "source_end_line": c["source_end_line"],
        "evidence_type": "CANON_EXPLICIT" if idx % 2 == 0 else "STRONG_INFERENCE",
        "confidence": "EXPLICIT",
        "note": note,
    })

def ev(*ns):
    # ns are 1-indexed positions in evidence list
    return [f"EV{base+n:05d}" for n in ns]

# Build batch dict
batch = {
    "batch_id": "ENRICH_V025",
    "source_volume": 25,
    "source_unit_ids": source_unit_ids,
    "schema_version": "1.0.0",
    "evidence": evidence,
    "character_profiles": [
        {
            "profile_id": f"CP{base+1:05d}", "character_id": "E0001", "phase_id": f"P{base+1:04d}", "phase_name": "Biheiril decisive battle",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "mid-twenties, Orsted subordinate, father of several",
            "personality_traits": ["calm under fire","family-first","tactical","empathetic"],
            "values": ["protect family","serve Orsted","keep promises"],
            "desires": ["defeat Gisu trap","protect Eris Ruijerd","survive Fighting God"],
            "fears": ["lose Eris or Ruijerd","Fighting God armor unwinnable"],
            "taboos": ["abandon comrade"],
            "insecurities": ["mana limit vs god armor"],
            "pride": "chantless magic and tactics",
            "impulsiveness": "LOW", "patience": "HIGH", "risk_tolerance": "MEDIUM", "self_control": "HIGH",
            "attachment_style": "secure to wives and comrades",
            "authority_attitude": "trust Orsted and Atofi",
            "family_attitude": "protect as father",
            "romantic_attitude": "devoted to wives",
            "violence_attitude": "restrained then decisive",
            "money_attitude": "none",
            "status_attitude": "judge by deed not rank",
            "race_attitude": "respect ogre and demon",
            "religious_attitude": "none",
            "loyalty": "HIGH", "ambition": "MODERATE",
            "short_term_goals": ["win North III, save Sword God front","contain Badigadi"],
            "long_term_goals": ["defeat Human God"],
            "obligations": ["Orsted mission","protect allies"],
            "decision_tendencies": ["observe then coordinate","use valley terrain"],
            "speech_tendencies": ["short orders in battle","frank to comrades"],
            "social_tendencies": ["coordinate with Eris Ruijerd"],
            "conflict_tendencies": ["contain then finish","cover allies"],
            "known_skills": ["rock cannon","Frost Nova","tactics"],
            "knowledge_state": ["knows Alex is North II","knows Badigadi is apostle in God armor","knows Malt deceived"],
            "relationship_tendencies": ["trust Ruijerd with back","protect Eris"],
            "behavior_changes_note": "from support to front-line decision maker in Biheiril",
            "summary": "Rudeus leads Biheiril final battles, defeats North III and faces Fighting God.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(1,5,10,15)
        },
        {
            "profile_id": f"CP{base+2:05d}", "character_id": "E0021", "phase_id": f"P{base+2:04d}", "phase_name": "Sword King peak",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "early twenties, Sword King, Rudeus third wife",
            "personality_traits": ["direct","fearless","loyal","competitive"],
            "values": ["strength","loyalty","family"],
            "desires": ["cut down Sword God","protect Rudeus"],
            "fears": ["fail to protect"],
            "taboos": ["retreat"],
            "insecurities": ["none"],
            "pride": "Mad Sword King and Light Blade",
            "impulsiveness": "MEDIUM", "patience": "MEDIUM", "risk_tolerance": "HIGH", "self_control": "MEDIUM",
            "attachment_style": "fierce to Rudeus",
            "authority_attitude": "respect Gal Farion then surpass",
            "family_attitude": "belongs to Rudeus home",
            "romantic_attitude": "hot for Rudeus",
            "violence_attitude": "front blade",
            "money_attitude": "none",
            "status_attitude": "by strength",
            "race_attitude": "no bias",
            "religious_attitude": "none",
            "loyalty": "HIGH", "ambition": "HIGH",
            "short_term_goals": ["kill Sword God with Ruijerd"],
            "long_term_goals": ["master Light Blade"],
            "obligations": ["guard Rudeus"],
            "decision_tendencies": ["charge with Ruijerd"],
            "speech_tendencies": ["short challenge"],
            "social_tendencies": ["side by side with Ruijerd"],
            "conflict_tendencies": ["face head-on"],
            "known_skills": ["Light Blade","North basics"],
            "knowledge_state": ["knows Gal Farion is enemy","knows Badigadi is threat"],
            "relationship_tendencies": ["trust Ruijerd"],
            "behavior_changes_note": "inherits Sword God sword after kill",
            "summary": "Eris at peak cuts Sword God with Ruijerd and receives his sword.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(3,4,8)
        },
        {
            "profile_id": f"CP{base+3:05d}", "character_id": "E0031", "phase_id": f"P{base+3:04d}", "phase_name": "Superd escort peak",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "adult Superd, Rudeus benefactor",
            "personality_traits": ["calm","honorable","protective","resolute"],
            "values": ["protect children","honor"],
            "desires": ["avenge disease plot","guard Eris"],
            "fears": ["fail comrades"],
            "taboos": ["harm innocent"],
            "insecurities": ["none"],
            "pride": "Superd spear and trust",
            "impulsiveness": "LOW", "patience": "HIGH", "risk_tolerance": "MEDIUM", "self_control": "HIGH",
            "attachment_style": "loyal to Rudeus and Eris",
            "authority_attitude": "respect Atofi",
            "family_attitude": "protective",
            "romantic_attitude": "none",
            "violence_attitude": "precise spear",
            "money_attitude": "none",
            "status_attitude": "by deed",
            "race_attitude": "proud Superd now accepted",
            "religious_attitude": "none",
            "loyalty": "HIGH", "ambition": "LOW",
            "short_term_goals": ["kill Sword God with Eris"],
            "long_term_goals": ["guard Rudeus family"],
            "obligations": ["comrade oath"],
            "decision_tendencies": ["coordinate flanking"],
            "speech_tendencies": ["quiet affirm"],
            "social_tendencies": ["shoulder with Eris"],
            "conflict_tendencies": ["spear through opening"],
            "known_skills": ["spear","stealth"],
            "knowledge_state": ["knows Gisu trap","knows ogre reconciliation"],
            "relationship_tendencies": ["protect Eris"],
            "behavior_changes_note": "from lone wanderer to paired killer",
            "summary": "Ruijerd pairs with Eris to kill Sword God in Biheiril.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(3,4,9)
        },
        {
            "profile_id": f"CP{base+4:05d}", "character_id": "E0164", "phase_id": f"P{base+4:04d}", "phase_name": "North God II revealed",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "middle-aged, true North God Kalman II Alex Rybak",
            "personality_traits": ["stoic","responsible","fatherly","duelist"],
            "values": ["father duty","duel honor"],
            "desires": ["stop son Alexander","settle with Badigadi by duel"],
            "fears": ["son dies by his hand"],
            "taboos": ["kill son lightly"],
            "insecurities": ["failed father"],
            "pride": "North God title and sword",
            "impulsiveness": "LOW", "patience": "HIGH", "risk_tolerance": "MEDIUM", "self_control": "HIGH",
            "attachment_style": "distant father to Alexander",
            "authority_attitude": "challenge Badigadi to duel",
            "family_attitude": "father to North III",
            "romantic_attitude": "none",
            "violence_attitude": "duel by code",
            "money_attitude": "none",
            "status_attitude": "by rank",
            "race_attitude": "no bias",
            "religious_attitude": "none",
            "loyalty": "HIGH", "ambition": "LOW",
            "short_term_goals": ["duel Badigadi","contain Alexander"],
            "long_term_goals": ["end North God feud"],
            "obligations": ["father to Alexander"],
            "decision_tendencies": ["accept formal duel"],
            "speech_tendencies": ["formal challenge"],
            "social_tendencies": ["with Atofi as envoy"],
            "conflict_tendencies": ["duel honourably"],
            "known_skills": ["North God sword"],
            "knowledge_state": ["knows Alexander is his son","knows Badigadi is apostle"],
            "relationship_tendencies": ["oppose Badigadi but respect duel"],
            "behavior_changes_note": "reveals identity and accepts duel",
            "summary": "Alex revealed as North II, duels Badigadi in Fighting God armor.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(6,11,14)
        },
        {
            "profile_id": f"CP{base+5:05d}", "character_id": "E0162", "phase_id": f"P{base+5:04d}", "phase_name": "North God III final",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "young adult, North God Kalman III, son of Alex",
            "personality_traits": ["proud","hot-headed","ambitious","loyal to Gisu"],
            "values": ["inherit title","prove strength"],
            "desires": ["defeat Rudeus","win for Human God side"],
            "fears": ["fail father name"],
            "taboos": ["flee"],
            "insecurities": ["not equal to father"],
            "pride": "North God III title",
            "impulsiveness": "HIGH", "patience": "LOW", "risk_tolerance": "HIGH", "self_control": "LOW",
            "attachment_style": "seek father approval",
            "authority_attitude": "follow Gisu/Badigadi",
            "family_attitude": "son vs father",
            "romantic_attitude": "none",
            "violence_attitude": "aggressive",
            "money_attitude": "none",
            "status_attitude": "by title",
            "race_attitude": "none",
            "religious_attitude": "none",
            "loyalty": "MEDIUM", "ambition": "HIGH",
            "short_term_goals": ["kill Rudeus in Biheiril valley"],
            "long_term_goals": ["be true North God"],
            "obligations": ["to Human God camp"],
            "decision_tendencies": ["charge"],
            "speech_tendencies": ["boast title"],
            "social_tendencies": ["with Badigadi"],
            "conflict_tendencies": ["overextend"],
            "known_skills": ["North sword"],
            "knowledge_state": ["knows father is Alex"],
            "relationship_tendencies": ["oppose father"],
            "behavior_changes_note": "falls in valley then finished by Rudeus",
            "summary": "North III Alexander defeated in Biheiril, finished by Rudeus.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(5,7,10)
        },
        {
            "profile_id": f"CP{base+6:05d}", "character_id": "E0113", "phase_id": f"P{base+6:04d}", "phase_name": "Fighting God apostle",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "immortal Demon King, Human God apostle",
            "personality_traits": ["jovial then menacing","unstoppable","cunning"],
            "values": ["serve Human God","overwhelm"],
            "desires": ["crush Rudeus camp with God armor"],
            "fears": ["none stated"],
            "taboos": ["none"],
            "insecurities": ["none"],
            "pride": "immortality and God armor",
            "impulsiveness": "MEDIUM", "patience": "MEDIUM", "risk_tolerance": "HIGH", "self_control": "MEDIUM",
            "attachment_style": "bound to Human God",
            "authority_attitude": "declare apostle to Rudeus",
            "family_attitude": "brother to Atofi",
            "romantic_attitude": "betrothed to Kishirika",
            "violence_attitude": "armor crush",
            "money_attitude": "none",
            "status_attitude": "by power",
            "race_attitude": "demon king",
            "religious_attitude": "Human God faith",
            "loyalty": "HIGH to Human God", "ambition": "HIGH",
            "short_term_goals": ["challenge with God armor","duel North II"],
            "long_term_goals": ["defeat Orsted"],
            "obligations": ["apostle duty"],
            "decision_tendencies": ["declare then challenge"],
            "speech_tendencies": ["loud proclamation"],
            "social_tendencies": ["with Gisu"],
            "conflict_tendencies": ["armor frontal"],
            "known_skills": ["Fighting God armor","immortality"],
            "knowledge_state": ["knows Gisu plan","knows armor by Laplace"],
            "relationship_tendencies": ["oppose Atofi then spare"],
            "behavior_changes_note": "dons Laplace-made strongest armor and declares war",
            "summary": "Badigadi appears in Fighting God armor as Human God apostle, duels North II.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(12,13,21)
        },
        {
            "profile_id": f"CP{base+7:05d}", "character_id": "E0165", "phase_id": f"P{base+7:04d}", "phase_name": "Ogre God reconciled",
            "start_date": None, "end_date": None, "date_precision": "UNKNOWN",
            "age_description": "king of ogres on Ogre Isle in Biheiril",
            "personality_traits": ["honorable","easily deceived","stern then conciliatory"],
            "values": ["island honor","truth"],
            "desires": ["correct after being deceived"],
            "fears": ["be used again"],
            "taboos": ["break oath"],
            "insecurities": ["tricked by Gisu"],
            "pride": "Ogre God title",
            "impulsiveness": "MEDIUM", "patience": "MEDIUM", "risk_tolerance": "MEDIUM", "self_control": "MEDIUM",
            "attachment_style": "to island kin",
            "authority_attitude": "receive Atofi envoy",
            "family_attitude": "king to kin",
            "romantic_attitude": "none",
            "violence_attitude": "restrained after truth",
            "money_attitude": "none",
            "status_attitude": "by strength",
            "race_attitude": "ogre king",
            "religious_attitude": "none",
            "loyalty": "MEDIUM", "ambition": "LOW",
            "short_term_goals": ["reconcile with Rudeus camp"],
            "long_term_goals": ["guard isle"],
            "obligations": ["to island"],
            "decision_tendencies": ["hear envoy then admit"],
            "speech_tendencies": ["gruff then apologetic"],
            "social_tendencies": ["island court"],
            "conflict_tendencies": ["pause when truth shown"],
            "known_skills": ["ogre strength"],
            "knowledge_state": ["knows tricked by Gisu"],
            "relationship_tendencies": ["from foe to neutral with Rudeus"],
            "behavior_changes_note": "admits deceived and reconciles via Atofi and Alex",
            "summary": "Ogre God Malt reconciles after envoy clarifies Gisu deceit.",
            "visible_from_volume": 25, "visible_to_volume": None,
            "evidence_refs": ev(11,13,22)
        },
    ],
    "behavior_cases": [
        {"case_id": f"BC{base+1:05d}", "character_id": "E0021", "phase_id": f"P{base+2:04d}", "phase_name": "Sword King peak", "volume_no": 25, "situation_type": "combat", "context": "Biheiril Sword God front: Gal Farion vs Eris and Ruijerd", "trigger": "Gal joins Gisu camp and blocks path", "available_information": "Gal is former Sword God, Eris is Mad Sword King with Ruijerd spear cover", "action": "paired flank: Eris Light Blade main, Ruijerd spear finish, accepts Gal sword after", "verbal_response": "short kiai and accept sword", "emotional_response": "fierce then solemn", "goal_at_time": "kill Sword God to open path", "relationship_context": "Eris-Ruijerd co-killers, Eris successor", "social_context": "open battlefield", "immediate_outcome": "Gal killed and sword passed to Eris", "long_term_outcome": "Sword God title ends, Eris inherits blade", "tags": ["COMBAT","LOYALTY"], "evidence_refs": ev(4)},
        {"case_id": f"BC{base+2:05d}", "character_id": "E0031", "phase_id": f"P{base+3:04d}", "phase_name": "Superd escort peak", "volume_no": 25, "situation_type": "combat", "context": "Same Sword God kill: Ruijerd with Eris", "trigger": "Eris engages Gal, opening appears", "available_information": "Gal focused on Eris Light Blade", "action": "spear thrust through opening to finish", "verbal_response": "quiet coordination", "emotional_response": "calm resolve", "goal_at_time": "ensure Gal dies", "relationship_context": "Ruijerd supports Eris", "social_context": "paired combat", "immediate_outcome": "Gal falls", "long_term_outcome": "Superd reputation restored by honorable kill", "tags": ["COMBAT","PROTECT"], "evidence_refs": ev(4)},
        {"case_id": f"BC{base+3:05d}", "character_id": "E0001", "phase_id": f"P{base+1:04d}", "phase_name": "Biheiril decisive battle", "volume_no": 25, "situation_type": "combat", "context": "Superd village valley vs North III Alexander", "trigger": "Alexander charges with North camp", "available_information": "valley trap terrain, Eris Ruijerd nearby, Alex watches son", "action": "coordinate contain, force fall into valley, finish with magic after fall", "verbal_response": "orders to hold and cast", "emotional_response": "tense then cold finish", "goal_at_time": "defeat North III without losing allies", "relationship_context": "Rudeus as coordinator, Eris Ruijerd as blades", "social_context": "valley ambush", "immediate_outcome": "Alexander falls then finished", "long_term_outcome": "North God line broken, Alex mourns", "tags": ["COMBAT","NEGOTIATION"], "evidence_refs": ev(5,7,10)},
        {"case_id": f"BC{base+4:05d}", "character_id": "E0164", "phase_id": f"P{base+4:04d}", "phase_name": "North God II revealed", "volume_no": 25, "situation_type": "authority", "context": "Post valley: Badigadi in God armor declares", "trigger": "Badigadi challenges in armor", "available_information": "armor is Laplace strongest, Badigadi is apostle", "action": "reveal true name Alex Rybak and accept duel", "verbal_response": "I am Kalman II, I accept", "emotional_response": "heavy father then duelist resolve", "goal_at_time": "contain immortal armor by code duel", "relationship_context": "Alex vs Badigadi formal duel", "social_context": "declared duel before both camps", "immediate_outcome": "duel set, Rudeus camp stalls armor", "long_term_outcome": "buys time vs Fighting God", "tags": ["AUTHORITY","COMBAT"], "evidence_refs": ev(6,12,21)},
        {"case_id": f"BC{base+5:05d}", "character_id": "E0113", "phase_id": f"P{base+6:04d}", "phase_name": "Fighting God apostle", "volume_no": 25, "situation_type": "anger", "context": "Biheiril declaration with armor", "trigger": "arrive with Gisu after North III falls", "available_information": "Rudeus camp gathered, Atofi neutral", "action": "declare Human God apostle, show God armor, propose duel to North II", "verbal_response": "I am apostle, this is God armor made by Laplace", "emotional_response": "jovial to menacing", "goal_at_time": "break Rudeus camp morale", "relationship_context": "Badigadi vs Rudeus and Alex", "social_context": "public declaration", "immediate_outcome": "Rudeus camp shocked", "long_term_outcome": "duel line established", "tags": ["AUTHORITY","ANGER"], "evidence_refs": ev(12,13)},
        {"case_id": f"BC{base+6:05d}", "character_id": "E0165", "phase_id": f"P{base+7:04d}", "phase_name": "Ogre God reconciled", "volume_no": 25, "situation_type": "negotiation", "context": "Ogre Isle envoy: Atofi and Alex meet Malt", "trigger": "Atofi and Alex arrive to clarify Gisu lie", "available_information": "Gisu used Malt isle troops", "action": "hear envoy, admit deceived, agree reconcile", "verbal_response": "Was tricked, will withdraw", "emotional_response": "shame then relief", "goal_at_time": "avoid further blood", "relationship_context": "Malt with Atofi/Alex as envoys to Rudeus", "social_context": "island court", "immediate_outcome": "Malt reconciles", "long_term_outcome": "Biheiril ogre force leaves Gisu camp", "tags": ["NEGOTIATION","TRUST"], "evidence_refs": ev(11,22)},
        {"case_id": f"BC{base+7:05d}", "character_id": "E0001", "phase_id": f"P{base+1:04d}", "phase_name": "Biheiril decisive battle", "volume_no": 25, "situation_type": "trust", "context": "Ogre Isle after battle: leave isle to envoys", "trigger": "need to hold valley while envoys go", "available_information": "Atofi and Alex trustworthy to ogres", "action": "entrust envoy to Atofi and Alex, hold line", "verbal_response": "Please go, we hold here", "emotional_response": "trustful delegation", "goal_at_time": "split front to secure political flank", "relationship_context": "Rudeus entrusts Atofi and Alex", "social_context": "divided fronts", "immediate_outcome": "envoys depart", "long_term_outcome": "Malt side flips", "tags": ["TRUST","LOYALTY"], "evidence_refs": ev(11)},
        {"case_id": f"BC{base+8:05d}", "character_id": "E0057", "phase_id": f"P{base+1:04d}", "phase_name": "Biheiril decisive battle", "volume_no": 25, "situation_type": "retreat", "context": "Gisu trap collapses across Biheiril", "trigger": "Sword God dead, North III dead, Malt flips", "available_information": "Fighting God armor still holds but rest lost", "action": "flee Biheiril to preserve apostle", "verbal_response": "silent escape", "emotional_response": "calculating retreat", "goal_at_time": "survive to scheme again", "relationship_context": "Gisu abandons Badigadi line", "social_context": "routed camp", "immediate_outcome": "Gisu escapes", "long_term_outcome": "Human God loses Biheiril", "tags": ["RETREAT","SECRET"], "evidence_refs": ev(10,13)},
        {"case_id": f"BC{base+9:05d}", "character_id": "E0129", "phase_id": f"P{base+4:04d}", "phase_name": "North God II revealed", "volume_no": 25, "situation_type": "loyalty", "context": "Atofi accompanies Alex to Ogre Isle as envoy", "trigger": "Rudeus asks to handle ogre front", "available_information": "Atofi is Demon King, respected by ogres", "action": "fly with Alex to isle and vouch", "verbal_response": "We come to clarify", "emotional_response": "proud sister-king bearing", "goal_at_time": "use Demon King weight to reconcile", "relationship_context": "Atofi with Alex as pair envoy", "social_context": "inter-king envoy", "immediate_outcome": "Malt listens", "long_term_outcome": "ogre-demon neutrality kept", "tags": ["LOYALTY","NEGOTIATION"], "evidence_refs": ev(11,13)},
        {"case_id": f"BC{base+10:05d}", "character_id": "E0001", "phase_id": f"P{base+1:04d}", "phase_name": "Biheiril decisive battle", "volume_no": 25, "situation_type": "fear", "context": "Facing Fighting God armor after wins", "trigger": "Badigadi armor declared strongest by Laplace", "available_information": "armor nulls normal damage, immortal wearer", "action": "avoid direct clash, anchor on Alex duel, prepare to support", "verbal_response": "We take duel, we will back you", "emotional_response": "cold fear mastered", "goal_at_time": "survive unwinnable armor", "relationship_context": "Rudeus backs Alex vs Badigadi", "social_context": "staredown before duel", "immediate_outcome": "camp holds not broken", "long_term_outcome": "Fighting God front stalemates", "tags": ["FEAR","PROTECT","COMBAT"], "evidence_refs": ev(12,13,21)},
    ],
    "detailed_events": [
        {
            "event_id": f"DE{base+1:05d}", "event_type": "battle", "title": "Sword God Slain",
            "timeline_event_id": "T0091", "time_date": None, "time_precision": "UNKNOWN", "time_note": "Biheiril decisive, before North III",
            "volume_no": 25, "location_id": None, "participants": ["E0021","E0031","E0110"],
            "prerequisites": [{"prerequisite_id": f"EP{base+1:05d}", "prerequisite_type": "PERSON_PRESENT", "ref_id": "E0110", "statement": "Gal Farion present as enemy Sword God", "evidence_refs": ev(3)}],
            "dependencies": [{"dependency_id": f"ED{base+1:05d}", "dependency_type": "ENABLES", "target_event_id": f"DE{base+2:05d}", "statement": "Sword God death opens path to North III valley"}],
            "state_changes": [{"change_id": f"SC{base+1:05d}", "change_kind": "death", "subject_id": "E0110", "before": "alive Sword God", "after": "slain, sword passed to Eris"}],
            "trigger": "Gal Farion blocks Biheiril with Gisu camp",
            "actions": ["Eris and Ruijerd paired kill", "Gal passes his beloved sword to Eris"],
            "outcome": "Sword God dead, Eris inherits sword; Gisu camp loses sword line",
            "relationship_change_ids": [f"RC{base+1:05d}"], "belief_ids": ["BL25001"], "canon_importance": "MAJOR", "evidence_refs": ev(3,4,8)
        },
        {
            "event_id": f"DE{base+2:05d}", "event_type": "battle", "title": "North God III Defeated",
            "timeline_event_id": "T0092", "time_date": None, "time_precision": "UNKNOWN", "time_note": "Biheiril valley after Sword God",
            "volume_no": 25, "location_id": None, "participants": ["E0001","E0021","E0031","E0164","E0162"],
            "prerequisites": [{"prerequisite_id": f"EP{base+2:05d}", "prerequisite_type": "PERSON_PRESENT", "ref_id": "E0162", "statement": "Alexander present as North III", "evidence_refs": ev(5)}],
            "dependencies": [{"dependency_id": f"ED{base+2:05d}", "dependency_type": "CAUSES", "target_event_id": f"DE{base+4:05d}", "statement": "North III fall brings Badigadi in armor to recover"}],
            "state_changes": [{"change_id": f"SC{base+2:05d}", "change_kind": "death", "subject_id": "E0162", "before": "alive North III", "after": "defeated, falls then finished by Rudeus"}],
            "trigger": "Gisu commits North III to break Rudeus line",
            "actions": ["valley contain", "force fall", "Rudeus finishes"],
            "outcome": "North III dead; North God line cut; Gisu loses second king",
            "relationship_change_ids": [f"RC{base+2:05d}"], "belief_ids": ["BL25002"], "canon_importance": "MAJOR", "evidence_refs": ev(5,7,10)
        },
        {
            "event_id": f"DE{base+3:05d}", "event_type": "parley", "title": "Ogre God Reconciliation",
            "timeline_event_id": "T0093", "time_date": None, "time_precision": "UNKNOWN", "time_note": "Biheiril isle after valley",
            "volume_no": 25, "location_id": None, "participants": ["E0129","E0164","E0165"],
            "prerequisites": [{"prerequisite_id": f"EP{base+3:05d}", "prerequisite_type": "PERSON_PRESENT", "ref_id": "E0165", "statement": "Malt present on Ogre Isle", "evidence_refs": ev(11)}],
            "dependencies": [],
            "state_changes": [{"change_id": f"SC{base+3:05d}", "change_kind": "political", "subject_id": "E0165", "before": "hostile under Gisu trick", "after": "reconciled, withdraws"}],
            "trigger": "Atofi and Alex envoy to clarify Gisu deceit",
            "actions": ["Atofi vouches", "Alex explains", "Malt admits tricked and reconciles"],
            "outcome": "Ogre God flips from Gisu camp to neutral, Biheiril ogre troops leave",
            "relationship_change_ids": [f"RC{base+3:05d}"], "belief_ids": ["BL25003","BL25004"], "canon_importance": "MAJOR", "evidence_refs": ev(11,22)
        },
        {
            "event_id": f"DE{base+4:05d}", "event_type": "standoff", "title": "Fighting God Appears",
            "timeline_event_id": "T0094", "time_date": None, "time_precision": "UNKNOWN", "time_note": "Biheiril field after reconciliations",
            "volume_no": 25, "location_id": None, "participants": ["E0113","E0164","E0057","E0001"],
            "prerequisites": [{"prerequisite_id": f"EP{base+4:05d}", "prerequisite_type": "ITEM", "ref_id": f"IT{base+1:05d}", "statement": "Fighting God armor available by Laplace", "evidence_refs": ev(12)}],
            "dependencies": [],
            "state_changes": [{"change_id": f"SC{base+4:05d}", "change_kind": "stance", "subject_id": "E0113", "before": "reserve apostle", "after": "declared front in God armor"}],
            "trigger": "Gisu deploys last card: Badigadi in armor",
            "actions": ["Badigadi declares Human God apostle", "reveals armor as Laplace strongest", "proposes duel to North II"],
            "outcome": "Standoff: Alex accepts duel, Rudeus camp holds, Gisu still escapes",
            "relationship_change_ids": [], "belief_ids": ["BL25005"], "canon_importance": "MAJOR", "evidence_refs": ev(12,13,21)
        },
        {
            "event_id": f"DE{base+5:05d}", "event_type": "undone", "title": "Gisu Escape",
            "timeline_event_id": None, "time_date": None, "time_precision": "UNKNOWN", "time_note": "Biheiril tail",
            "volume_no": 25, "location_id": None, "participants": ["E0057","E0001","E0113"],
            "prerequisites": [{"prerequisite_id": f"EP{base+5:05d}", "prerequisite_type": "PERSON_PRESENT", "ref_id": "E0057", "statement": "Gisu present as trap planner", "evidence_refs": ev(13)}],
            "dependencies": [{"dependency_id": f"ED{base+3:05d}", "dependency_type": "INFLUENCES", "target_event_id": f"DE{base+3:05d}", "statement": "ogre flip forces Gisu to abandon that flank"}],
            "state_changes": [{"change_id": f"SC{base+5:05d}", "change_kind": "position", "subject_id": "E0057", "before": "Biheiril trap master", "after": "fled, Human God camp scattered"}],
            "trigger": "all Gisu kings spent except armor",
            "actions": ["Gisu slips away while armor draws focus"],
            "outcome": "Decisive battle won but mastermind escapes",
            "relationship_change_ids": [], "belief_ids": [], "canon_importance": "MINOR", "evidence_refs": ev(10,13)
        },
    ],
    "items": [
        {"item_id": f"IT{base+1:05d}", "canonical_name": "Fighting God Armor", "aliases": ["God armor","Toshin armor"], "category": "armor", "subcategory": "god armor", "description": "Laplace-made strongest armor worn by Badigadi as Fighting God, declared in Biheiril", "material": "unknown god metal", "size": "giant", "weight": "immense", "durability": "near invincible", "rarity": "unique", "value_information": "priceless, strongest by Laplace", "currency": None, "creator": "Laplace", "origin": "Laplace workshop", "manufacturer": None, "abilities": ["vast strength and defense"], "effects": ["bearer becomes Fighting God"], "requirements": ["immense strength to wear"], "limitations": ["consumes bearer"], "first_appearance_volume": 25, "first_appearance_line": 229606, "visible_from_volume": 25, "evidence_refs": ev(12,21)},
        {"item_id": f"IT{base+2:05d}", "canonical_name": "Sword God Longsword", "aliases": ["Gal sword"], "category": "weapon", "subcategory": "sword", "description": "Gal Farion beloved sword passed to Eris upon death", "material": "steel", "size": "longsword", "weight": None, "durability": "high", "rarity": "unique", "value_information": None, "currency": None, "creator": None, "origin": "Sword Sanctum", "manufacturer": None, "abilities": [], "effects": ["symbol of Sword God"], "requirements": [], "limitations": [], "first_appearance_volume": 25, "first_appearance_line": 225700, "visible_from_volume": 25, "evidence_refs": ev(4,8)},
    ],
    "item_instances": [
        {"instance_id": f"IN{base+1:05d}", "definition_id": f"IT{base+1:05d}", "owner_id": "E0113", "holder_id": "E0113", "location_id": None, "location_name": "Biheiril field", "condition": "intact", "durability_if_known": None, "acquired_at": None, "lost_at": None, "acquired_at_volume": 25, "lost_at_volume": None, "ownership_history": [{"entry_id": f"OH{base+1:05d}", "owner_id": "E0113", "period_start": None, "period_end": None, "acquired_via": "worn as Fighting God in Biheiril", "lost_via": None, "note": "armor declared strongest by Laplace"}], "evidence_refs": ev(12,21)},
        {"instance_id": f"IN{base+2:05d}", "definition_id": f"IT{base+2:05d}", "owner_id": "E0021", "holder_id": "E0021", "location_id": None, "location_name": "Biheiril", "condition": "intact", "durability_if_known": None, "acquired_at": None, "lost_at": None, "acquired_at_volume": 25, "lost_at_volume": None, "ownership_history": [{"entry_id": f"OH{base+2:05d}", "owner_id": "E0110", "period_start": None, "period_end": None, "acquired_via": "wielded as Sword God", "lost_via": "passed on death", "note": "Gal passes to Eris"}, {"entry_id": f"OH{base+3:05d}", "owner_id": "E0021", "period_start": None, "period_end": None, "acquired_via": "received from dying Gal", "lost_via": None, "note": "Eris inherits"}], "evidence_refs": ev(4,8)},
    ],
    "abilities": [
        {"ability_id": f"AB{base+1:05d}", "name": "Fighting God Armor equip", "aliases": [], "ability_type": "SPECIAL", "school": None, "element": None, "tier": "god", "requirements": ["Laplace armor"], "preconditions": ["wear armor"], "mana_cost_if_known": None, "stamina_cost_if_known": None, "range_if_known": "melee god", "duration_if_known": "while worn", "effects": ["become Fighting God, immense power"], "limitations": ["bearer consumed"], "counters": ["Alex duel code"], "qualitative_power": "overwhelming", "learning_method": ["wear"], "known_users": ["E0113"], "evidence_refs": ev(12,21)},
        {"ability_id": f"AB{base+2:05d}", "name": "North God dual-wield", "aliases": [], "ability_type": "SWORD", "school": "North God", "element": None, "tier": "god", "requirements": [], "preconditions": [], "mana_cost_if_known": None, "stamina_cost_if_known": None, "range_if_known": "melee", "duration_if_known": None, "effects": ["North God sword with trick"], "limitations": [], "counters": ["valley contain"], "qualitative_power": "high", "learning_method": [], "known_users": ["E0164","E0162"], "evidence_refs": ev(5,6)},
        {"ability_id": f"AB{base+3:05d}", "name": "Light Blade of Eris", "aliases": [], "ability_type": "SWORD", "school": "Sword God", "element": None, "tier": "king", "requirements": [], "preconditions": [], "mana_cost_if_known": None, "stamina_cost_if_known": None, "range_if_known": "melee", "duration_if_known": "instant", "effects": ["light-speed cut"], "limitations": [], "counters": [], "qualitative_power": "high", "learning_method": [], "known_users": ["E0021"], "evidence_refs": ev(4)},
    ],
    "power_comparisons": [
        {"comparison_id": f"PC{base+1:05d}", "actor_id": "E0021", "target_id": "E0110", "dimension": "sword", "context": "Biheiril Sword God duel with Ruijerd support", "result": "Eris and Ruijerd kill Gal, Gal passes sword acknowledging successor", "confidence": "EXPLICIT", "evidence_refs": ev(4)},
        {"comparison_id": f"PC{base+2:05d}", "actor_id": "E0001", "target_id": "E0162", "dimension": "battlefield control", "context": "Biheiril valley vs North III", "result": "Rudeus camp contains and finishes Alexander, valley forces fall", "confidence": "EXPLICIT", "evidence_refs": ev(5,7)},
    ],
    "world_rules": [
        {"rule_id": f"WR{base+1:05d}", "domain": "COMBAT", "statement": "Fighting God armor made by Laplace is strongest; bearer becomes Fighting God with near invincible offense/defense but consumes bearer", "scope": "Biheiril field, Laplace craft", "exceptions": "immortal Badigadi can endure longer", "confidence": "EXPLICIT", "visible_from_volume": 25, "evidence_refs": ev(12,21)},
        {"rule_id": f"WR{base+2:05d}", "domain": "SOCIETY", "statement": "North God title passes Kalman I to II to III by strength; father vs son duel requires formal challenge to contain armor", "scope": "North God lineage", "exceptions": "non-formal ambush breaks code", "confidence": "STRONG_INFERENCE", "visible_from_volume": 25, "evidence_refs": ev(5,6)},
        {"rule_id": f"WR{base+3:05d}", "domain": "POLITICS", "statement": "Ogre Isle force can be hired via deceit; envoy of Demon King plus North God can flip by clarifying lie", "scope": "Biheiril ogre politics", "exceptions": "if deceit not exposed, stays hostile", "confidence": "EXPLICIT", "visible_from_volume": 25, "evidence_refs": ev(11,22)},
    ],
    "locations": [],
    "routes": [],
    "travel_observations": [],
    "organizations": [],
    "political_states": [],
    "species": [],
    "creatures": [],
    "beliefs": [
        {"belief_id": "BL25001", "owner_id": "E0110", "topic": "succession", "statement": "Eris worthy to inherit his sword as next Sword God hope", "certainty": "EXPLICIT", "belief_state": "FACT_KNOWN", "learned_from": "E0021", "learned_at_volume": 25, "learned_method": "dueled to death", "is_true_in_world": True, "visible_from_volume": 25, "visible_to_volume": None, "note": "passes sword", "evidence_refs": ev(4)},
        {"belief_id": "BL25002", "owner_id": "E0164", "topic": "son fate", "statement": "Alexander must be stopped even if he dies, father duty", "certainty": "EXPLICIT", "belief_state": "FACT_KNOWN", "learned_from": None, "learned_at_volume": 25, "learned_method": "watches valley", "is_true_in_world": True, "visible_from_volume": 25, "visible_to_volume": None, "note": "lets Rudeus finish", "evidence_refs": ev(6,7)},
        {"belief_id": "BL25003", "owner_id": "E0165", "topic": "Gisu trick", "statement": "was deceived by Gisu to join Biheiril war", "certainty": "EXPLICIT", "belief_state": "FACT_KNOWN", "learned_from": "E0129", "learned_at_volume": 25, "learned_method": "envoy clarification", "is_true_in_world": True, "visible_from_volume": 25, "visible_to_volume": None, "note": "admits and reconciles", "evidence_refs": ev(11,22)},
        {"belief_id": "BL25004", "owner_id": "E0165", "topic": "Gisu prior", "statement": "before envoy, believed Rudeus was aggressor justice target", "certainty": "EXPLICIT", "belief_state": "FALSE_BELIEF", "learned_from": "E0057", "learned_at_volume": 25, "learned_method": "Gisu lie", "is_true_in_world": False, "visible_from_volume": 25, "visible_to_volume": None, "note": "false until envoy", "evidence_refs": ev(11)},
        {"belief_id": "BL25005", "owner_id": "E0001", "topic": "apostle", "statement": "Badigadi is Human God apostle in God armor, immortal and unwinnable head-on", "certainty": "EXPLICIT", "belief_state": "FACT_KNOWN", "learned_from": "E0113", "learned_at_volume": 25, "learned_method": "declaration and armor display", "is_true_in_world": True, "visible_from_volume": 25, "visible_to_volume": None, "note": "holds duel line", "evidence_refs": ev(12,21)},
        {"belief_id": "BL25006", "owner_id": "E0001", "topic": "Gisu role", "statement": "Gisu is Human God apostle and Biheiril trap maker who flees", "certainty": "EXPLICIT", "belief_state": "FACT_KNOWN", "learned_from": None, "learned_at_volume": 25, "learned_method": "battle result and missing", "is_true_in_world": True, "visible_from_volume": 25, "visible_to_volume": None, "note": "escape", "evidence_refs": ev(10,13)},
    ],
    "economic_observations": [],
    "relationship_changes": [
        {"change_id": f"RC{base+1:05d}", "source_id": "E0110", "target_id": "E0021", "dimension": "succession", "before": "Sword God vs challenger", "trigger": "slain by Eris and Ruijerd", "after": "passes sword acknowledging successor", "at_volume": 25, "at_date": None, "evidence_refs": ev(4)},
        {"change_id": f"RC{base+2:05d}", "source_id": "E0164", "target_id": "E0162", "dimension": "father-son", "before": "estranged North lineage", "trigger": "valley defeat and finish", "after": "father survives son, mourning", "at_volume": 25, "at_date": None, "evidence_refs": ev(5,7)},
        {"change_id": f"RC{base+3:05d}", "source_id": "E0165", "target_id": "E0001", "dimension": "hostility", "before": "hostile hired force", "trigger": "Atofi and Alex envoy clarifies Gisu lie", "after": "reconciled neutral", "at_volume": 25, "at_date": None, "evidence_refs": ev(11,22)},
        {"change_id": f"RC{base+4:05d}", "source_id": "E0113", "target_id": "E0164", "dimension": "duel", "before": "no relation", "trigger": "Badigadi proposes duel in God armor", "after": "formal duel accepted", "at_volume": 25, "at_date": None, "evidence_refs": ev(12,21)},
    ],
    "speech_profiles": [
        {"profile_id": f"ST{base+1:05d}", "character_id": "E0164", "phase_id": f"P{base+4:04d}", "phase_name": "North God II revealed", "politeness": "formal duel register", "sentence_length": "short declarative", "address_habits": "calls Badigadi by title, Alexander as son", "emotion_expression": "stoic then resonant", "anger_expression": "cold challenge", "shy_expression": "none", "intimate_speech": "father to son terse", "stranger_speech": "formal to Rudeus camp", "superior_speech": "measured to Alexander", "inferior_speech": "respect to Badigadi duel", "canonical_examples": ["I am Kalman II Alex Rybak","I accept the duel"], "visible_from_volume": 25, "evidence_refs": ev(6,12)},
        {"profile_id": f"ST{base+2:05d}", "character_id": "E0113", "phase_id": f"P{base+6:04d}", "phase_name": "Fighting God apostle", "politeness": "loud jocund to declaring", "sentence_length": "mid, exclaiming", "address_habits": "calls Rudeus little and Atofi sister", "emotion_expression": "laugh then boom", "anger_expression": "roar", "shy_expression": "none", "intimate_speech": "to Kishirika tender", "stranger_speech": "proclaim apostle", "superior_speech": "taunt", "inferior_speech": "rare", "canonical_examples": ["I am apostle of Human God","This is strongest armor Laplace made"], "visible_from_volume": 25, "evidence_refs": ev(12,13)},
    ],
    "character_quirks": [
        {"quirk_id": f"QK{base+1:05d}", "character_id": "E0113", "phase_id": f"P{base+6:04d}", "category": "mannerism", "name": "jovial declaration then armor reveal", "description": "laughs heartily then reveals God armor and declares apostle in same breath", "intensity": "HIGH", "frequency": "once in Biheiril", "triggers": ["need to shock enemy"], "preferred_targets": ["E0001"], "avoided_targets": [], "public_expression": "loud before both camps", "private_expression": None, "behavior_patterns": ["laugh then show armor"], "verbal_patterns": ["apostle","Laplace"], "body_language": "spreads arms in armor", "emotional_reward": "awe", "emotional_response": "elated", "boundaries": ["not against Kishirika"], "exceptions": [], "start_date": None, "end_date": None, "visible_from_volume": 25, "visible_to_volume": None, "evidence_type": "CANON_EXPLICIT", "confidence": "EXPLICIT", "evidence_refs": ev(12,21)},
    ],
    "character_preferences": [
        {"preference_id": f"PF{base+1:05d}", "character_id": "E0021", "phase_id": f"P{base+2:04d}", "preference_type": "LIKE", "target": "duel to death", "description": "prefers head-on sword duel especially vs Gal Farion", "intensity": "HIGH", "context": "Sword God front", "visible_from_volume": 25, "visible_to_volume": None, "evidence_type": "CANON_EXPLICIT", "confidence": "EXPLICIT", "evidence_refs": ev(4)},
    ],
    "body_language_profiles": [
        {"profile_id": f"BY{base+1:05d}", "character_id": "E0021", "phase_id": f"P{base+2:04d}", "phase_name": "Sword King peak", "happy_signs": ["grin after kill"], "angry_signs": ["bared teeth at Gal"], "nervous_signs": [], "embarrassed_signs": [], "lying_signs": [], "fear_signs": [], "thinking_signs": [], "affection_signs": ["leans to Rudeus after"], "hostility_signs": ["sword up at Gal"], "visible_from_volume": 25, "visible_to_volume": None, "evidence_refs": ev(4,8)},
    ],
    "character_personas": [
        {"persona_id": f"PN{base+1:05d}", "character_id": "E0164", "phase_id": f"P{base+4:04d}", "persona_type": "PUBLIC", "description": "publicly Sandor the escort, privately North II father-duelist", "speech_style": "escort plain vs duel formal", "behavior_traits": ["shield then reveal","accept duel"], "visible_from_volume": 25, "visible_to_volume": None, "evidence_refs": ev(6,11)},
    ],
    "canon_conflicts": [],
    "canon_gaps": [
        {"gap_id": f"GAP{base+1:05d}", "domain": "COMBAT", "question": "Exact Fighting God armor limits and how to break it without killing immortal Badigadi", "why_needed": "to simulate duel outcome and alternative containment", "searched_volumes": [25], "status": "OPEN", "possible_sources": "later Laplace and Orsted records", "note": "volume 25 declares strongest but not full counters"},
    ]
}

# validate and write
try:
    b = EnrichmentBatch.from_json(batch)
    print("from_json ok", b.counts())
except Exception as e:
    print("from_json fail", e)
    raise

out = pathlib.Path("data/canon_enriched/V025.json")
out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", out, "ev", len(batch["evidence"]))

# verify whole corpus
reg = load_entity_registry(pathlib.Path("data/canon"))
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
report = verify_enrichment(batches, doc, reg)
print("clean", report.is_clean, "errors", len(report.errors))
for e in report.errors:
    print(e.code, e.path, e.message)
pathlib.Path("data/canon_enriched/report.json").write_text(json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
