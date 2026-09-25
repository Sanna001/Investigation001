from flask import Flask, render_template, request, jsonify
from player import PlayerManager, PlayerProfile, hash_password
from cases import CaseLoader
from game import GameSession
from case_generator import generate_case

app = Flask(__name__)

player_manager = PlayerManager()
case_loader = CaseLoader()

active_sessions = {}
locked_usernames = set() 

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/command", methods=["POST"])
def handle_command():
    data = request.json
    cmd = data.get("command", "").strip()
    username = data.get("username", "").strip()
    
    if not username:
        return jsonify({"result": "\n[ПОМИЛКА]: Ім'я не може бути порожнім.", "rank": "", "score": 0, "name": ""})
    if username in locked_usernames:
        return jsonify({
            "result": "\n[АКТИВНИЙ ЗАХИСТ]: Доступ заблоковано. Термінал не відповідає на запити.",
            "rank": "",
            "score": 0,
            "name": username,
            "locked": True
        })

    if username not in active_sessions:
        active_sessions[username] = {
            "profile": None,
            "session": None,
            "state": "ASK_PASSWORD",
            "temp_profile": player_manager.load_profile(username),
            "password_attempts": 0
        }

    user_data = active_sessions[username]
    state = user_data["state"]
    if state == "ASK_PASSWORD":
        temp_profile: PlayerProfile = user_data["temp_profile"]
        
        if not temp_profile.password_hash:
            temp_profile.password_hash = hash_password(cmd)
            player_manager.save_profile(temp_profile)
            user_data["profile"] = temp_profile
            
            case_data = case_loader.get_starter_case(0)
            user_data["session"] = GameSession(temp_profile, case_data)
            user_data["state"] = "MENU"
            
            return jsonify({
                "result": f"\n[РЕЄСТРАЦІЯ]: Профіль для '{username}' створено успішно!\nВведіть команду 'start' для перегляду головного меню справи.",
                "rank": temp_profile.get_rank(),
                "score": temp_profile.total_score,
                "name": temp_profile.name,
                "locked": False
            })
        else:
            if temp_profile.password_hash == hash_password(cmd):
                user_data["password_attempts"] = 0
                user_data["profile"] = temp_profile
                try:
                    case_data = case_loader.get_starter_case(temp_profile.solved_count)
                except ValueError:
                    case_data = generate_case(temp_profile.get_rank())

                user_data["session"] = GameSession(temp_profile, case_data)
                user_data["state"] = "MENU"
                
                return jsonify({
                    "result": f"\n[АВТОРИЗАЦІЯ УСПІШНА]: Вітаємо з поверненням, розслідувачу {username}!\nВведіть команду 'start' для перегляду головного меню справи.",
                    "rank": temp_profile.get_rank(),
                    "score": temp_profile.total_score,
                    "name": temp_profile.name,
                    "locked": False
                })
            else:
                user_data["password_attempts"] += 1
                remaining = 3 - user_data["password_attempts"]

                if remaining <= 0:
                    locked_usernames.add(username)
                    if username in active_sessions:
                        del active_sessions[username]
                        
                    return jsonify({
                        "result": "\n[КРИТИЧНА ТРИВОГА]: СУВЕРЕННИЙ ЗАХИСТ АКТИВОВАНО! Виявлено 3 невдалі спроби несанкціонованого доступу. Термінал заблоковано через загрозу безпеці даних Кіберкорпорації!",
                        "rank": "",
                        "score": 0,
                        "name": "",
                        "locked": True
                    })
                else:
                    return jsonify({
                        "result": f"\n[ПОПЕРЕДЖЕННЯ БЕЗПЕКИ]: Невірний пароль. Залишилось спроб: {remaining}.\nСпробуйте ще раз ввести пароль:",
                        "rank": "",
                        "score": 0,
                        "name": username,
                        "locked": False
                    })

    profile: PlayerProfile = user_data["profile"]
    session: GameSession = user_data["session"]
    rank = profile.get_rank()
    response_text = ""

    if state == "WAITING_LEVEL_CHOICE":
        user_data["state"] = "MENU"
        selected_lvl = "Junior Investigator"
        
        if cmd == "1":
            selected_lvl = "Junior Investigator"
        elif cmd == "2" and rank in ["Middle Investigator", "Senior Investigator"]:
            selected_lvl = "Middle Investigator"
        elif cmd == "3" and rank == "Senior Investigator":
            selected_lvl = "Senior Investigator"
        else:
            response_text = "\n[ПОМИЛКА]: Невірний вибір рівня. Автоматично призначено: Junior Investigator.\n"

        session = GameSession(profile, generate_case(selected_lvl))
        user_data["session"] = session
        user_data["last_tree"] = None
        response_text += f"\n[Нова справа успішно згенерована]: Рівень [{selected_lvl}].\nВведіть 'start' для перегляду меню."

        return jsonify({
            "result": response_text,
            "rank": profile.get_rank(),
            "score": profile.total_score,
            "name": profile.name,
            "locked": False
        })

    if state == "WAITING_HYPOTHESIS":
        user_data["state"] = "MENU"
        try:
            tree = session.verify_hypothesis(cmd)
            user_data["last_tree"] = tree
            
            if tree.status == "PROVED":
                profile.solved_count += 1
                profile.total_score += 10
                profile.current_level = profile.get_rank()
                player_manager.save_profile(profile)
                response_text = (
                    f"\n[УСПІХ!]: Гіпотезу успішно ДОВЕДЕНО методом резолюції!\n"
                    f"Оновлені бали: {profile.total_score} | Ранг: {profile.get_rank()}\n"
                    f"Введіть 'start' у головному меню, щоб продовжити."
                )
            else:
                session.attempts_left -= 1
                response_text = f"\n[ВІДМОВА]: Гіпотеза НЕ слідує з бази знань.\nЗалишилось спроб: {session.attempts_left}"
                if session.attempts_left <= 0:
                    response_text += "\n[УВАГА]: Вичерпано ліміт спроб у цій справі!"
        except Exception as e:
            response_text = f"\n[ПОМИЛКА ПАРСИНГУ/ЛОГІКИ]: {e}"
        
        return jsonify({
            "result": response_text,
            "rank": profile.get_rank(),
            "score": profile.total_score,
            "name": profile.name,
            "locked": False
        })

    if cmd.lower() == "start" or cmd.lower() == "меню":
        if rank == "Junior Investigator":
            menu_item_5 = " 5. [Заблоковано] Обрати рівень складності (доступно з Middle)"
        else:
            menu_item_5 = " 5. Обрати рівень складності справи"

        response_text = (
            f"\n========================================\n"
            f" МЕНЮ РОЗСЛІДУВАННЯ (Розслідувач: {profile.name} | Ранг: {rank} | Бали: {profile.total_score}):\n"
            f"========================================\n"
            f" Поточна справа: {session.case_data['title']}\n"
            f" 1. Переглянути опис та легенду справи\n"
            f" 2. Переглянути аксіоми (Базу Знань)\n"
            f" 3. Перевірити гіпотезу (зробити дедуктивний хід)\n"
            f" 4. Показати дерево виведення останнього доведення\n"
            f"{menu_item_5}\n"
            f" 6. Вийти / Зберегти\n"
            f"----------------------------------------\n"
            f"Оберіть пункт меню (1-6):"
        )
    elif cmd == "1":
        c = session.case_data
        legend_str = "\n".join([f"   {k} : {v}" for k, v in c['legend'].items()])
        response_text = (
            f"\n==================================================\n"
            f" БРИФІНГ: {c['title']}\n"
            f"==================================================\n"
            f" Режим: {c['mode']}  |  Рівень: {c['level']}\n\n"
            f" [Опис розслідування]:\n {c['description']}\n\n"
            f" Легенда змінних:\n{legend_str}\n"
            f"=================================================="
        )
    elif cmd == "2":
        axioms_str = "\n".join([f"  [Аксіома {i}]: {ax}" for i, ax in enumerate(session.case_data["axioms"], 1)])
        response_text = f"\n--- БАЗА ЗНАНЬ (АКСІОМИ) ---\n{axioms_str}"
    elif cmd == "3":
        user_data["state"] = "WAITING_HYPOTHESIS"
        response_text = f"\nСпроб залишилось у цій сесії: {session.attempts_left}\nВведіть гіпотезу для перевірки (напр. ~C або C):"
    elif cmd == "4":
        tree = user_data.get("last_tree")
        if not tree or not tree.steps:
            response_text = "\n[Інформація]: Спочатку перевірте хоча б одну гіпотезу."
        else:
            steps_str = "\n".join([f" Крок {idx}: {s.parent1}  +  {s.parent2}  -->  {s.result_clause}" for idx, s in enumerate(tree.steps, 1)])
            response_text = f"\n--- ДЕРЕВО ВИВЕДЕННЯ ---\n{steps_str}"
    elif cmd == "5":
        if rank == "Junior Investigator":
            response_text = f"\n[ДОСТУП ОБМЕЖЕНО]: Ранг Junior Investigator не дозволяє обирати рівень. Набирайте бали та підвищуйте ранг до Middle!\nВведіть 'start' для повернення до меню."
        elif rank == "Middle Investigator":
            user_data["state"] = "WAITING_LEVEL_CHOICE"
            response_text = (
                f"\n--- ОБЕРІТЬ РІВЕНЬ СКЛАДНОСТІ СПРАВИ ---\n"
                f" 1. Junior Investigator\n"
                f" 2. Middle Investigator\n"
                f"Введіть номер рівня (1-2):"
            )
        elif rank == "Senior Investigator":
            user_data["state"] = "WAITING_LEVEL_CHOICE"
            response_text = (
                f"\n--- ОБЕРІТЬ РІВЕНЬ СКЛАДНОСТІ СПРАВИ ---\n"
                f" 1. Junior Investigator\n"
                f" 2. Middle Investigator\n"
                f" 3. Senior Investigator\n"
                f"Введіть номер рівня (1-3):"
            )
    elif cmd == "6":
        player_manager.save_profile(profile)
        response_text = f"\nПрофіль {profile.name} збережено. Сеанс завершено. Можете закрити вкладку."
    else:
        response_text = f"\n[Система]: Невідома команда. Введіть 'start' для виклику головного меню."

    return jsonify({
        "result": response_text,
        "rank": profile.get_rank(),
        "score": profile.total_score,
        "name": profile.name,
        "locked": False
    })
import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)