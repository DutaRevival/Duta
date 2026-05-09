# -*- coding: utf-8 -*-
import logging
import random
import json
import os
import unicodedata
import asyncio
import requests
import time
from datetime import datetime, date
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8272954567:AAG3vHRWr3zD-gI-i1PiVx-iejskLBWVJZI"
FOOTBALL_API_KEY = "4b559620c705450f958b5fb0548ab6d3"
WEATHER_API_KEY = "bd5e378503939ddaee76f12ad7a97608"  # OpenWeatherMap gratuit
SCORES_FILE = "scores.json"
logging.basicConfig(level=logging.INFO)

# ========== PAYS DU MONDE ENTIER ==========
COUNTRIES = {
    # Afrique de l'Ouest
    "🇨🇲 Cameroun": "CM", "🇸🇳 Sénégal": "SN", "🇨🇮 Côte d'Ivoire": "CI",
    "🇳🇬 Nigeria": "NG", "🇬🇭 Ghana": "GH", "🇲🇱 Mali": "ML",
    "🇧🇫 Burkina Faso": "BF", "🇹🇬 Togo": "TG", "🇧🇯 Bénin": "BJ",
    "🇳🇪 Niger": "NE", "🇬🇳 Guinée": "GN", "🇸🇱 Sierra Leone": "SL",
    "🇱🇷 Liberia": "LR", "🇬🇲 Gambie": "GM", "🇬🇼 Guinée-Bissau": "GW",
    "🇨🇻 Cap-Vert": "CV", "🇲🇷 Mauritanie": "MR",
    # Afrique Centrale
    "🇨🇬 Congo": "CG", "🇨🇩 RDC": "CD", "🇬🇦 Gabon": "GA",
    "🇨🇫 RCA": "CF", "🇹🇩 Tchad": "TD", "🇬🇶 Guinée Équatoriale": "GQ",
    "🇸🇹 São Tomé": "ST",
    # Afrique de l'Est
    "🇰🇪 Kenya": "KE", "🇹🇿 Tanzanie": "TZ", "🇺🇬 Ouganda": "UG",
    "🇷🇼 Rwanda": "RW", "🇧🇮 Burundi": "BI", "🇪🇹 Éthiopie": "ET",
    "🇸🇴 Somalie": "SO", "🇩🇯 Djibouti": "DJ", "🇪🇷 Érythrée": "ER",
    "🇸🇸 Soudan du Sud": "SS", "🇸🇩 Soudan": "SD",
    # Afrique du Nord
    "🇲🇦 Maroc": "MA", "🇩🇿 Algérie": "DZ", "🇹🇳 Tunisie": "TN",
    "🇱🇾 Libye": "LY", "🇪🇬 Égypte": "EG",
    # Afrique Australe
    "🇿🇦 Afrique du Sud": "ZA", "🇿🇼 Zimbabwe": "ZW", "🇿🇲 Zambie": "ZM",
    "🇲🇼 Malawi": "MW", "🇲🇿 Mozambique": "MZ", "🇧🇼 Botswana": "BW",
    "🇳🇦 Namibie": "NA", "🇸🇿 Eswatini": "SZ", "🇱🇸 Lesotho": "LS",
    "🇦🇴 Angola": "AO", "🇲🇬 Madagascar": "MG", "🇲🇺 Maurice": "MU",
    "🇸🇨 Seychelles": "SC", "🇰🇲 Comores": "KM",
    # Europe
    "🇫🇷 France": "FR", "🇧🇪 Belgique": "BE", "🇨🇭 Suisse": "CH",
    "🇱🇺 Luxembourg": "LU", "🇩🇪 Allemagne": "DE", "🇬🇧 Royaume-Uni": "GB",
    "🇪🇸 Espagne": "ES", "🇵🇹 Portugal": "PT", "🇮🇹 Italie": "IT",
    "🇳🇱 Pays-Bas": "NL", "🇦🇹 Autriche": "AT", "🇸🇪 Suède": "SE",
    "🇳🇴 Norvège": "NO", "🇩🇰 Danemark": "DK", "🇫🇮 Finlande": "FI",
    "🇵🇱 Pologne": "PL", "🇷🇴 Roumanie": "RO", "🇷🇺 Russie": "RU",
    "🇺🇦 Ukraine": "UA", "🇬🇷 Grèce": "GR", "🇹🇷 Turquie": "TR",
    "🇨🇿 Tchéquie": "CZ", "🇭🇺 Hongrie": "HU", "🇸🇰 Slovaquie": "SK",
    "🇭🇷 Croatie": "HR", "🇷🇸 Serbie": "RS", "🇧🇬 Bulgarie": "BG",
    "🇮🇪 Irlande": "IE", "🇮🇸 Islande": "IS",
    # Amérique du Nord
    "🇺🇸 États-Unis": "US", "🇨🇦 Canada": "CA", "🇲🇽 Mexique": "MX",
    # Amérique Centrale & Caraïbes
    "🇬🇹 Guatemala": "GT", "🇭🇳 Honduras": "HN", "🇸🇻 Salvador": "SV",
    "🇳🇮 Nicaragua": "NI", "🇨🇷 Costa Rica": "CR", "🇵🇦 Panama": "PA",
    "🇨🇺 Cuba": "CU", "🇭🇹 Haïti": "HT", "🇩🇴 Rép. Dominicaine": "DO",
    "🇯🇲 Jamaïque": "JM", "🇹🇹 Trinidad": "TT",
    # Amérique du Sud
    "🇧🇷 Brésil": "BR", "🇦🇷 Argentine": "AR", "🇨🇴 Colombie": "CO",
    "🇻🇪 Venezuela": "VE", "🇵🇪 Pérou": "PE", "🇨🇱 Chili": "CL",
    "🇪🇨 Équateur": "EC", "🇧🇴 Bolivie": "BO", "🇵🇾 Paraguay": "PY",
    "🇺🇾 Uruguay": "UY", "🇬🇾 Guyana": "GY", "🇸🇷 Suriname": "SR",
    # Asie
    "🇨🇳 Chine": "CN", "🇯🇵 Japon": "JP", "🇰🇷 Corée du Sud": "KR",
    "🇮🇳 Inde": "IN", "🇵🇰 Pakistan": "PK", "🇧🇩 Bangladesh": "BD",
    "🇮🇩 Indonésie": "ID", "🇲🇾 Malaisie": "MY", "🇸🇬 Singapour": "SG",
    "🇹🇭 Thaïlande": "TH", "🇻🇳 Vietnam": "VN", "🇵🇭 Philippines": "PH",
    "🇸🇦 Arabie Saoudite": "SA", "🇦🇪 Émirats": "AE", "🇶🇦 Qatar": "QA",
    "🇮🇷 Iran": "IR", "🇮🇶 Irak": "IQ", "🇸🇾 Syrie": "SY",
    "🇱🇧 Liban": "LB", "🇯🇴 Jordanie": "JO", "🇮🇱 Israël": "IL",
    "🇰🇼 Koweït": "KW", "🇧🇭 Bahreïn": "BH", "🇴🇲 Oman": "OM",
    "🇾🇪 Yémen": "YE", "🇦🇫 Afghanistan": "AF", "🇳🇵 Népal": "NP",
    "🇱🇰 Sri Lanka": "LK", "🇲🇲 Myanmar": "MM", "🇰🇭 Cambodge": "KH",
    "🇲🇳 Mongolie": "MN",
    # Océanie
    "🇦🇺 Australie": "AU", "🇳🇿 Nouvelle-Zélande": "NZ", "🇫🇯 Fidji": "FJ",
    # Autre
    "🌍 Autre": "XX",
}

# Groupes de pays pour l'affichage en pages
COUNTRY_PAGES = [
    # Page 1 - Afrique de l'Ouest
    ["🇨🇲 Cameroun","🇸🇳 Sénégal","🇨🇮 Côte d'Ivoire","🇳🇬 Nigeria","🇬🇭 Ghana","🇲🇱 Mali","🇧🇫 Burkina Faso","🇹🇬 Togo","🇧🇯 Bénin","🇳🇪 Niger","🇬🇳 Guinée","🇲🇷 Mauritanie"],
    # Page 2 - Afrique Centrale & Est
    ["🇨🇬 Congo","🇨🇩 RDC","🇬🇦 Gabon","🇨🇫 RCA","🇹🇩 Tchad","🇬🇶 Guinée Équatoriale","🇰🇪 Kenya","🇹🇿 Tanzanie","🇺🇬 Ouganda","🇷🇼 Rwanda","🇧🇮 Burundi","🇪🇹 Éthiopie"],
    # Page 3 - Afrique du Nord & Australe
    ["🇲🇦 Maroc","🇩🇿 Algérie","🇹🇳 Tunisie","🇱🇾 Libye","🇪🇬 Égypte","🇿🇦 Afrique du Sud","🇿🇼 Zimbabwe","🇿🇲 Zambie","🇲🇿 Mozambique","🇦🇴 Angola","🇲🇬 Madagascar","🇸🇩 Soudan"],
    # Page 4 - Europe
    ["🇫🇷 France","🇧🇪 Belgique","🇨🇭 Suisse","🇱🇺 Luxembourg","🇩🇪 Allemagne","🇬🇧 Royaume-Uni","🇪🇸 Espagne","🇵🇹 Portugal","🇮🇹 Italie","🇳🇱 Pays-Bas","🇸🇪 Suède","🇷🇺 Russie"],
    # Page 5 - Amériques
    ["🇺🇸 États-Unis","🇨🇦 Canada","🇲🇽 Mexique","🇧🇷 Brésil","🇦🇷 Argentine","🇨🇴 Colombie","🇻🇪 Venezuela","🇵🇪 Pérou","🇨🇱 Chili","🇭🇹 Haïti","🇩🇴 Rép. Dominicaine","🇨🇺 Cuba"],
    # Page 6 - Asie & Océanie
    ["🇨🇳 Chine","🇯🇵 Japon","🇰🇷 Corée du Sud","🇮🇳 Inde","🇸🇦 Arabie Saoudite","🇦🇪 Émirats","🇶🇦 Qatar","🇮🇩 Indonésie","🇸🇬 Singapour","🇹🇭 Thaïlande","🇦🇺 Australie","🌍 Autre"],
]

PAGE_TITLES = [
    "Afrique de l'Ouest",
    "Afrique Centrale & Est",
    "Afrique du Nord & Australe",
    "Europe",
    "Amériques",
    "Asie & Océanie",
]

def normalize(text):
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def can_form_word(word, letters):
    letters = list(normalize(letters))
    for c in normalize(word):
        if c in letters:
            letters.remove(c)
        else:
            return False
    return True

FALLBACK_DICT = set(normalize(w) for w in ['ah','ai','an','as','au','ba','be','bi','bo','bu','ca','ce','ci','da','de','du','eh','el','em','en','er','es','et','eu','ex','fa','fi','go','ha','hi','ho','il','in','je','la','le','li','lo','lu','ma','me','mi','mo','mu','na','ne','ni','no','nu','on','or','os','ou','pa','pi','po','pu','ra','re','ri','ro','ru','sa','se','si','so','su','ta','te','ti','to','tu','un','us','va','ve','vi','vo','vu','ya','yo','ab','ad','ag','al','am','ar','at','aw','ax','ay','by','do','ed','ef','he','id','if','is','it','jo','ka','ki','my','of','oh','oi','ok','om','op','ow','ox','oy','pe','qi','sh','uh','um','up','we','wo','xi','xu','ye','lit','lits','met','mets','mis','mot','mots','lot','lots','rot','pot','pots','mer','fer','ver','vert','net','set','jet','pet','bet','art','part','car','bar','can','ban','fan','man','ran','tan','van','pan','cap','map','nap','rap','tap','cat','bat','fat','hat','mat','pat','rat','sat','bad','had','lad','mad','sad','bag','lag','nag','rag','sag','tag','bit','fit','hit','kit','pit','sit','wit','bog','cog','dog','fog','hog','jog','log','bon','con','don','ion','son','ton','bug','dug','jug','mug','pug','rug','tug','bun','fun','gun','nun','pun','run','sun','but','cut','gut','hut','nut','put','rut','able','acte','aide','aile','ami','amie','ane','ange','arme','aube','auto','beau','bien','bleu','bloc','bois','bon','bord','bout','bras','cage','camp','case','cent','char','chat','chef','cher','ciel','cite','clan','clou','club','code','coin','cone','cote','coup','cran','cure','dame','date','demi','dent','deux','dire','dome','dose','drap','dune','dure','edit','elan','etat','etre','euro','face','fait','file','film','fils','fine','flot','foie','fond','fort','four','gain','gale','gare','gate','gaze','gene','gite','golf','gout','gras','gris','hale','halo','hate','hier','home','hors','hote','ile','jade','jean','joli','joue','jour','juge','jupe','lame','lard','lent','lest','leur','lieu','lime','lire','lobe','loge','loin','lors','loue','loup','lune','male','malt','mare','mars','mate','mere','mine','mode','mort','mule','noel','noir','note','nuit','once','onde','oral','orge','ours','page','pale','pare','part','pate','peau','pere','pied','pile','pine','pire','plan','plat','plie','pore','port','pose','prix','puce','rade','rale','rame','rang','rape','rare','rase','rate','reel','rein','rent','ride','rire','rite','robe','role','rude','ruse','sang','sans','saut','seau','sere','seve','silo','sole','sort','sous','stop','sure','tare','tele','tend','tenu','tire','toit','tome','tone','tore','tort','trac','tram','trap','tres','trio','trop','tube','tune','type','vale','vane','veau','vent','vers','vide','vile','vine','vite','voie','voir','vole','vote','vrai','zero','zone','able','acid','also','area','army','away','back','ball','band','bank','base','bath','bear','beat','bell','best','bird','bite','blow','blue','boat','body','bold','bolt','bond','bone','book','bore','born','bowl','burn','came','camp','cape','card','care','cart','case','cast','cave','cent','char','chat','chin','chip','clan','clap','clip','clot','club','clue','coal','coat','coil','cold','come','cord','core','corn','cost','crop','dart','data','date','deal','dear','debt','deck','dent','diet','dirt','disc','dish','dome','done','door','down','drag','draw','drip','drop','drum','duel','dune','dust','earn','east','edge','edit','epic','even','ever','evil','face','fact','fail','fair','fall','fame','fare','farm','fast','fate','fear','feat','feel','fell','felt','fern','file','fill','film','find','fine','fire','firm','fist','flag','flat','flaw','fled','flip','flow','foam','fold','fond','food','fool','foot','ford','fore','fork','form','fort','foul','four','free','fuel','full','gain','gale','game','gang','gate','gave','gaze','gear','gent','germ','girl','give','glad','glob','glue','goal','gold','golf','gone','good','gore','gown','grab','gram','gray','grew','grid','grim','grin','grip','grit','grow','gulf','gust','hack','hale','half','hall','halt','hand','hang','hard','hare','harm','harp','hate','have','heal','heap','heat','heel','held','helm','help','here','hero','hide','high','hike','hill','hint','hire','hold','hole','home','hood','hook','hope','horn','host','hour','hull','hunt','hurt','idea','idle','inch','into','iron','isle','item','jade','jail','jaws','jean','joke','jolt','jump','just','keen','keep','kick','kind','king','knot','lace','lack','lame','lamp','land','lane','lard','lark','lash','last','late','lead','leaf','lean','leap','lend','lens','lest','liar','lick','life','lift','like','lime','limp','line','link','lint','list','live','load','lobe','lock','loft','lone','long','look','loom','lord','lose','lost','loud','love','luck','made','mail','main','make','male','malt','mane','mare','mark','mast','mate','meal','mean','meat','meet','melt','mend','mere','mild','mile','milk','mill','mind','mine','mint','mire','miss','mist','moan','mole','mood','moon','moor','more','most','move','muck','mule','must','nail','name','near','neck','need','next','nice','nick','node','none','noon','norm','nose','note','once','open','oral','oven','over','pace','pack','page','pain','pair','pale','palm','pane','park','part','past','path','peak','peel','peer','pick','pier','pile','pine','pink','pipe','plan','play','plot','plum','plus','poem','pole','poll','pond','pore','port','pose','post','pour','prey','prop','pull','pump','pure','push','race','rack','raid','rail','rain','rake','ramp','rang','rank','rant','rate','read','real','reap','reel','rein','rely','rend','rent','rest','rice','rich','ride','ring','riot','rise','risk','road','roam','roar','robe','rock','rode','role','roll','roof','room','root','rope','rose','rude','ruin','rule','rune','ruse','rush','rust','safe','sail','sake','sale','salt','same','sand','sane','sang','save','seal','seam','seat','self','send','shin','ship','shoe','shop','shot','shut','sick','side','sign','silk','sing','sink','site','size','skin','skip','slab','slap','slim','slip','slot','snap','snow','soak','sock','soil','sold','sole','some','song','sore','sort','soul','soup','sour','span','spin','spit','spot','stag','star','stay','stem','step','stir','stop','stun','suck','suit','sung','sure','surf','swan','swap','swim','tail','tale','talk','tall','tame','tank','tart','team','tear','tell','tend','tent','term','thin','tide','tile','till','time','tire','toad','toil','told','toll','tome','tone','tool','torn','toss','tour','town','trap','tray','tree','trim','trip','true','tube','tuck','tune','twin','type','upon','urge','used','vale','vane','vast','veil','vein','vent','verb','very','vest','vice','view','vile','vine','void','wade','wage','wake','walk','wall','wand','wane','ward','ware','warm','warn','wash','wave','weak','wear','weed','went','wide','wild','will','wind','wine','wing','wire','wise','wish','woke','wood','wool','word','wore','work','worm','worn','wrap','yell','zero','zinc','zone','zoom'])

# Mots supplementaires tres courants FR+EN souvent manques
EXTRA_WORDS = set(normalize(w) for w in [
    # FR basiques
    'mer','mers','fer','fers','ver','vers','vert','verts','net','nets',
    'set','sets','jet','jets','pet','pets','met','mets','bet','bets',
    'art','arts','part','parts','car','cars','bar','bars','far','jar',
    'jars','tar','tars','can','cans','ban','bans','fan','fans','man',
    'ran','tan','van','vans','pan','pans','cap','caps','map','maps',
    'nap','naps','rap','raps','sap','tap','taps','cat','cats','bat',
    'bats','fat','hat','hats','mat','mats','pat','pats','rat','rats',
    'sat','vat','bad','dad','had','lad','mad','sad','bag','gag','lag',
    'nag','rag','sag','tag','wag','bit','fit','hit','kit','pit','sit',
    'wit','bog','cog','dog','fog','hog','jog','log','tog','bon','con',
    'don','ion','son','ton','won','bud','mud','bug','dug','jug','mug',
    'pug','rug','tug','bun','fun','gun','nun','pun','run','sun','bus',
    'but','cut','gut','hut','jut','nut','put','rut','cab','dab','gab',
    'jab','lab','tab','cad','gal','gap','gar','gel','gin','gnu','got',
    'gou','lac','lai','lan','las','lat','lob','log','lot','lue','lui',
    'mac','mas','max','mil','mis','mit','mob','mod','moi','mol','mon',
    'mot','mou','nag','nez','nid','nil','nob','nom','non','nos','not',
    'nou','nue','nue','oie','ole','omi','ont','ora','ore','ors','ose',
    'ouf','our','pad','par','pat','pec','pen','per','peu','pic','pin',
    'pio','pit','pix','pli','poc','poi','pol','pop','pro','pub','pue',
    'put','raz','rec','ref','rem','rep','res','rev','rie','rif','rin',
    'rip','riz','roi','ros','rue','rut','sac','sas','sau','sec','sel',
    'sen','sep','sex','ski','sol','som','son','sot','sou','sud','sue',
    'sus','tac','tap','tan','tas','tau','tex','tic','tir','ton','top',
    'tot','tou','tri','tub','tue','val','van','var','vas','vic','vin',
    'vis','vit','vol','wok','yak','zoo',
    # EN basiques souvent manques
    'lit','bit','fit','hit','kit','pit','sit','wit','lot','cot','dot',
    'got','hot','jot','not','pot','rot','tot','met','set','net','bet',
    'get','jet','let','pet','vet','wet','yet','cut','but','gut','hut',
    'nut','put','rut','map','cap','gap','lap','nap','rap','sap','tap',
    'zap','mat','bat','cat','fat','hat','pat','rat','sat','vat','bad',
    'had','lad','mad','sad','bag','lag','nag','rag','sag','tag','bin',
    'fin','gin','kin','pin','sin','tin','win','bog','cog','dog','fog',
    'hog','jog','log','bud','mud','bug','dug','jug','mug','pug','rug',
    'tug','bun','fun','gun','nun','pun','run','sun','bus','cab','dab',
    'gab','jab','lab','tab','lid','bid','did','hid','kid','rid','cod',
    'god','mod','nod','rod','sob','bob','cob','fob','gob','job','lob',
    'mob','rob','cub','dub','hub','pub','rub','sub','ego','era','eve',
    'ire','oak','oar','oat','odd','ode','oil','old','ore','our','out',
    'own','pad','pal','paw','pay','pig','pit','ply','pod','pro','pry',
    'pub','pug','pun','pup','pus','ram','raw','ray','ref','rep','rev',
    'rib','rid','rim','rip','rob','rot','row','rub','rug','rum','rut',
    'rye','sad','sag','sap','sat','saw','say','sea','shy','sin','sip',
    'sir','ski','sky','sly','sob','sod','son','sow','soy','spa','spy',
    'sty','sub','sue','sum','sun','sup','tab','tan','tap','tar','tat',
    'tax','thy','tie','tin','tip','toe','ton','too','top','toy','try',
    'tub','tug','tun','two','urn','use','van','vat','via','vie','vim',
    'vow','wad','war','was','wax','way','web','wed','wig','win','wit',
    'woe','wok','won','woo','wow','yam','yap','yaw','yep','yes','yet',
    'yew','you','zap','zed','zen','zig','zip','zoo',
])

def is_valid_word(word):
    w = normalize(word)
    return w in FALLBACK_DICT or w in EXTRA_WORDS

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, ensure_ascii=False)

def add_score(user_id, username, points, country_code=None):
    scores = load_scores()
    uid = str(user_id)
    if uid not in scores:
        scores[uid] = {"username": username, "score": 0, "country": country_code or "XX", "last_bonus": ""}
    scores[uid]["score"] += points
    scores[uid]["username"] = username
    if country_code:
        scores[uid]["country"] = country_code
    save_scores(scores)

def get_user_score(user_id):
    scores = load_scores()
    return scores.get(str(user_id), {}).get("score", 0)

def get_user_country(user_id):
    scores = load_scores()
    return scores.get(str(user_id), {}).get("country", None)

def get_country_flag(code):
    """Retourne le drapeau emoji depuis le code pays"""
    for name, c in COUNTRIES.items():
        if c == code:
            parts = name.strip().split(" ")
            return parts[0]  # emoji drapeau
    return "🌍"

def get_country_name(code):
    """Retourne le nom complet depuis le code pays"""
    for name, c in COUNTRIES.items():
        if c == code:
            return name
    return "🌍 Inconnu"

JUMBLE_SETS = ['ABDNEATUER','SOMELICART','TNEPLIAMOS','RACEBOTINF','DELACTIRMO','PATIOSNECR','FORMALBENIT','CASTLERIPON','VITRACEOLMS','GRANDPOTILE','PLANETORIES','CARBONITEMS']

ALL_QUIZ_QUESTIONS = [
    {"q": "Capitale de la France ?", "a": "paris", "choices": ["Madrid", "Paris", "Rome"]},
    {"q": "Joueurs dans une equipe de foot ?", "a": "11", "choices": ["9", "11", "13"]},
    {"q": "Vainqueur Coupe du Monde 2018 ?", "a": "france", "choices": ["France", "Allemagne", "Bresil"]},
    {"q": "Planete la plus proche du soleil ?", "a": "mercure", "choices": ["Venus", "Mercure", "Mars"]},
    {"q": "Combien de continents sur Terre ?", "a": "7", "choices": ["5", "6", "7"]},
    {"q": "Plus grande planete du systeme solaire ?", "a": "jupiter", "choices": ["Saturne", "Jupiter", "Neptune"]},
    {"q": "Annee de la 1ere Coupe du Monde ?", "a": "1930", "choices": ["1926", "1930", "1934"]},
    {"q": "Animal le plus rapide du monde ?", "a": "guepard", "choices": ["Lion", "Guepard", "Aigle"]},
    {"q": "Cordes sur une guitare classique ?", "a": "6", "choices": ["4", "6", "8"]},
    {"q": "Plus grand pays du monde ?", "a": "russie", "choices": ["Canada", "Chine", "Russie"]},
    {"q": "Capitale du Cameroun ?", "a": "yaounde", "choices": ["Douala", "Yaounde", "Bafoussam"]},
    {"q": "Capitale du Senegal ?", "a": "dakar", "choices": ["Dakar", "Thies", "Saint-Louis"]},
    {"q": "Capitale du Nigeria ?", "a": "abuja", "choices": ["Lagos", "Abuja", "Kano"]},
    {"q": "Fleuve le plus long du monde ?", "a": "nil", "choices": ["Amazone", "Nil", "Congo"]},
    {"q": "Capitale du Bresil ?", "a": "brasilia", "choices": ["Sao Paulo", "Rio", "Brasilia"]},
    {"q": "Vainqueur Coupe du Monde 2022 ?", "a": "argentine", "choices": ["France", "Argentine", "Bresil"]},
    {"q": "Joueurs dans une equipe de basket ?", "a": "5", "choices": ["5", "6", "7"]},
    {"q": "Capitale de l Espagne ?", "a": "madrid", "choices": ["Barcelone", "Valence", "Madrid"]},
    {"q": "Capitale de l Allemagne ?", "a": "berlin", "choices": ["Munich", "Berlin", "Hambourg"]},
    {"q": "Vainqueur Coupe du Monde 2014 ?", "a": "allemagne", "choices": ["Allemagne", "Argentine", "Bresil"]},
    {"q": "Duree d un match de foot ?", "a": "90 min", "choices": ["80 min", "90 min", "120 min"]},
    {"q": "Capitale du Maroc ?", "a": "rabat", "choices": ["Casablanca", "Marrakech", "Rabat"]},
    {"q": "Capitale du Ghana ?", "a": "accra", "choices": ["Kumasi", "Accra", "Tamale"]},
    {"q": "Vainqueur Coupe du Monde 2010 ?", "a": "espagne", "choices": ["Espagne", "Pays-Bas", "Allemagne"]},
    {"q": "Inventeur du telephone ?", "a": "graham bell", "choices": ["Thomas Edison", "Graham Bell", "Nikola Tesla"]},
    {"q": "Capitale du Japon ?", "a": "tokyo", "choices": ["Osaka", "Tokyo", "Kyoto"]},
    {"q": "Nombre d os dans le corps humain ?", "a": "206", "choices": ["186", "206", "256"]},
    {"q": "Plus grand ocean du monde ?", "a": "pacifique", "choices": ["Atlantique", "Indien", "Pacifique"]},
    {"q": "Combien de pays en Afrique ?", "a": "54", "choices": ["48", "54", "60"]},
    {"q": "Plus grand desert du monde ?", "a": "sahara", "choices": ["Kalahari", "Sahara", "Gobi"]},
    {"q": "Couleurs dans l arc en ciel ?", "a": "7", "choices": ["5", "6", "7"]},
    {"q": "Plus grand pays d Afrique ?", "a": "algerie", "choices": ["Soudan", "Algerie", "RDC"]},
    {"q": "Joueurs dans une equipe de rugby ?", "a": "15", "choices": ["13", "15", "17"]},
    {"q": "Peintre de la Joconde ?", "a": "leonard de vinci", "choices": ["Michel-Ange", "Leonard de Vinci", "Raphael"]},
    {"q": "Planetes dans le systeme solaire ?", "a": "8", "choices": ["7", "8", "9"]},
    {"q": "Plus haut sommet du monde ?", "a": "everest", "choices": ["K2", "Everest", "Kilimandjaro"]},
    {"q": "Plus petit pays du monde ?", "a": "vatican", "choices": ["Monaco", "Vatican", "Liechtenstein"]},
    {"q": "Plus grand continent ?", "a": "asie", "choices": ["Afrique", "Asie", "Amerique"]},
    {"q": "Pays le plus peuple du monde ?", "a": "inde", "choices": ["Chine", "Inde", "USA"]},
    {"q": "Monnaie du Japon ?", "a": "yen", "choices": ["Won", "Yuan", "Yen"]},
    {"q": "Pays le plus peuple d Afrique ?", "a": "nigeria", "choices": ["Ethiopie", "Nigeria", "Egypte"]},
    {"q": "Club avec le plus de Champions League ?", "a": "real madrid", "choices": ["Real Madrid", "Barcelona", "Bayern Munich"]},
    {"q": "Annee creation de Facebook ?", "a": "2004", "choices": ["2002", "2004", "2006"]},
    {"q": "Fondateur d Apple ?", "a": "steve jobs", "choices": ["Bill Gates", "Steve Jobs", "Mark Zuckerberg"]},
    {"q": "Annee lancement du 1er iPhone ?", "a": "2007", "choices": ["2005", "2007", "2009"]},
    {"q": "Pays de naissance de Cristiano Ronaldo ?", "a": "portugal", "choices": ["Espagne", "Bresil", "Portugal"]},
    {"q": "Pays de naissance de Lionel Messi ?", "a": "argentine", "choices": ["Argentine", "Uruguay", "Chili"]},
    {"q": "Recordman du monde du 100m ?", "a": "usain bolt", "choices": ["Usain Bolt", "Tyson Gay", "Asafa Powell"]},
    {"q": "Pays de la Tour Eiffel ?", "a": "france", "choices": ["Belgique", "Suisse", "France"]},
    {"q": "Pays du Colisee ?", "a": "italie", "choices": ["Grece", "Italie", "Espagne"]},
    {"q": "Plus grande montagne d Afrique ?", "a": "kilimandjaro", "choices": ["Mont Kenya", "Kilimandjaro", "Mont Cameroun"]},
    {"q": "Debut de la 1ere Guerre Mondiale ?", "a": "1914", "choices": ["1912", "1914", "1916"]},
    {"q": "Pays inventeur du football ?", "a": "angleterre", "choices": ["France", "Angleterre", "Ecosse"]},
    {"q": "Joueurs dans une equipe de handball ?", "a": "7", "choices": ["5", "7", "9"]},
    {"q": "Capitale de l Egypte ?", "a": "le caire", "choices": ["Alexandrie", "Le Caire", "Louxor"]},
    {"q": "Os le plus long du corps ?", "a": "femur", "choices": ["Tibia", "Femur", "Humerus"]},
    {"q": "Animal au plus long cou ?", "a": "girafe", "choices": ["Elephant", "Chameau", "Girafe"]},
    {"q": "Seul mammifere qui vole ?", "a": "chauve souris", "choices": ["Ecureuil volant", "Chauve Souris", "Lemur"]},
    {"q": "Monnaie de l Europe ?", "a": "euro", "choices": ["Franc", "Euro", "Mark"]},
    {"q": "Dents d un adulte ?", "a": "32", "choices": ["28", "30", "32"]},
    {"q": "Annee homme sur la lune ?", "a": "1969", "choices": ["1965", "1969", "1972"]},
    {"q": "Inventeur de l ampoule electrique ?", "a": "thomas edison", "choices": ["Nikola Tesla", "Thomas Edison", "Benjamin Franklin"]},
    {"q": "Faces d un cube ?", "a": "6", "choices": ["4", "6", "8"]},
    {"q": "Joueurs volleyball ?", "a": "6", "choices": ["5", "6", "7"]},
    {"q": "Capitale de l Italie ?", "a": "rome", "choices": ["Milan", "Naples", "Rome"]},
    {"q": "Capitale du Portugal ?", "a": "lisbonne", "choices": ["Porto", "Lisbonne", "Faro"]},
    {"q": "Vainqueur Coupe du Monde 2006 ?", "a": "italie", "choices": ["France", "Italie", "Allemagne"]},
    {"q": "Vainqueur Coupe du Monde 2002 ?", "a": "bresil", "choices": ["Bresil", "Allemagne", "Coree du Sud"]},
    {"q": "Capitale de la Cote d Ivoire ?", "a": "abidjan", "choices": ["Yamoussoukro", "Abidjan", "Bouake"]},
    {"q": "Capitale du Mali ?", "a": "bamako", "choices": ["Tombouctou", "Bamako", "Segou"]},
    {"q": "Capitale du Togo ?", "a": "lome", "choices": ["Kara", "Lome", "Sokode"]},
    {"q": "Capitale du Gabon ?", "a": "libreville", "choices": ["Port-Gentil", "Franceville", "Libreville"]},
    {"q": "Capitale de la RDC ?", "a": "kinshasa", "choices": ["Lubumbashi", "Kinshasa", "Goma"]},
    {"q": "Zeros dans un million ?", "a": "6", "choices": ["5", "6", "7"]},
    {"q": "Element chimique de l eau ?", "a": "h2o", "choices": ["CO2", "H2O", "O2"]},
    {"q": "Compositeur de la 5eme symphonie ?", "a": "beethoven", "choices": ["Mozart", "Beethoven", "Bach"]},
    {"q": "Pays du Machu Picchu ?", "a": "perou", "choices": ["Bolivie", "Colombie", "Perou"]},
    {"q": "Jours dans une annee bissextile ?", "a": "366", "choices": ["364", "365", "366"]},
    {"q": "Sport le plus populaire au monde ?", "a": "football", "choices": ["Basketball", "Football", "Tennis"]},
    {"q": "Capitale de la Russie ?", "a": "moscou", "choices": ["Saint-Petersbourg", "Moscou", "Kazan"]},
    {"q": "Capitale de la Chine ?", "a": "pekin", "choices": ["Shanghai", "Pekin", "Canton"]},
    {"q": "Capitale de la Belgique ?", "a": "bruxelles", "choices": ["Anvers", "Bruges", "Bruxelles"]},
    {"q": "Capitale des Pays Bas ?", "a": "amsterdam", "choices": ["Rotterdam", "Amsterdam", "La Haye"]},
    {"q": "Capitale du Burkina Faso ?", "a": "ouagadougou", "choices": ["Bobo-Dioulasso", "Ouagadougou", "Koudougou"]},
    {"q": "Capitale du Niger ?", "a": "niamey", "choices": ["Zinder", "Niamey", "Maradi"]},
    {"q": "Capitale du Tchad ?", "a": "ndjamena", "choices": ["Moundou", "Ndjamena", "Sarh"]},
    {"q": "Vainqueur Euro 2020 ?", "a": "italie", "choices": ["France", "Angleterre", "Italie"]},
    {"q": "Minutes dans une journee ?", "a": "1440", "choices": ["1000", "1440", "2400"]},
    {"q": "Grammes dans un kg ?", "a": "1000", "choices": ["500", "1000", "1500"]},
]

jumble_sessions = {}
quiz_sessions = {}
quiz_used_questions = {}
QUIZ_USED_FILE = "quiz_used.json"

def load_quiz_used():
    if os.path.exists(QUIZ_USED_FILE):
        with open(QUIZ_USED_FILE, "r") as f:
            return json.load(f)
    return {}

def save_quiz_used(data):
    with open(QUIZ_USED_FILE, "w") as f:
        json.dump(data, f)
quiz_timers = {}

CITY_TIMEZONES = {
    "london": "Europe/London", "angleterre": "Europe/London", "uk": "Europe/London",
    "paris": "Europe/Paris", "france": "Europe/Paris",
    "tokyo": "Asia/Tokyo", "japon": "Asia/Tokyo",
    "dubai": "Asia/Dubai",
    "lagos": "Africa/Lagos", "nigeria": "Africa/Lagos", "abuja": "Africa/Lagos",
    "dakar": "Africa/Dakar", "senegal": "Africa/Dakar",
    "abidjan": "Africa/Abidjan", "cote d ivoire": "Africa/Abidjan",
    "casablanca": "Africa/Casablanca", "maroc": "Africa/Casablanca", "rabat": "Africa/Casablanca",
    "nairobi": "Africa/Nairobi", "kenya": "Africa/Nairobi",
    "cairo": "Africa/Cairo", "egypte": "Africa/Cairo", "le caire": "Africa/Cairo",
    "berlin": "Europe/Berlin", "allemagne": "Europe/Berlin",
    "madrid": "Europe/Madrid", "espagne": "Europe/Madrid",
    "rome": "Europe/Rome", "italie": "Europe/Rome",
    "moscou": "Europe/Moscow", "russie": "Europe/Moscow",
    "beijing": "Asia/Shanghai", "chine": "Asia/Shanghai", "pekin": "Asia/Shanghai",
    "sydney": "Australia/Sydney", "australie": "Australia/Sydney",
    "kinshasa": "Africa/Kinshasa", "rdc": "Africa/Kinshasa", "congo": "Africa/Kinshasa",
    "accra": "Africa/Accra", "ghana": "Africa/Accra",
    "new york": "America/New_York", "usa": "America/New_York",
    "canada": "America/Toronto", "toronto": "America/Toronto", "montreal": "America/Toronto",
    "yaounde": "Africa/Douala", "douala": "Africa/Douala", "cameroun": "Africa/Douala",
    "tunis": "Africa/Tunis", "tunisie": "Africa/Tunis",
    "alger": "Africa/Algiers", "algerie": "Africa/Algiers",
    "bamako": "Africa/Bamako", "mali": "Africa/Bamako",
    "lome": "Africa/Lome", "togo": "Africa/Lome",
    "niamey": "Africa/Niamey", "niger": "Africa/Niamey",
    "ouagadougou": "Africa/Ouagadougou", "burkina": "Africa/Ouagadougou",
    "libreville": "Africa/Libreville", "gabon": "Africa/Libreville",
    "brazzaville": "Africa/Brazzaville",
    "ndjamena": "Africa/Ndjamena", "tchad": "Africa/Ndjamena",
    "johannesburg": "Africa/Johannesburg", "afrique du sud": "Africa/Johannesburg",
    "lisbonne": "Europe/Lisbon", "portugal": "Europe/Lisbon",
    "amsterdam": "Europe/Amsterdam", "pays bas": "Europe/Amsterdam",
    "bruxelles": "Europe/Brussels", "belgique": "Europe/Brussels",
    "geneve": "Europe/Zurich", "suisse": "Europe/Zurich",
    "stockholm": "Europe/Stockholm", "suede": "Europe/Stockholm",
    "seoul": "Asia/Seoul", "coree": "Asia/Seoul",
    "singapour": "Asia/Singapore",
    "bangkok": "Asia/Bangkok", "thailande": "Asia/Bangkok",
    "mumbai": "Asia/Kolkata", "inde": "Asia/Kolkata", "new delhi": "Asia/Kolkata",
    "lima": "America/Lima", "perou": "America/Lima",
    "bogota": "America/Bogota", "colombie": "America/Bogota",
    "buenos aires": "America/Argentina/Buenos_Aires", "argentine": "America/Argentina/Buenos_Aires",
    "sao paulo": "America/Sao_Paulo", "bresil": "America/Sao_Paulo",
    "mexico": "America/Mexico_City", "mexique": "America/Mexico_City",
    "istanbul": "Europe/Istanbul", "turquie": "Europe/Istanbul",
    "athenes": "Europe/Athens", "grece": "Europe/Athens",
    "harare": "Africa/Harare", "zimbabwe": "Africa/Harare",
}

LEAGUE_IDS = {
    "foot_cl": ("2001", "Champions League"),
    "foot_pl": ("2021", "Premier League"),
    "foot_liga": ("2014", "Liga - Espagne"),
    "foot_seria": ("2019", "Serie A - Italie"),
    "foot_bundesliga": ("2002", "Bundesliga - Allemagne"),
    "foot_ligue1": ("2015", "Ligue 1 - France"),
    "foot_europa": ("2146", "Europa League"),
    "foot_cdm": ("2000", "Coupe du Monde"),
}

def get_live_scores(league_id):
    try:
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        matches = requests.get(f"https://api.football-data.org/v4/competitions/{league_id}/matches?status=LIVE", headers=headers, timeout=10).json().get("matches", [])
        if not matches:
            matches = requests.get(f"https://api.football-data.org/v4/competitions/{league_id}/matches?status=IN_PLAY,PAUSED,HALFTIME", headers=headers, timeout=10).json().get("matches", [])
        return matches
    except:
        return None

def format_matches(matches, league_name):
    if matches is None:
        return f"{league_name}\n\nErreur de connexion."
    if not matches:
        return f"{league_name}\n\nPas d evenement en ce moment."
    lines = [f"{league_name} - EN DIRECT\n"]
    for m in matches[:8]:
        home = m["homeTeam"].get("shortName") or m["homeTeam"]["name"]
        away = m["awayTeam"].get("shortName") or m["awayTeam"]["name"]
        full = m.get("score", {}).get("fullTime", {})
        hs = full.get("home")
        as_ = full.get("away")
        if hs is None:
            half = m.get("score", {}).get("halfTime", {})
            hs = half.get("home", "?")
            as_ = half.get("away", "?")
        lines.append(f"{home} {hs} - {as_} {away}")
    return "\n".join(lines)

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fr"}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if resp.status_code != 200:
            return None
        desc = data["weather"][0]["description"].capitalize()
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        city_name = data["name"]
        country = data["sys"]["country"]
        return f"Meteo a {city_name} ({country}):\n\n{desc}\nTemperature: {temp}°C\nRessentie: {feels}°C\nHumidite: {humidity}%"
    except:
        return None

# ========== COMMANDES ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    country = get_user_country(user_id)

    if not country:
        await show_country_selection(update, context, page=0)
        return

    await update.message.reply_text(
        "Bienvenue sur DutaBot!\n\n"
        "/jumble - Formez le max de mots en 3 min\n"
        "/quiz - QCM 3 choix de reponse\n"
        "/score - Votre score\n"
        "/top - Classement pays + mondial\n"
        "/time paris - Heure dans un pays\n"
        "/meteo Douala - Meteo d une ville\n"
        "/foot - Scores de foot en direct\n"
        "/bonus - Bonus quotidien +10 pts\n"
        "/niveau - Jumble avec niveaux (XP x1 a x3)\n"
        "/profile - Votre profil complet\n\n"
        "Bonne chance!"
    )

async def show_country_selection(update, context, page=0):
    countries_page = COUNTRY_PAGES[page]
    keyboard = []
    row = []
    for i, country in enumerate(countries_page):
        row.append(InlineKeyboardButton(country, callback_data=f"country_{COUNTRIES[country]}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Precedent", callback_data=f"page_{page-1}"))
    if page < len(COUNTRY_PAGES) - 1:
        nav.append(InlineKeyboardButton("Suivant ➡️", callback_data=f"page_{page+1}"))
    if nav:
        keyboard.append(nav)

    text = f"Bienvenue! Choisissez votre pays:\n\n📍 {PAGE_TITLES[page]} ({page+1}/{len(COUNTRY_PAGES)})"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        await show_country_selection(update, context, page=page)
        return

    if query.data.startswith("country_"):
        code = query.data.split("_")[1]
        user_id = query.from_user.id
        username = query.from_user.first_name

        scores = load_scores()
        uid = str(user_id)
        if uid not in scores:
            scores[uid] = {"username": username, "score": 0, "country": code, "last_bonus": ""}
        else:
            scores[uid]["country"] = code
            scores[uid]["username"] = username
        save_scores(scores)

        country_name = get_country_name(code)
        await query.edit_message_text(
            f"Parfait! Vous etes enregistre comme {country_name}\n\n"
            f"Bienvenue sur DutaBot!\n\n"
            f"/jumble - Formez le max de mots en 3 min\n"
            f"/quiz - QCM 3 choix de reponse\n"
            f"/score - Votre score\n"
            f"/top - Classement pays + mondial\n"
            f"/time paris - Heure dans un pays\n"
            f"/meteo Douala - Meteo d une ville\n"
            f"/foot - Scores de foot en direct\n"
            f"/bonus - Bonus quotidien +10 pts\n\n"
            f"Bonne chance!"
        )

async def jumble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id in jumble_sessions and jumble_sessions[user_id].get("active"):
        s = jumble_sessions[user_id]
        elapsed = time.time() - s["start_time"]
        remaining = int(180 - elapsed)
        if remaining > 0:
            await update.message.reply_text(f"Partie en cours! {remaining}s restantes\nLettres: >>> {s['letters']} <<<")
            return

    letters = random.choice(JUMBLE_SETS)
    jumble_sessions[user_id] = {
        "letters": letters, "found_words": [], "active": True,
        "start_time": time.time(), "chat_id": chat_id,
        "username": update.effective_user.first_name, "total_points": 0
    }

    await update.message.reply_text(
        f"JUMBLE! Vous avez 3 minutes!\n\n"
        f"Lettres: >>> {letters} <<<\n\n"
        f"Points = lettres du mot\nEx: BON=3pts | GRAND=5pts\n\n"
        f"✅ = Valide | ❌ = Invalide\n\nC est parti!"
    )
    asyncio.create_task(jumble_timer(user_id, chat_id, context))

async def jumble_timer(user_id, chat_id, context):
    await asyncio.sleep(180)
    if user_id not in jumble_sessions or not jumble_sessions[user_id].get("active"):
        return
    session = jumble_sessions[user_id]
    session["active"] = False
    found = session["found_words"]
    points = session["total_points"]
    username = session["username"]
    if points > 0:
        country = get_user_country(user_id)
        add_score(user_id, username, points, country)
        total = get_user_score(user_id)
        mots_str = ", ".join([f"{w}({len(normalize(w))})" for w in found])
        await context.bot.send_message(chat_id=chat_id,
            text=f"Temps ecoule!\n\nMots: {mots_str}\n\n+{points} points!\nScore total: {total} pts\n\n/jumble pour rejouer!")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Temps ecoule! Aucun mot valide.\n/jumble pour reessayer!")
    del jumble_sessions[user_id]

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id in quiz_timers:
        quiz_timers[user_id].cancel()
        del quiz_timers[user_id]
    if user_id in quiz_sessions:
        del quiz_sessions[user_id]

    # Charger questions utilisees depuis fichier (persistant)
    quiz_used = load_quiz_used()
    uid_str = str(user_id)
    if uid_str not in quiz_used:
        quiz_used[uid_str] = []
    used = quiz_used[uid_str]
    available = [q for q in ALL_QUIZ_QUESTIONS if q["q"] not in used]
    if not available:
        quiz_used[uid_str] = []
        available = ALL_QUIZ_QUESTIONS[:]
        save_quiz_used(quiz_used)

    question = random.choice(available)
    quiz_used[uid_str].append(question["q"])
    save_quiz_used(quiz_used)
    choices = question["choices"][:]
    random.shuffle(choices)
    session_id = str(int(time.time() * 1000))

    quiz_sessions[user_id] = {
        "answer": normalize(question["a"]), "active": True,
        "chat_id": chat_id, "username": update.effective_user.first_name,
        "choices_normalized": [normalize(c) for c in choices],
        "choices_display": choices, "session_id": session_id,
    }

    keyboard = [[InlineKeyboardButton(c, callback_data=f"qz_{user_id}_{i}_{session_id}")] for i, c in enumerate(choices)]
    await update.message.reply_text(f"QUIZ!\n\n{question['q']}", reply_markup=InlineKeyboardMarkup(keyboard))

    task = asyncio.create_task(quiz_timer(user_id, chat_id, question["a"], session_id, context))
    quiz_timers[user_id] = task

async def quiz_timer(user_id, chat_id, answer, session_id, context):
    await asyncio.sleep(30)
    if user_id in quiz_sessions and quiz_sessions[user_id].get("active") and quiz_sessions[user_id].get("session_id") == session_id:
        quiz_sessions[user_id]["active"] = False
        del quiz_sessions[user_id]
        if user_id in quiz_timers:
            del quiz_timers[user_id]
        await context.bot.send_message(chat_id=chat_id,
            text=f"Temps ecoule! La reponse etait: {answer.upper()}\n\n/quiz pour continuer!")

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    if len(parts) < 4:
        await query.answer()
        return

    target_user_id = int(parts[1])
    choice_index = int(parts[2])
    session_id = parts[3]
    actual_user_id = query.from_user.id

    if actual_user_id != target_user_id:
        await query.answer("Ce n est pas votre question!", show_alert=True)
        return

    if target_user_id not in quiz_sessions or not quiz_sessions[target_user_id].get("active"):
        await query.answer()
        await query.edit_message_text("Question expiree. /quiz pour continuer!")
        return

    session = quiz_sessions[target_user_id]
    if session.get("session_id") != session_id:
        await query.answer()
        await query.edit_message_text("Question expiree. /quiz pour continuer!")
        return

    correct = session["answer"]
    username = session["username"]
    chosen_norm = session["choices_normalized"][choice_index]
    chosen_display = session["choices_display"][choice_index]
    session["active"] = False
    del quiz_sessions[target_user_id]

    if target_user_id in quiz_timers:
        quiz_timers[target_user_id].cancel()
        del quiz_timers[target_user_id]

    await query.answer()

    if chosen_norm == correct:
        country = get_user_country(target_user_id)
        add_score(target_user_id, username, 15, country)
        add_xp(target_user_id, username, 15, "medium")
        update_stats(target_user_id, username, quiz_correct=1)
        s = get_user_score(target_user_id)
        xp_data = get_user_xp(target_user_id)
        lg = get_league(xp_data.get("xp", 0))
        await query.edit_message_text(
            "✅ " + chosen_display + " - Bonne reponse!\n"
            "+15 pts | +15 XP\n"
            "Score: " + str(s) + " pts | " + lg["emoji"] + " " + lg["name"] + "\n\n"
            "/quiz pour continuer!"
        )
    else:
        await query.edit_message_text(f"❌ {chosen_display} - Mauvaise reponse!\nBonne reponse: {correct.upper()}\n\n/quiz pour continuer!")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    s = get_user_score(user_id)
    name = update.effective_user.first_name
    country_code = get_user_country(user_id)
    country_name = get_country_name(country_code) if country_code else "Non defini"
    await update.message.reply_text(f"Votre score:\n\n{name}\nPays: {country_name}\nScore: {s} points")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    scores = load_scores()
    if not scores:
        await update.message.reply_text("Aucun joueur enregistre!")
        return

    user_country = get_user_country(user_id)
    sorted_world = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    # Classement mondial
    world_lines = ["CLASSEMENT MONDIAL 🌍\n"]
    for i, (uid, data) in enumerate(sorted_world[:10]):
        flag = get_country_flag(data.get("country", "XX"))
        world_lines.append(f"{i+1}. {flag} {data['username']} - {data['score']} pts")

    # Classement par pays
    country_lines = []
    if user_country and user_country != "XX":
        country_name = get_country_name(user_country)
        country_players = [(uid, data) for uid, data in sorted_world if data.get("country") == user_country]
        if country_players:
            country_lines.append(f"\nCLASSEMENT {country_name}\n")
            for i, (uid, data) in enumerate(country_players[:10]):
                country_lines.append(f"{i+1}. {data['username']} - {data['score']} pts")

    result = "\n".join(world_lines)
    if country_lines:
        result += "\n" + "\n".join(country_lines)
    result += f"\n\nTotal joueurs: {len(scores)}"

    await update.message.reply_text(result)

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    scores = load_scores()
    uid = str(user_id)
    today = str(date.today())

    if uid not in scores:
        scores[uid] = {"username": username, "score": 0, "country": "XX", "last_bonus": ""}
        save_scores(scores)

    last_bonus = scores[uid].get("last_bonus", "")
    if last_bonus == today:
        await update.message.reply_text(f"Vous avez deja pris votre bonus aujourd hui!\nRevenez demain pour +10 pts!")
        return

    scores[uid]["score"] += 10
    scores[uid]["last_bonus"] = today
    scores[uid]["username"] = username
    save_scores(scores)

    total = scores[uid]["score"]
    await update.message.reply_text(f"🎁 Bonus quotidien!\n\n+10 points!\nScore total: {total} pts\n\nRevenez demain pour un nouveau bonus!")

async def meteo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /meteo Douala\nEx: /meteo Paris, /meteo Lagos, /meteo Dakar")
        return
    city = " ".join(context.args)
    result = get_weather(city)
    if not result:
        await update.message.reply_text(f"Ville '{city}' non trouvee.\nVerifiez le nom et reessayez.")
    else:
        await update.message.reply_text(result)

async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /time paris\nEx: /time cameroun, /time london, /time dakar")
        return
    city = " ".join(context.args).lower().strip()
    city_norm = normalize(city)
    tz_name = None
    for key, val in CITY_TIMEZONES.items():
        if normalize(key) == city_norm:
            tz_name = val
            break
    if not tz_name:
        await update.message.reply_text(f"'{city}' non trouve.\nEx: /time paris, /time cameroun, /time dakar")
        return
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    await update.message.reply_text(f"Heure a {city.title()}:\n{now.strftime('%H:%M')} - {now.strftime('%d/%m/%Y')}")

async def foot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Champions League", callback_data="foot_cl")],
        [InlineKeyboardButton("Premier League", callback_data="foot_pl")],
        [InlineKeyboardButton("Liga (Espagne)", callback_data="foot_liga")],
        [InlineKeyboardButton("Serie A (Italie)", callback_data="foot_seria")],
        [InlineKeyboardButton("Bundesliga (Allemagne)", callback_data="foot_bundesliga")],
        [InlineKeyboardButton("Ligue 1 (France)", callback_data="foot_ligue1")],
        [InlineKeyboardButton("Europa League", callback_data="foot_europa")],
        [InlineKeyboardButton("Coupe du Monde", callback_data="foot_cdm")],
    ]
    await update.message.reply_text("Choisissez un championnat:", reply_markup=InlineKeyboardMarkup(keyboard))

async def foot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    league_data = LEAGUE_IDS.get(query.data)
    if not league_data:
        return
    league_id, league_name = league_data
    await query.edit_message_text("Recherche en cours...")
    matches = get_live_scores(league_id)
    await query.edit_message_text(format_matches(matches, league_name))

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    text_norm = normalize(text)

    if user_id not in jumble_sessions or not jumble_sessions[user_id].get("active"):
        return

    session = jumble_sessions[user_id]
    elapsed = time.time() - session["start_time"]
    if elapsed >= 180:
        return

    letters = session["letters"]
    found = session["found_words"]
    remaining = int(180 - elapsed)

    if len(text) < 2:
        return

    if text_norm in [normalize(w) for w in found]:
        await update.message.reply_text(f"'{text}' deja trouve!\nLettres: >>> {letters} <<< | {remaining}s")
        return

    if not can_form_word(text_norm, normalize(letters)):
        await update.message.reply_text(f"❌ '{text}' - Impossible avec ces lettres!\nLettres: >>> {letters} <<< | {remaining}s")
        return

    # Verifier avec dictionnaire etendu
    valid = await asyncio.get_event_loop().run_in_executor(None, check_word_extended, text)

    if valid:
        pts = len(text_norm)
        difficulty = session.get("difficulty", "medium")
        xp = xp_for_word(pts, difficulty)
        found.append(text)
        session["total_points"] += pts
        session["xp_earned"] = session.get("xp_earned", 0) + xp
        update_stats(user_id, update.effective_user.first_name, words_found=1)
        await update.message.reply_text(
            "✅ '" + text + "' +" + str(pts) + "pts +" + str(xp) + "XP\n"
            "Mots: " + str(len(found)) + " | Total: " + str(session["total_points"]) + "pts | " + str(remaining) + "s\n"
            "Lettres: >>> " + letters + " <<<"
        )
    else:
        await update.message.reply_text(
            "❌ '" + text + "' - Mot non reconnu!\n"
            "Lettres: >>> " + letters + " <<< | " + str(remaining) + "s"
        )


# =====================================
# PHASE 1 - XP, LIGUES, PROFIL, NIVEAUX
# =====================================

# ========== DICTIONNAIRE ETENDU ==========
def _build_extended_dict():
    def _n(w):
        w = w.lower().strip()
        return "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")
    words = set()
    all_words = (
        # FR 2 lettres
        "ah ai an as au ba be bi bo bu ca ce ci da de du eh el em en er es et eu ex "
        "fa fi go ha hi ho il in je la le li lo lu ma me mi mo mu na ne ni no nu on "
        "or os ou pa pi po pu ra re ri ro ru sa se si so su ta te ti to tu un us va "
        "ve vi vo vu ya yo "
        # EN 2 lettres
        "ab ad ag ah ai al am an ar at aw ax ay ba be bi bo by do ed ef eh el em en "
        "er es et ex fa fe go ha he hi hm ho id if in is it jo ka ki la li lo ma me "
        "mi mo mu my na ne no nu od oe of oh oi ok om op or ow ox oy pa pe pi po qi "
        "re sh si so ta ti to uh um un up us ut we wo xi xu ya ye "
        # FR 3 lettres
        "ace age ago air ale ami ane arc art bal ban bar bas bat bec bel bol bon but "
        "cal cap car cas cel col con cor cou duc dur eco ela emu eta ete eux fac fan "
        "far fat fer feu fez fil fin fix fol fon for fou fun fur gag gai gal gap gar "
        "gaz gel gen gin glu lac lai lan las lat leu lob log lot lue lui mac mal mas "
        "mat max mer mes met mie mil mis mit mob mod moi mol mon mot mou mue mun mur "
        "mus nez nid nil nom non nos not nou nun ode oie ole ont ora ore ors ose ouf "
        "oui our pad pan par pat pec pen per pet peu pic pin pit pli poi pol pop pot "
        "pou pro pub pue put raz rec ref rem rep res rev rie riz roi ros rot rue rut "
        "sac sas sau sec sel sep set sex ski sol som son sot sou sud sue sus tac tan "
        "tap tar tas tau tic tir ton top tot tou tri tub tue val van var vas ver via "
        "vic vin vis vit vol zoo "
        # EN 3 lettres
        "ace act add age ago aid aim air ale all ant ape apt arc are ark arm art ash "
        "ask awe axe aye bad bag ban bar bat bay bed beg bet bid big bit bog boo bow "
        "box boy bud bug bun bus but buy cab can cap car cat caw cob cod cog cop cot "
        "cow cry cub cup cut dab dam dip dog dot dry dub dug dye ear eat egg ego elf "
        "elm end era eve ewe fad fan far fat fax fee fen few fib fig fin fit fix fly "
        "fog for foe fry fun fur gag gap gas gel gem get gig gin gnu god got gum gun "
        "gut guy gym had ham has hat hay hem hen hew hey hid him hip his hit hob hod "
        "hog hop how hub hug hum hut ice ill imp ink inn ion ire ivy jab jag jam jar "
        "jaw jet jig job jog jot joy jug jut keg ken kip kit lab lag lap law lax lay "
        "lea led leg let lid lip lit log lot low lug mad map mat maw mix mob mop mud "
        "mug nag nap nor oak oar oat odd ode oil old one eon opt orb our out owl own "
        "pad pal pan pap par pat paw pay pea peg pen pep pet pie pig pit ply pod pop "
        "pot pox pry pub pun pup pus put rag ram ran rap rat raw ray red ref rep rev "
        "rib rid rig rip rob rod rot row rub rug rum run rut rye sac sad sag sap sat "
        "saw say sea set sex shy sip sir sis sit ski sky sly sob sod son sow soy spa "
        "spy sty sub sue sum sun sup tab tan tap tar tat tax tie tin tip toe ton too "
        "top toy try tub tug two urn use van vat via vie vim vow wad war was wax way "
        "web wed wig win wit woe wok won woo wow yam yap yaw yep yes yet yew you zap "
        "zed zen zig zip zoo "
        # FR 4+ lettres
        "able acte aide aile aire amie amis ange anis arme arte atre aube auge auto "
        "aveu beau bien bile bleu bloc bois bond bord bout bras brin brun cage camp "
        "cane case cent cepe char chat chef cher chic chou ciel cite clan clip clou "
        "club code coin come cone cote coup cour crac cran cure dame dard date demi "
        "dent deux dire disc dome done dose doue drap dune dure ecot eden edit elan "
        "emir ente epee este etat etre euro face fade fait fane fate fele fete fier "
        "file film fils fine flan flat flic flot flux foie fond font fore fort four "
        "frac frai fret gain gale gare gars gate gaze gene gent gite glas golf gore "
        "gout grad gras gril gris grue hale halo hate heur hier home hors hote inde "
        "iris issu jade jean joli joue jour juge jupe lame lard lent lest leur lice "
        "lieu lime lire lobe loge loin lors loue loup lune mage male malt mare mars "
        "mast mate mere mine mode moue mort mule noel noir note nuit ocre once onde "
        "oral orge orme ours page pale paon pare part pate pave peau pere pied pile "
        "pine pire plan plat plie plot pore port pose prat pres prix puce rade rale "
        "rame rang rape rare rase rate reel rein rent rice ride rire rite robe role "
        "rude ruse sang sans saut seau sere seve silo sole sort sous stop suer sure "
        "tare tele tend tenu tire toit tome tone tore tort trac tram trap tres trio "
        "trop tube tune type vale vane veau vent vers vide vile vine vite voie voir "
        "vole vote vrai zero zone "
        # Mots FR souvent rejetes
        "lit lits lot lots pot pots rot met mets mer fers ver vert verts net nets "
        "set sets jet jets pet pets bet bets art arts part parts car cars bar bars "
        "jar jars tar tars can cans ban bans fan fans van vans pan pans cap caps "
        "map maps nap naps rap raps sap tap taps cat cats bat bats fat hat hats "
        "mat mats pat pats rat rats sat vat bad had lad mad sad bag lag nag rag "
        "sag tag bit fit hit kit pit sit wit bog cog dog fog hog jog log bon con "
        "don ion son ton bug dug jug mug pug rug tug bun fun gun nun pun run sun "
        "cut gut hut nut put rut sol bol col vol "
        # EN 4+ lettres
        "able acid aged also area army away back ball band bank base bath bear beat "
        "bell best bird bite blow blue boat body bold bolt bond bone book bore born "
        "both bowl burn came camp cape card care cart case cast cave cent char chat "
        "chin chip cite clan clap clip clot club clue coal coat coil cold colt come "
        "cord core corn cost cram crop dart data date deal dean dear debt deck deed "
        "deer deli dent diet dirt disc dish disk dock dole dome done door dorm dote "
        "down drag dram draw drip drop drum dual duel dune dupe dust earl earn east "
        "edge edit else emit epic even ever evil exam face fact fail fair fall fame "
        "fang fare farm fast fate fear feat feel fell felt fend fern file fill film "
        "find fine fire firm fist flag flat flaw flea fled flew flip flit flow foam "
        "fold folk fond food fool foot ford fore fork form fort foul four free fuel "
        "full fume gain gale game gang gate gave gaze gear gent germ gild girl give "
        "glad glee glen glib glob glue goal gold golf gone good gore gown grab grad "
        "gram gray grew grid grim grin grip grit grow gulf gust hack hale half hall "
        "halt hand hang hard hare harm harp hart hate have heal heap heat heel held "
        "helm help here hero hide high hike hill hint hire hold hole home hood hook "
        "hope horn host hour hulk hull hump hunt hurt idea idle inch into iron isle "
        "item jade jail jaws jean jeer jibe jilt jive joke jolt jump just keel keen "
        "keep kern kick kind king knob knot lace lack lame lamp land lane lard lark "
        "lash last late lead leaf lean leap lend lens lest liar lice lick lied lies "
        "life lift like lime limp line link lint list live load loam lobe lock loft "
        "lone long look loom lord lore lose lost loud love luck made mail main make "
        "male malt mane mare mark mart mast mate mead meal mean meat meet melt mend "
        "mere mild mile milk mill mind mine mint mire miss mist moan mole molt monk "
        "mood moon moor more mort most move muck mule must nail name near neck need "
        "next nice nick nine node none noon norm nose note null oath odds once open "
        "oral orca oven over pace pack page paid pain pair pale palm pane park part "
        "past path peak peel peer pelt pick pier pile pine pink pipe plan play plod "
        "plot plow plum plus poem poet pole poll pond pore port pose post pour prey "
        "prod prop pull pump pure push race rack raid rail rain rake ramp rang rank "
        "rant rapt rate read real reap reel rein rely rend rent rest rice rich ride "
        "rift ring riot rise risk road roam roar robe rock rode role roll roof room "
        "root rope rose rout rude ruin rule rump rune ruse rush rust safe sail sake "
        "sale salt same sand sane sang sank sate save scan scar seal seam sear seat "
        "self send shed shin ship shoe shop shot shun shut sick side sift sign silk "
        "silo silt sing sink site size skid skim skin skip slab slap slat slim slip "
        "slob slop slot slum slur snag snap snob snot snow soak soar sock soil sold "
        "sole some song soot sore sort soul soup sour span spar spin spit spot spur "
        "stab stag star stay stem step stir stop stub stun suck suit sulk sung sunk "
        "sure surf swam swan swap sway swim tail tale talk tall tame tang tank tare "
        "tart teal team tear teem tell tend tent term than that them then they thin "
        "this tide tile till time tire toad toil told toll tome tone tong tool torn "
        "toss tour town trap tray tree trim trip trod true tube tuck tuft tune tusk "
        "twin type undo upon urge used vale vane vast veil vein vent verb very vest "
        "vial vice view vile vine void volt wade wage wail wake walk wall wand wane "
        "ward ware warm warn warp wart wash wave weak weal wean wear weed weld went "
        "west when whim whip wide wild will wilt wind wine wing wink wire wise wish "
        "wisp woke wold womb wont wood wool word wore work worm worn wrap wren yell "
        "your zeal zero zinc zone zoom "
        # EN mots souvent rejetes
        "got hot not lot bit sit hit fit kit cut but put nut run fun gun sun bug "
        "mug rug tug bag lag nag rag tag bad had lad mad sad man ran tan bin fin "
        "gin kin pin sin tin win bog cog hog jog bud mud cab dab gab jab lab tab "
        "lid bid did hid kid rid cod god mod nod rod sob bob cob fob gob job lob "
        "mob rob cub dub hub pub rub sub "
    )
    for w in all_words.split():
        w = w.strip()
        if len(w) >= 2:
            words.add(_n(w))
    return words

print("Construction du dictionnaire etendu...")
EXTENDED_DICT = _build_extended_dict()
print(f"Dictionnaire: {len(EXTENDED_DICT)} mots")

def check_word_extended(word):
    """Verifie un mot: dictionnaire local + API en ligne"""
    w = normalize(word)
    if len(w) < 2:
        return False
    if w in EXTENDED_DICT:
        return True
    # Verifier aussi dans le dictionnaire original
    if w in FALLBACK_DICT:
        return True
    # API anglaise en ligne
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=2
        )
        if resp.status_code == 200:
            return True
    except:
        pass
    return False

# ========== SYSTEME XP ET LIGUES ==========
XP_FILE = "xp_data.json"

LEAGUES = [
    {"name": "Bronze",  "min_xp": 0,     "emoji": "🥉"},
    {"name": "Silver",  "min_xp": 500,   "emoji": "🥈"},
    {"name": "Gold",    "min_xp": 2000,  "emoji": "🥇"},
    {"name": "Diamond", "min_xp": 5000,  "emoji": "💎"},
    {"name": "Legend",  "min_xp": 15000, "emoji": "👑"},
]

DIFFICULTY_CONFIG = {
    "easy":   {"min_letters": 6,  "max_letters": 8,  "xp_mult": 1.0, "emoji": "🟢"},
    "medium": {"min_letters": 8,  "max_letters": 10, "xp_mult": 1.5, "emoji": "🟡"},
    "hard":   {"min_letters": 10, "max_letters": 12, "xp_mult": 2.0, "emoji": "🟠"},
    "insane": {"min_letters": 12, "max_letters": 15, "xp_mult": 3.0, "emoji": "🔴"},
}

WORD_POOLS = {
    "easy":   ["maison","jardin","soleil","nuage","plage","foret","enfant","famille","nature","planet","garden","castle","bridge","forest","island","animal","candle","bottle","mirror","carpet","window","basket","flower","orange","silver"],
    "medium": ["aventure","lumiere","musique","couleur","histoire","science","voyage","culture","silence","bonheur","liberte","journey","freedom","balance","capture","central","dynamic","fortune","gesture","horizon","justice","kingdom","lantern","machine"],
    "hard":   ["revolution","philosophie","technologie","architecture","experience","education","organisation","communication","generation","atmosphere","temperature","competition","absolutely","adventure","beautiful","carefully","dangerous"],
    "insane": ["extraordinaire","transformation","manifestation","consideration","administration","extraordinary","internationally","predominantly","simultaneously","comprehensively","substantially"],
}

VOWELS_SET = set("aeiouy")
JUMBLE_HISTORY_FILE = "jumble_history.json"

def load_xp():
    if os.path.exists(XP_FILE):
        with open(XP_FILE) as f:
            return json.load(f)
    return {}

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f)

def get_league(xp):
    current = LEAGUES[0]
    for lg in LEAGUES:
        if xp >= lg["min_xp"]:
            current = lg
    return current

def add_xp(user_id, username, xp_amount, difficulty="medium"):
    data = load_xp()
    uid = str(user_id)
    mult = DIFFICULTY_CONFIG.get(difficulty, {}).get("xp_mult", 1.0)
    earned = int(xp_amount * mult)
    if uid not in data:
        data[uid] = {"username": username, "xp": 0}
    old_league = get_league(data[uid].get("xp", 0))["name"]
    data[uid]["xp"] = data[uid].get("xp", 0) + earned
    data[uid]["username"] = username
    new_league = get_league(data[uid]["xp"])
    save_xp(data)
    promoted = old_league != new_league["name"]
    return earned, new_league, promoted

def get_user_xp(user_id):
    return load_xp().get(str(user_id), {"xp": 0})

def xp_for_word(length, difficulty="medium"):
    if length <= 2: base = 2
    elif length == 3: base = 5
    elif length == 4: base = 10
    else: base = 20 + (length - 5) * 5
    return int(base * DIFFICULTY_CONFIG.get(difficulty, {}).get("xp_mult", 1.0))

def load_jumble_history():
    if os.path.exists(JUMBLE_HISTORY_FILE):
        with open(JUMBLE_HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_jumble_history(h):
    with open(JUMBLE_HISTORY_FILE, "w") as f:
        json.dump(h[-50:], f)

def generate_letters(difficulty="medium"):
    config = DIFFICULTY_CONFIG[difficulty]
    pool = WORD_POOLS[difficulty]
    history = load_jumble_history()
    for _ in range(20):
        base = random.choice(pool)
        letters = list(normalize(base.upper()))
        target = random.randint(config["min_letters"], config["max_letters"])
        while len(letters) < target:
            letters.append(random.choice("AEIOUBCDFGHLMNPRST"))
        if len(letters) > config["max_letters"]:
            letters = letters[:config["max_letters"]]
        vowels = sum(1 for l in letters if l.lower() in VOWELS_SET)
        if vowels / len(letters) < 0.25:
            continue
        random.shuffle(letters)
        ls = "".join(letters)
        if ls not in history:
            history.append(ls)
            save_jumble_history(history)
            return ls, difficulty
    fallback = random.choice(["ABDNEATUER", "SOMELICART", "CASTLERIPON", "GRANDPOTILE"])
    return fallback, difficulty

# ========== STATS ET BADGES ==========
STATS_FILE = "stats.json"
BADGES = {
    "first_game":  {"emoji": "🎮", "name": "Premier pas"},
    "word_master": {"emoji": "📚", "name": "Maitre des mots"},
    "quiz_king":   {"emoji": "🧠", "name": "Roi du Quiz"},
    "streak_7":    {"emoji": "🔥", "name": "Semaine de feu"},
    "duel_master": {"emoji": "⚔️", "name": "Dueliste"},
}

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {}

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)

def get_stats(user_id):
    return load_stats().get(str(user_id), {
        "games_played": 0, "words_found": 0,
        "quiz_correct": 0, "streak": 0, "badges": []
    })

def update_stats(user_id, username, **kwargs):
    data = load_stats()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"username": username, "games_played": 0,
                     "words_found": 0, "quiz_correct": 0, "streak": 0, "badges": []}
    data[uid]["username"] = username
    for k, v in kwargs.items():
        data[uid][k] = data[uid].get(k, 0) + v
    badges = data[uid].get("badges", [])
    if data[uid].get("games_played", 0) >= 1 and "first_game" not in badges:
        badges.append("first_game")
    if data[uid].get("words_found", 0) >= 100 and "word_master" not in badges:
        badges.append("word_master")
    if data[uid].get("quiz_correct", 0) >= 50 and "quiz_king" not in badges:
        badges.append("quiz_king")
    if data[uid].get("streak", 0) >= 7 and "streak_7" not in badges:
        badges.append("streak_7")
    data[uid]["badges"] = badges
    save_stats(data)

# ========== PROFIL ==========
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    uid = str(user_id)
    scores = load_scores()
    xp_info = get_user_xp(user_id)
    stats = get_stats(user_id)
    score = scores.get(uid, {}).get("score", 0)
    country_code = scores.get(uid, {}).get("country", "XX")
    country_name = get_country_name(country_code)
    xp = xp_info.get("xp", 0)
    league = get_league(xp)
    next_lg = None
    for i, lg in enumerate(LEAGUES):
        if lg["name"] == league["name"] and i + 1 < len(LEAGUES):
            next_lg = LEAGUES[i + 1]
            break
    all_scores = sorted(scores.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    world_rank = next((i + 1 for i, (k, v) in enumerate(all_scores) if k == uid), "?")
    badge_display = " ".join([BADGES[b]["emoji"] for b in stats.get("badges", []) if b in BADGES])
    if not badge_display:
        badge_display = "Aucun badge encore"
    progress = ""
    if next_lg:
        cur_min = league["min_xp"]
        nxt_min = next_lg["min_xp"]
        prog = min(1.0, (xp - cur_min) / max(1, nxt_min - cur_min))
        filled = int(prog * 10)
        bar = "X" * filled + "-" * (10 - filled)
        pct = int(prog * 100)
        progress = "\n" + bar + " " + str(pct) + "% -> " + next_lg["name"]
    sep = "=" * 20
    msg = "\n".join([
        sep,
        "PROFIL DE " + username.upper(),
        sep,
        "",
        league["emoji"] + " Ligue: " + league["name"],
        "XP: " + str(xp) + progress,
        "",
        "Score: " + str(score) + " pts",
        "Rang mondial: #" + str(world_rank),
        "Pays: " + country_name,
        "",
        "STATISTIQUES",
        "Parties: " + str(stats.get("games_played", 0)),
        "Mots trouves: " + str(stats.get("words_found", 0)),
        "Quiz reussis: " + str(stats.get("quiz_correct", 0)),
        "Streak: " + str(stats.get("streak", 0)) + " jours",
        "",
        "BADGES",
        badge_display,
        sep,
    ])
    await update.message.reply_text(msg)

# ========== JUMBLE AVEC NIVEAUX ==========
async def niveau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Facile (6-8 lettres, XP x1)", callback_data="jlvl_easy")],
        [InlineKeyboardButton("🟡 Moyen (8-10 lettres, XP x1.5)", callback_data="jlvl_medium")],
        [InlineKeyboardButton("🟠 Difficile (10-12 lettres, XP x2)", callback_data="jlvl_hard")],
        [InlineKeyboardButton("🔴 Insane (12-15 lettres, XP x3)", callback_data="jlvl_insane")],
    ]
    await update.message.reply_text(
        "JUMBLE - Choisissez la difficulte:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def jlvl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    difficulty = query.data.replace("jlvl_", "")
    chat_id = query.message.chat_id
    if user_id in jumble_sessions and jumble_sessions[user_id].get("active"):
        s = jumble_sessions[user_id]
        elapsed = time.time() - s["start_time"]
        remaining = int(180 - elapsed)
        if remaining > 0:
            await query.edit_message_text(
                "Partie en cours! Il reste " + str(remaining) + "s\n"
                "Lettres: >>> " + s["letters"] + " <<<"
            )
            return
    letters, diff = generate_letters(difficulty)
    cfg = DIFFICULTY_CONFIG[difficulty]
    jumble_sessions[user_id] = {
        "letters": letters, "found_words": [], "active": True,
        "start_time": time.time(), "chat_id": chat_id,
        "username": query.from_user.first_name, "total_points": 0,
        "difficulty": difficulty, "xp_earned": 0,
    }
    update_stats(user_id, query.from_user.first_name, games_played=1)
    await query.edit_message_text(
        "JUMBLE " + cfg["emoji"] + " " + difficulty.upper() + "!\n\n"
        "Lettres: >>> " + letters + " <<<\n\n"
        "XP multiplicateur: x" + str(cfg["xp_mult"]) + "\n"
        "Points = lettres du mot\n\n"
        "3 minutes! C est parti!"
    )
    asyncio.create_task(jlvl_timer(user_id, chat_id, context))

async def jlvl_timer(user_id, chat_id, context):
    await asyncio.sleep(180)
    if user_id not in jumble_sessions or not jumble_sessions[user_id].get("active"):
        return
    session = jumble_sessions[user_id]
    session["active"] = False
    found = session["found_words"]
    points = session["total_points"]
    xp_earned = session.get("xp_earned", 0)
    username = session["username"]
    difficulty = session.get("difficulty", "medium")
    if points > 0:
        country = get_user_country(user_id)
        add_score(user_id, username, points, country)
        earned_xp, league, promoted = add_xp(user_id, username, xp_earned, difficulty)
        total = get_user_score(user_id)
        mots_str = ", ".join([w + "(" + str(len(normalize(w))) + ")" for w in found])
        lg_emoji = league["emoji"]
        lg_name = league["name"]
        msg = ("Temps ecoule!\n\nMots: " + mots_str + "\n\n"
               "+" + str(points) + " pts | +" + str(earned_xp) + " XP\n"
               "Score: " + str(total) + " pts\n"
               "Ligue: " + lg_emoji + " " + lg_name)
        if promoted:
            msg += "\n\nPROMOTION! " + lg_emoji + " " + lg_name + "!"
        msg += "\n\n/niveau pour rejouer!"
        await context.bot.send_message(chat_id=chat_id, text=msg)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Temps ecoule! Aucun mot valide.\n/niveau pour reessayer!"
        )
    del jumble_sessions[user_id]


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jumble", jumble))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("meteo", meteo))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("foot", foot))
    app.add_handler(CallbackQueryHandler(country_callback, pattern="^(country_|page_)"))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern="^qz_"))
    app.add_handler(CallbackQueryHandler(foot_callback, pattern="^foot_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("niveau", niveau))
    app.add_handler(CallbackQueryHandler(jlvl_callback, pattern="^jlvl_"))
    print("Bot demarre!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()


# ========== SERVEUR HTTP POUR RAILWAY ==========
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DutaBot actif!")
    def log_message(self, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    main()
