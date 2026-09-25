from flask import Flask, render_template, request, jsonify
from player import PlayerManager, PlayerProfile, hash_password
from cases import CaseLoader
from game import GameSession
from case_generator import generate_case

app = Flask(__name__)

player_manager = PlayerManager()
case_loader = CaseLoader()

# Сесії активних підключень за ID сесії / IP
active_sessions = {}
locked_usernames = set()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/command", methods=["POST"])
def handle_command():
    try:
        data = request.json or {}
        cmd = data.get("command", "").strip()
        session_id = data.get("session_id", "default_session")

        # Ініціалізація нової сесії підключення
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "state": "ASK_MODE",  # ASK_MODE, ASK_USERNAME, ASK_PASSWORD, MENU, WAITING_*
                "mode": None,          # 'LOGIN' або 'REGISTER'
                "username": "",
                "password_attempts": 0,
                "profile": None,
                "session": None
            }

        sess = active_sessions[session_id]
        state = sess["state"]

        # КРОК 1: Вибір режиму (Вхід або Реєстрація)
        if state == "ASK_MODE":
            if cmd == "1":
                sess["mode"] = "LOGIN"
                sess["state"] = "ASK_USERNAME"
                return jsonify({
                    "result": "\n[РЕЖИМ ВХОДУ]: Введіть ваше ім'я розслідувача:",
                    "step": "ASK_USERNAME"
                })
            elif cmd == "2":
                sess["mode"] = "REGISTER"
                sess["state"] = "ASK_USERNAME"
                return jsonify({
                    "result": "\n[РЕЖИМ РЕЄСТРАЦІЇ]: Введіть бажане ім'я нового розслідувача:",
                    "step": "ASK_USERNAME"
                })
            else:
                return jsonify({
                    "result": "\n[ПОМИЛКА]: Невірний вибір. Введіть 1 для Входу або 2 для Реєстрації:",
                    "step": "ASK_MODE"
                })

        # КРОК 2: Введення та перевірка імені
        if state == "ASK_USERNAME":
            if not cmd:
                return jsonify({"result": "\n[ПОМИЛКА]: Ім'я не може бути порожнім. Спробуйте ще раз:"})

            if cmd.lower() in [u.lower() for u in locked_usernames]:
                return jsonify({
                    "result": "\n[АКТИВНИЙ ЗАХИСТ]: Доступ для цього користувача заблоковано через загрозу безпеці!",
                    "locked": True
                })

            user_exists = player_manager.exists(cmd)

            if sess["mode"] == "LOGIN":
                if not user_exists:
                    return jsonify({
                        "result": f"\n[ПОМИЛКА ВХОДУ]: Користувача з ім'ям '{cmd}' не знайдено!\nПеревірте ім'я та спробуйте ще раз (або оновіть сторінку для реєстрації):",
                        "step": "ASK_USERNAME"
                    })
                
                real_name = player_manager.get_real_name(cmd)
                sess["username"] = real_name
                sess["profile"] = player_manager.load_profile(real_name)
                sess["state"] = "ASK_PASSWORD"
                return jsonify({
                    "result": f"\n[АВТОРИЗАЦІЯ]: Користувача '{real_name}' знайдено.\nВведіть пароль доступу:",
                    "step": "ASK_PASSWORD"
                })

            elif sess["mode"] == "REGISTER":
                if user_exists:
                    real_name = player_manager.get_real_name(cmd)
                    return jsonify({
                        "result": f"\n[ПОМИЛКА РЕЄСТРАЦІЇ]: Ім'я '{real_name}' вже зайняте іншим розслідувачем!\nВведіть інше бажане ім'я:",
                        "step": "ASK_USERNAME"
                    })
                
                sess["username"] = cmd
                sess["profile"] = PlayerProfile(name=cmd)
                sess["state"] = "ASK_PASSWORD"
                return jsonify({
                    "result": f"\n[РЕЄСТРАЦІЯ]: Ім'я '{cmd}' вільне.\nПридумайте та введіть новий пароль:",
                    "step": "ASK_PASSWORD"
                })

        # КРОК 3: Введення та перевірка пароля
        if state == "ASK_PASSWORD":
            username = sess["username"]
            profile: PlayerProfile = sess["profile"]

            if sess["mode"] == "REGISTER":
                profile.password_hash = hash_password(cmd)
                player_manager.save_profile(profile)

                # ДЛЯ НОВОГО КОРИСТУВАЧА ЗАВЖДИ БЕРЕМО СПРАВУ 001 З JSON
                case_data = case_loader.get_starter_case(profile.solved_count)

                sess["session"] = GameSession(profile, case_data)
                sess["state"] = "MENU"

                return jsonify({
                    "result": f"\n[РЕЄСТРАЦІЯ УСПІШНА]: Акаунт '{username}' успішно створено та збережено!\nВведіть команду 'start' для перегляду меню справи.",
                    "rank": profile.get_rank(),
                    "score": profile.total_score,
                    "name": profile.name,
                    "step": "PLAYING"
                })

            elif sess["mode"] == "LOGIN":
                if profile.password_hash == hash_password(cmd):
                    sess["password_attempts"] = 0

                    # ЯКЩО solved_count == 0 -> СПРАВА 001 З JSON, ІНАКШЕ -> ГЕНЕРУЄМО НОВУ
                    if profile.solved_count == 0:
                        case_data = case_loader.get_starter_case(0)
                    else:
                        case_data = generate_case(profile.get_rank())

                    sess["session"] = GameSession(profile, case_data)
                    sess["state"] = "MENU"

                    return jsonify({
                        "result": f"\n[ВХІД УСПІШНИЙ]: Вітаємо з поверненням, розслідувачу {username}!\nВведіть команду 'start' для перегляду меню справи.",
                        "rank": profile.get_rank(),
                        "score": profile.total_score,
                        "name": profile.name,
                        "step": "PLAYING"
                    })
                else:
                    sess["password_attempts"] += 1
                    remaining = 3 - sess["password_attempts"]

                    if remaining <= 0:
                        locked_usernames.add(username)
                        del active_sessions[session_id]
                        return jsonify({
                            "result": "\n[КРИТИЧНА ТРИВОГА]: СУВЕРЕННИЙ ЗАХИСТ АКТИВОВАНО! Виявлено 3 невдалі спроби входу. Термінал заблоковано!",
                            "locked": True
                        })
                    else:
                        return jsonify({
                            "result": f"\n[ПОПЕРЕДЖЕННЯ БЕЗПЕКИ]: Невірний пароль! Залишилось спроб: {remaining}.\nСпробуйте ще раз:",
                            "step": "ASK_PASSWORD"
                        })

        # ГРА / МЕНЮ СПРАВИ
        profile: PlayerProfile = sess["profile"]
        session: GameSession = sess["session"]
        rank = profile.get_rank()
        response_text = ""

        if state == "WAITING_LEVEL_CHOICE":
            sess["state"] = "MENU"
            selected_lvl = "Junior Investigator"
            if cmd == "1":
                selected_lvl = "Junior Investigator"
            elif cmd == "2" and rank in ["Middle Investigator", "Senior Investigator"]:
                selected_lvl = "Middle Investigator"
            elif cmd == "3" and rank == "Senior Investigator":
                selected_lvl = "Senior Investigator"
            else:
                response_text = "\n[ПОМИЛКА]: Невірний вибір рівня. Автоматично призначено: Junior Investigator.\n"

            sess["session"] = GameSession(profile, generate_case(selected_lvl))
            sess["last_tree"] = None
            response_text += f"\n[Нова справа успішно згенерована]: Рівень [{selected_lvl}].\nВведіть 'start' для перегляду меню."

            return jsonify({
                "result": response_text,
                "rank": profile.get_rank(),
                "score": profile.total_score,
                "name": profile.name
            })

        if state == "WAITING_HYPOTHESIS":
            sess["state"] = "MENU"
            try:
                tree = session.verify_hypothesis(cmd)
                sess["last_tree"] = tree
                
                if tree.status == "PROVED":
                    profile.solved_count += 1
                    profile.total_score += 10
                    profile.current_level = profile.get_rank()
                    
                    # Збереження оновленого профілю
                    player_manager.save_profile(profile)
                    
                    # Лише ПІСЛЯ першої розв'язаної справи (solved_count >= 1) переходимо до процедурної генерації
                    sess["session"] = GameSession(profile, generate_case(profile.get_rank()))
                    
                    response_text = (
                        f"\n[УСПІХ!]: Гіпотезу успішно ДОВЕДЕНО методом резолюції!\n"
                        f"Оновлені бали: {profile.total_score} | Ранг: {profile.get_rank()}\n"
                        f"Дані збережено. Нову справу підготовлено!\n"
                        f"Введіть 'start' у головному меню, щоб перейти до нової справи."
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
                "name": profile.name
            })

        if cmd.lower() in ["start", "меню"]:
            menu_item_5 = " 5. [Заблоковано] Обрати рівень складності (доступно з Middle)" if rank == "Junior Investigator" else " 5. Обрати рівень складності справи"
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
            sess["state"] = "WAITING_HYPOTHESIS"
            response_text = f"\nСпроб залишилось у цій сесії: {session.attempts_left}\nВведіть гіпотезу для перевірки (напр. ~V або V):"
        elif cmd == "4":
            tree = sess.get("last_tree")
            if not tree or not tree.steps:
                response_text = "\n[Інформація]: Спочатку перевірте хоча б одну гіпотезу."
            else:
                steps_str = "\n".join([f" Крок {idx}: {s.parent1}  +  {s.parent2}  -->  {s.result_clause}" for idx, s in enumerate(tree.steps, 1)])
                response_text = f"\n--- ДЕРЕВО ВИВЕДЕННЯ ---\n{steps_str}"
        elif cmd == "5":
            if rank == "Junior Investigator":
                response_text = f"\n[ДОСТУП ОБМЕЖЕНО]: Ранг Junior Investigator не дозволяє обирати рівень.\nВведіть 'start' для повернення до меню."
            elif rank == "Middle Investigator":
                sess["state"] = "WAITING_LEVEL_CHOICE"
                response_text = "\n--- ОБЕРІТЬ РІВЕНЬ СКЛАДНОСТІ СПРАВИ ---\n 1. Junior Investigator\n 2. Middle Investigator\nВведіть номер рівня (1-2):"
            elif rank == "Senior Investigator":
                sess["state"] = "WAITING_LEVEL_CHOICE"
                response_text = "\n--- ОБЕРІТЬ РІВЕНЬ СКЛАДНОСТІ СПРАВИ ---\n 1. Junior Investigator\n 2. Middle Investigator\n 3. Senior Investigator\nВведіть номер рівня (1-3):"
        elif cmd == "6":
            player_manager.save_profile(profile)
            del active_sessions[session_id]
            response_text = f"\nПрофіль {profile.name} збережено. Сеанс завершено. Можете закрити вкладку або оновити сторінку."
        else:
            response_text = f"\n[Система]: Невідома команда. Введіть 'start' для виклику головного меню."

        return jsonify({
            "result": response_text,
            "rank": profile.get_rank(),
            "score": profile.total_score,
            "name": profile.name
        })

    except Exception as err:
        return jsonify({"result": f"\n[ПОМИЛКА СЕРВЕРА]: {str(err)}"}), 500

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)