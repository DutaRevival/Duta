
import os
import logging
import random
import time
from datetime import datetime, timedelta
import pytz
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configuration du logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Variables Globales et Configuration ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN n'est pas défini dans les variables d'environnement.")
    exit(1)

# Dictionnaire pour stocker les données des utilisateurs (en mémoire pour l'instant)
# user_id: {username, country, score_jumble, score_quiz, xp, level, league, active_game, jumble_state, quiz_state}
user_data = {}

# Dictionnaire pour stocker l'état des jeux Jumble actifs par chat_id
# chat_id: {word, scrambled_word, found_words, players_scores, start_time, difficulty}
active_jumble_games = {}

# Dictionnaire pour stocker l'état des jeux Quiz actifs par chat_id
# chat_id: {questions, current_question_index, players_answers, start_time, difficulty}
active_quiz_games = {}

# Liste de mots français pour le Jumble
FRENCH_WORDS = []
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 12 # Limite pour éviter des mots trop complexes pour le jumble

# Chargement des mots français
try:
    with open("french_words.txt", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH and word.isalpha():
                FRENCH_WORDS.append(word)
    logger.info(f"Chargé {len(FRENCH_WORDS)} mots français.")
except FileNotFoundError:
    logger.error("Le fichier french_words.txt est introuvable. Le jeu Jumble ne fonctionnera pas.")
    FRENCH_WORDS = ["telegram", "python", "jumble", "bot", "intelligence", "artificielle"]

# Niveaux de difficulté pour Jumble et Quiz
DIFFICULTY_LEVELS = {
    "facile": {"jumble_min_len": 4, "jumble_max_len": 6, "quiz_categories": ["General Knowledge"]},
    "moyen": {"jumble_min_len": 7, "jumble_max_len": 9, "quiz_categories": ["Science & Nature", "History"]},
    "difficile": {"jumble_min_len": 10, "jumble_max_len": 12, "quiz_categories": ["Politics", "Mythology", "Art"]},
}

# XP et Niveaux
XP_THRESHOLDS = {
    1: 0, 2: 100, 3: 250, 4: 500, 5: 1000, 6: 2000, 7: 3500, 8: 5000, 9: 7500, 10: 10000
}
LEAGUES = {
    1: "Bronze", 3: "Argent", 5: "Or", 7: "Platine", 9: "Diamant"
}

# --- Fonctions d'aide ---
def get_user_profile(user_id):
    return user_data.setdefault(user_id, {
        'username': None,
        'country': 'Unknown',
        'score_jumble': 0,
        'score_quiz': 0,
        'xp': 0,
        'level': 1,
        'league': 'Bronze',
        'active_game': None,
        'jumble_state': {},
        'quiz_state': {},
        'last_activity': datetime.now()
    })

def update_user_xp(user_id, xp_gained):
    profile = get_user_profile(user_id)
    profile['xp'] += xp_gained
    current_level = profile['level']
    for level, threshold in XP_THRESHOLDS.items():
        if profile['xp'] >= threshold:
            profile['level'] = level
    if profile['level'] > current_level:
        # Mettre à jour la ligue si le niveau change
        for level_threshold, league_name in LEAGUES.items():
            if profile['level'] >= level_threshold:
                profile['league'] = league_name
        return True # Niveau monté
    return False # Niveau inchangé

def scramble_word(word):
    word_list = list(word)
    random.shuffle(word_list)
    return ''.join(word_list)

# --- Commandes du Bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = get_user_profile(user.id)
    profile['username'] = user.username or user.first_name
    await update.message.reply_html(
        f"Salut {user.mention_html()} ! Bienvenue dans le monde des jeux Duta-like !\n"
        "Je suis un bot inspiré par le célèbre Duta de WhatsApp.\n"
        "Tu peux jouer au Jumble, au Quiz, et obtenir des infos sur le foot, la météo et l'heure.\n"
        "Utilise /help pour voir toutes les commandes disponibles."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Voici les commandes disponibles :\n"
        "/start - Lance le bot et t'accueille.\n"
        "/help - Affiche ce message d'aide.\n"
        "/register [pays] - Enregistre ton pays (ex: /register France).\n"
        "/jumble - Lance une partie de Jumble (mots mélangés).\n"
        "/quiz - Lance une série de Quiz.\n"
        "/meteo [ville] - Donne la météo d'une ville (ex: /meteo Paris).\n"
        "/time [ville] - Donne l'heure d'une ville (ex: /time Tokyo).\n"
        "/foot - Affiche les matchs de football.\n"
        "/score - Affiche ton score personnel et ton profil.\n"
        "/top - Affiche le classement des meilleurs joueurs.\n"
    )
    await update.message.reply_text(help_text)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    if not context.args:
        await update.message.reply_text("Merci de spécifier votre pays. Exemple : /register France")
        return
    country = " ".join(context.args).strip()
    profile['country'] = country
    await update.message.reply_text(f"Votre pays a été enregistré comme : {country}.")

async def jumble(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    if chat_id in active_jumble_games:
        await update.message.reply_text("Une partie de Jumble est déjà en cours dans ce chat. Rejoignez le jeu !")
        return

    # Déterminer la difficulté en fonction du niveau de l'utilisateur
    user_level = profile['level']
    if user_level < 3: difficulty = "facile"
    elif user_level < 6: difficulty = "moyen"
    else: difficulty = "difficile"

    min_len = DIFFICULTY_LEVELS[difficulty]["jumble_min_len"]
    max_len = DIFFICULTY_LEVELS[difficulty]["jumble_max_len"]

    possible_words = [w for w in FRENCH_WORDS if min_len <= len(w) <= max_len]
    if not possible_words:
        await update.message.reply_text("Désolé, je n'ai pas de mots pour cette difficulté. Réessayez plus tard.")
        return

    word_to_find = random.choice(possible_words)
    scrambled = scramble_word(word_to_find)

    active_jumble_games[chat_id] = {
        "word": word_to_find,
        "scrambled_word": scrambled,
        "found_words": {},
        "players_scores": {},
        "start_time": datetime.now(),
        "difficulty": difficulty,
        "timer_message_id": None # Pour mettre à jour le message du timer
    }

    await update.message.reply_text(
        f"Nouvelle partie de Jumble lancée (Difficulté: {difficulty}) !\n"
        f"Décodez ce mot : `{scrambled.upper()}`\n"
        "Vous avez 3 minutes. Chaque mot trouvé rapporte 1 point par lettre. Le même mot ne peut être trouvé qu'une fois.\n"
        "Bonne chance !"
    )

    # Lancer le timer
    context.job_queue.run_once(end_jumble_game, 180, data=chat_id, name=f"jumble_{chat_id}")
    # Envoyer un message de timer qui sera mis à jour
    timer_message = await update.message.reply_text("Temps restant : 3:00")
    active_jumble_games[chat_id]["timer_message_id"] = timer_message.message_id
    context.job_queue.run_repeating(update_jumble_timer, interval=10, first=10, last=180, data=chat_id, name=f"jumble_timer_{chat_id}")

async def update_jumble_timer(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data
    if chat_id not in active_jumble_games:
        return

    game_state = active_jumble_games[chat_id]
    elapsed_time = (datetime.now() - game_state["start_time"]).total_seconds()
    remaining_time = 180 - int(elapsed_time)

    if remaining_time <= 0:
        return # Le jeu est déjà terminé ou sur le point de l'être

    minutes = remaining_time // 60
    seconds = remaining_time % 60
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=game_state["timer_message_id"],
            text=f"Temps restant : {minutes:02d}:{seconds:02d}"
        )
    except Exception as e:
        logger.warning(f"Impossible de mettre à jour le message du timer Jumble: {e}")

async def end_jumble_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data
    if chat_id not in active_jumble_games:
        return

    game_state = active_jumble_games.pop(chat_id) # Supprimer le jeu actif
    word_to_find = game_state["word"]
    players_scores = game_state["players_scores"]

    # Annuler le job de mise à jour du timer si toujours actif
    current_jobs = context.job_queue.get_jobs_by_name(f"jumble_timer_{chat_id}")
    for job in current_jobs:
        job.schedule_removal()

    results = "Temps écoulé ! Fin de la partie de Jumble.\n"
    results += f"Le mot à trouver était : **{word_to_find.upper()}**\n\n"

    if not players_scores:
        results += "Personne n'a trouvé de mots cette fois-ci."
    else:
        sorted_scores = sorted(players_scores.items(), key=lambda item: item[1]['score'], reverse=True)
        results += "Scores de la partie :\n"
        for user_id, data in sorted_scores:
            username = user_data[user_id]['username'] if user_id in user_data else f"Joueur {user_id}"
            results += f"- {username}: {data['score']} points (Mots: {', '.join(data['words'])})\n"
            # Mettre à jour l'XP de l'utilisateur
            if update_user_xp(user_id, data['score']):
                profile = get_user_profile(user_id)
                results += f"  -> {username} est passé au niveau {profile['level']} ({profile['league']}) !\n"

    await context.bot.send_message(chat_id=chat_id, text=results, parse_mode='Markdown')

async def handle_jumble_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text.lower()

    if chat_id not in active_jumble_games:
        return # Pas de partie de Jumble en cours

    game_state = active_jumble_games[chat_id]
    word_to_find = game_state["word"]
    scrambled_word_letters = sorted(list(game_state["scrambled_word"]))

    # Vérifier si le mot est valide
    if text not in FRENCH_WORDS:
        # await update.message.reply_text(f"'{text}' n'est pas un mot français valide.")
        return

    # Vérifier si le mot peut être formé avec les lettres du mot mélangé
    text_letters = sorted(list(text))
    temp_scrambled_letters = list(scrambled_word_letters)
    possible = True
    for char in text_letters:
        if char in temp_scrambled_letters:
            temp_scrambled_letters.remove(char)
        else:
            possible = False
            break
    if not possible:
        # await update.message.reply_text(f"'{text}' ne peut pas être formé avec les lettres données.")
        return

    # Vérifier si le mot a déjà été trouvé
    if text in game_state["found_words"]:
        await update.message.reply_text(f"'{text}' a déjà été trouvé par {game_state['found_words'][text]['username']}.")
        return

    # Mot valide et non trouvé
    score_gained = len(text)
    game_state["found_words"][text] = {"user_id": user_id, "username": update.effective_user.username or update.effective_user.first_name}

    if user_id not in game_state["players_scores"]:
        game_state["players_scores"][user_id] = {"score": 0, "words": []}
    game_state["players_scores"][user_id]["score"] += score_gained
    game_state["players_scores"][user_id]["words"].append(text)

    await update.message.reply_text(
        f"Bravo {update.effective_user.mention_html()} ! Vous avez trouvé '{text}' et gagnez {score_gained} points !",
        parse_mode='HTML'
    )

# --- Météo ---
async def meteo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Veuillez spécifier une ville. Exemple : /meteo Paris")
        return
    city = " ".join(context.args)
    url = f"https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current_weather=true&timezone=auto&q={city}"
    # Open-Meteo ne supporte pas la recherche par nom de ville directement, il faut d'abord obtenir lat/lon
    # Pour simplifier, nous allons utiliser une API de géocodage gratuite ou demander à l'utilisateur de fournir lat/lon
    # Pour cette version, je vais simuler une réponse ou utiliser une API de géocodage simple si disponible.
    # Utilisons Nominatim via requests pour obtenir les coordonnées
    geocode_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
    headers = {'User-Agent': 'DutaTelegramBot/1.0'}
    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            display_name = data[0]['display_name']

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            weather_response = requests.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            if 'current_weather' in weather_data:
                current = weather_data['current_weather']
                temperature = current['temperature']
                windspeed = current['windspeed']
                await update.message.reply_text(
                    f"Météo actuelle pour {display_name}:\n"
                    f"Température: {temperature}°C\n"
                    f"Vitesse du vent: {windspeed} km/h"
                )
            else:
                await update.message.reply_text(f"Impossible d'obtenir la météo pour {city}.")
        else:
            await update.message.reply_text(f"Ville '{city}' introuvable.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de la requête météo/géocodage: {e}")
        await update.message.reply_text("Désolé, une erreur est survenue lors de la récupération de la météo.")

# --- Heure ---
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Veuillez spécifier une ville ou un fuseau horaire. Exemple : /time Tokyo")
        return
    location_name = " ".join(context.args)

    try:
        # Tenter de trouver le fuseau horaire par le nom de la ville
        # Ceci est une simplification, une API de géocodage serait plus robuste
        # Pour l'instant, on peut mapper quelques villes ou laisser pytz essayer de deviner
        # Une approche plus robuste serait d'utiliser une API comme Google Time Zone API (non gratuite)
        # ou de demander à l'utilisateur de fournir un fuseau horaire IANA valide.

        # Simplification: on va chercher dans les fuseaux horaires connus par pytz
        # et faire une correspondance partielle.
        found_timezone = None
        for tz_name in pytz.all_timezones:
            if location_name.lower() in tz_name.lower():
                found_timezone = tz_name
                break
        
        if found_timezone:
            tz = pytz.timezone(found_timezone)
            now = datetime.now(tz)
            await update.message.reply_text(f"L'heure actuelle à {location_name} ({found_timezone}) est : {now.strftime('%H:%M:%S')}")
        else:
            await update.message.reply_text(f"Impossible de trouver le fuseau horaire pour '{location_name}'. Essayez un nom de ville plus précis ou un fuseau horaire IANA (ex: Europe/Paris).")

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'heure: {e}")
        await update.message.reply_text("Désolé, une erreur est survenue lors de la récupération de l'heure.")

# --- Football ---
async def foot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "La fonctionnalité Football nécessite une clé API pour accéder aux données en temps réel.\n"
        "Pour l'activer, vous devrez vous inscrire sur un service comme API-Football (plan gratuit disponible) et ajouter votre clé API comme variable d'environnement.\n"
        "En attendant, je ne peux pas afficher les matchs. Désolé !"
    )

# --- Quiz ---
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    if chat_id in active_quiz_games:
        await update.message.reply_text("Une partie de Quiz est déjà en cours dans ce chat. Attendez la fin ou rejoignez le jeu !")
        return

    # Déterminer la difficulté en fonction du niveau de l'utilisateur
    user_level = profile['level']
    if user_level < 3: difficulty = "facile"
    elif user_level < 6: difficulty = "moyen"
    else: difficulty = "difficile"

    # Pour l'instant, questions hardcodées. Idéalement, utiliser une API comme Open Trivia Database.
    # Exemple de structure de question: {"question": "...", "options": ["A", "B", "C"], "answer": "B"}
    questions_data = [
        {"question": "Quelle est la capitale de la France ?", "options": ["Berlin", "Madrid", "Paris"], "answer": "Paris", "difficulty": "facile"},
        {"question": "Qui a écrit 'Les Misérables' ?", "options": ["Alexandre Dumas", "Victor Hugo", "Émile Zola"], "answer": "Victor Hugo", "difficulty": "facile"},
        {"question": "Quel est le plus grand océan du monde ?", "options": ["Atlantique", "Indien", "Pacifique"], "answer": "Pacifique", "difficulty": "moyen"},
        {"question": "En quelle année la Révolution Française a-t-elle commencé ?", "options": ["1789", "1800", "1776"], "answer": "1789", "difficulty": "moyen"},
        {"question": "Quel est le nom scientifique de l'homme ?", "options": ["Homo erectus", "Homo sapiens", "Homo habilis"], "answer": "Homo sapiens", "difficulty": "difficile"},
        {"question": "Qui a peint la Joconde ?", "options": ["Van Gogh", "Léonard de Vinci", "Picasso"], "answer": "Léonard de Vinci", "difficulty": "difficile"},
    ]
    
    # Filtrer par difficulté et prendre 10 questions aléatoires
    filtered_questions = [q for q in questions_data if q["difficulty"] == difficulty]
    if len(filtered_questions) < 10:
        # Si pas assez de questions pour la difficulté, prendre des questions d'autres difficultés
        filtered_questions = random.sample(questions_data, min(10, len(questions_data)))
    else:
        filtered_questions = random.sample(filtered_questions, 10)

    if not filtered_questions:
        await update.message.reply_text("Désolé, je n'ai pas de questions de quiz pour le moment.")
        return

    active_quiz_games[chat_id] = {
        "questions": filtered_questions,
        "current_question_index": 0,
        "players_answers": {},
        "players_scores": {},
        "start_time": datetime.now(),
        "difficulty": difficulty,
        "timer_message_id": None,
        "question_message_id": None
    }

    await send_quiz_question(update, context, chat_id)

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    game_state = active_quiz_games[chat_id]
    q_index = game_state["current_question_index"]
    questions = game_state["questions"]

    if q_index >= len(questions):
        await end_quiz_game(context) # Toutes les questions ont été posées
        return

    question_data = questions[q_index]
    question_text = f"Question {q_index + 1}/10 (Difficulté: {game_state['difficulty']}):\n{question_data['question']}"

    keyboard = []
    for i, option in enumerate(question_data['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_answer_{i}_{chat_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Envoyer la question
    question_message = await context.bot.send_message(chat_id=chat_id, text=question_text, reply_markup=reply_markup)
    game_state["question_message_id"] = question_message.message_id
    game_state["players_answers"] = {} # Réinitialiser les réponses pour la nouvelle question
    game_state["start_time"] = datetime.now() # Réinitialiser le timer pour la question

    # Lancer le timer pour la question
    context.job_queue.run_once(evaluate_quiz_question, 10, data=chat_id, name=f"quiz_q_timer_{chat_id}_{q_index}")
    
    # Envoyer un message de timer qui sera mis à jour
    timer_message = await context.bot.send_message(chat_id=chat_id, text="Temps restant : 0:10")
    game_state["timer_message_id"] = timer_message.message_id
    context.job_queue.run_repeating(update_quiz_timer, interval=1, first=1, last=10, data=chat_id, name=f"quiz_timer_{chat_id}_{q_index}")

async def update_quiz_timer(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data
    if chat_id not in active_quiz_games:
        return

    game_state = active_quiz_games[chat_id]
    elapsed_time = (datetime.now() - game_state["start_time"]).total_seconds()
    remaining_time = 10 - int(elapsed_time)

    if remaining_time < 0:
        return # Le temps est écoulé, la question est évaluée

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=game_state["timer_message_id"],
            text=f"Temps restant : 0:{remaining_time:02d}"
        )
    except Exception as e:
        logger.warning(f"Impossible de mettre à jour le message du timer Quiz: {e}")

async def evaluate_quiz_question(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data
    if chat_id not in active_quiz_games:
        return

    game_state = active_quiz_games[chat_id]
    q_index = game_state["current_question_index"]
    question_data = game_state["questions"][q_index]
    correct_answer = question_data['answer']
    players_answers = game_state["players_answers"]

    correct_players = []
    for user_id, answer_text in players_answers.items():
        if answer_text == correct_answer:
            correct_players.append(user_id)
            if user_id not in game_state["players_scores"]:
                game_state["players_scores"][user_id] = 0
            game_state["players_scores"][user_id] += 10 # 10 points par bonne réponse

    feedback_text = f"La bonne réponse était : **{correct_answer}**\n"
    if correct_players:
        correct_usernames = [user_data[uid]['username'] if uid in user_data else f"Joueur {uid}" for uid in correct_players]
        feedback_text += f"Bravo à : {', '.join(correct_usernames)} !"
    else:
        feedback_text += "Personne n'a trouvé la bonne réponse cette fois-ci."

    # Supprimer le message de la question et du timer
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=game_state["question_message_id"])
        await context.bot.delete_message(chat_id=chat_id, message_id=game_state["timer_message_id"])
    except Exception as e:
        logger.warning(f"Impossible de supprimer les messages du quiz: {e}")

    await context.bot.send_message(chat_id=chat_id, text=feedback_text, parse_mode='Markdown')

    # Passer à la question suivante ou terminer le jeu
    game_state["current_question_index"] += 1
    if game_state["current_question_index"] < len(game_state["questions"]):
        await send_quiz_question(update, context, chat_id) # update est nécessaire pour send_quiz_question
    else:
        await end_quiz_game(context)

async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer() # Répondre au callback pour enlever le 
    # Répondre au callback pour enlever le "loading" sur le bouton

    data = query.data.split("_")
    # data[0] = "quiz", data[1] = "answer", data[2] = index_option, data[3] = chat_id
    
    chat_id = int(data[3])
    user_id = query.from_user.id
    
    if chat_id not in active_quiz_games:
        await query.edit_message_text("Cette partie de quiz est terminée ou n'existe plus.")
        return

    game_state = active_quiz_games[chat_id]
    q_index = game_state["current_question_index"]
    question_data = game_state["questions"][q_index]
    
    selected_option_index = int(data[2])
    selected_answer_text = question_data["options"][selected_option_index]

    if user_id in game_state["players_answers"]:
        await query.answer(text="Vous avez déjà répondu à cette question.", show_alert=True)
        return

    game_state["players_answers"][user_id] = selected_answer_text
    await query.answer(text=f"Votre réponse '{selected_answer_text}' a été enregistrée.")

async def end_quiz_game(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data if context.job else None # Peut être appelé directement ou par job
    if not chat_id or chat_id not in active_quiz_games:
        return

    game_state = active_quiz_games.pop(chat_id) # Supprimer le jeu actif
    players_scores = game_state["players_scores"]

    # Annuler les jobs de timer de la question si toujours actifs
    current_jobs = context.job_queue.get_jobs_by_name(f"quiz_q_timer_{chat_id}_{game_state['current_question_index']-1}")
    for job in current_jobs:
        job.schedule_removal()
    current_jobs = context.job_queue.get_jobs_by_name(f"quiz_timer_{chat_id}_{game_state['current_question_index']-1}")
    for job in current_jobs:
        job.schedule_removal()

    results = "Fin de la série de Quiz !\n\n"

    if not players_scores:
        results += "Personne n'a marqué de points cette fois-ci."
    else:
        sorted_scores = sorted(players_scores.items(), key=lambda item: item[1], reverse=True)
        results += "Scores finaux du Quiz :\n"
        for user_id, score in sorted_scores:
            username = user_data[user_id]["username"] if user_id in user_data else f"Joueur {user_id}"
            results += f"- {username}: {score} points\n"
            # Mettre à jour l'XP de l'utilisateur
            if update_user_xp(user_id, score):
                profile = get_user_profile(user_id)
                results += f"  -> {username} est passé au niveau {profile["level"]} ({profile["league"]}) !\n"

    await context.bot.send_message(chat_id=chat_id, text=results, parse_mode="Markdown")

# --- Profil et Classement ---
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    username = profile["username"] or update.effective_user.first_name
    response_text = (
        f"**Profil de {username}**\n"
        f"Pays: {profile["country"]}\n"
        f"Ligue: {profile["league"]}\n"
        f"Niveau: {profile["level"]} (XP: {profile["xp"]})\n"
        f"Score Jumble: {profile["score_jumble"]}\n"
        f"Score Quiz: {profile["score_quiz"]}\n"
    )
    await update.message.reply_text(response_text, parse_mode="Markdown")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_data:
        await update.message.reply_text("Aucun joueur enregistré pour le moment.")
        return

    sorted_players = sorted(user_data.items(), key=lambda item: item[1]["xp"], reverse=True)

    response_text = "**Classement Mondial (Top 10)**\n"
    for i, (user_id, profile) in enumerate(sorted_players[:10]):
        username = profile["username"] or f"Joueur {user_id}"
        response_text += f"{i+1}. {username} (Niveau {profile["level"]}, XP: {profile["xp"]}) - {profile["league"]}\n"
    
    await update.message.reply_text(response_text, parse_mode="Markdown")

# --- Main Function ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("jumble", jumble))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("meteo", meteo))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("foot", foot))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CommandHandler("top", top))

    # Message Handler pour le jeu Jumble
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_jumble_word))

    # CallbackQuery Handler pour le jeu Quiz
    application.add_handler(CallbackQueryHandler(quiz_button_handler, pattern=r"^quiz_answer_\d+_\d+$"))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
