# 📏 kok-userbot-tg: Юзербот для Telegram, измеряющий коки и позволяющий соревноваться! 🏆

[![GitHub issues](https://img.shields.io/github/issues/Mvory9/kok-userbot-tg?style=flat-square)](https://github.com/Mvory9/kok-userbot-tg/issues)
[![GitHub forks](https://img.shields.io/github/forks/Mvory9/kok-userbot-tg?style=flat-square)](https://github.com/Mvory9/kok-userbot-tg/network)
[![GitHub stars](https://img.shields.io/github/stars/Mvory9/kok-userbot-tg?style=flat-square)](https://github.com/Mvory9/kok-userbot-tg/stargazers)
[![GitHub license](https://img.shields.io/github/license/Mvory9/kok-userbot-tg?style=flat-square)](https://github.com/Mvory9/kok-userbot-tg/blob/main/LICENSE)

**Хотите узнать, у кого кок больше?** Этот юзербот поможет вам в этом! 😎

### ❓ Непонятны некоторые элементы игры?

Полная документация по всем командам и игровому процессу на сайте в [Github Pages](https://mvory9.github.io/kok-userbot-tg/).

### ⚠️ Обнаружили баг или есть предложения?

Мы всегда рады вашим отзывам! Пожалуйста, создайте новый [issue](https://github.com/Mvory9/kok-userbot-tg/issues) на GitHub.

---

## 🔑 Инструкция по получению API-токенов от вашего аккаунта Telegram

1.  **Перейдите на страницу API авторизации:** Откройте [API авторизации Telegram](https://my.telegram.org/auth) в вашем браузере.

    ![API Auth](https://github.com/user-attachments/assets/32f34e79-13d4-4ce1-badc-7e68c27cdc49)

2.  **Введите свой номер телефона:** Введите номер телефона, связанный с вашим аккаунтом Telegram. Вы получите код подтверждения в приложении Telegram от службы поддержки.

    ![Enter Phone](https://github.com/user-attachments/assets/0ef8e14b-8cbc-42d7-9041-4c99509fc0ae)

3.  **Получите код подтверждения:** Введите полученный код.

4.  **Откройте "API development tools":** На новом экране нажмите на кнопку "API development tools".

    ![API Tools](https://github.com/user-attachments/assets/798f6c6e-a2fd-414d-beb2-493fdaf70afb)

5.  **Заполните данные приложения:** Заполните поля "App title", "Short name" и выберите "Desktop" в качестве платформы. Пример заполнения представлен ниже:

    ![App Details](https://github.com/user-attachments/assets/16c9f137-848b-4b9e-bea8-8e3a02d806e3)

6.  **Сохраните `api_id` и `api_hash`:**  Если данные введены корректно, вы получите `api_id` и `api_hash`. Обязательно сохраните их в надежном месте! Они необходимы для работы юзербота.

    ![API Credentials](https://github.com/user-attachments/assets/a270fe5c-c80f-495d-a7cb-4585a3f890cb)

---

## ⚙️ Инструкция по установке, подготовке и запуску кода

1.  **Скачайте релиз:** Перейдите на страницу [релизов](https://github.com/Mvory9/kok-userbot-tg/releases/) и скачайте последнюю версию (latest).

    ![Download Release](https://github.com/user-attachments/assets/2692fc6c-acc7-4c3f-a51b-4cec98116b41)

2.  **Распакуйте архив:** Распакуйте скачанный архив в удобное для вас место на компьютере.

3.  **Установите зависимости:** Откройте терминал/командную строку, перейдите в папку с проектом и выполните команду для установки зависимостей Python:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Заполните файл `.env`:** Создайте в папке с проектом файл `.env` и заполните его данными из шага 6 предыдущей инструкции и данными для вашего аккаунта. Пример файла:
    ```
    API_ID=0000000
    API_HASH=iudjjhdyeqkkkkksssss
    PHONE=+3980000000
    LOGIN=yakvenalex_habr
    MONGO_URL=mongodb://127.0.0.1:27017
    ```

---

## 💾 Получаем сессионные файлы для юзербота

1.  **Откройте терминал/командную строку:** Если вы закрыли терминал, откройте его снова и перейдите в папку с проектом.

2.  **Запустите скрипт:** Выполните одну из следующих команд для запуска скрипта получения сессии:
    ```bash
    python3 start_working.py
    ```
    или
    ```bash
    python start_working.py
    ```
    или
    ```bash
    py start_working.py
    ```

3.  **Дождитесь кода подтверждения:** Ожидайте прихода кода подтверждения в ваш Telegram (это может занять несколько минут).

    ![Waiting for Code](https://github.com/user-attachments/assets/dfce1d90-7bc8-4f95-bf3e-86c79e4d8b53)

4.  **Введите код подтверждения:** Введите полученный в Telegram код.

    ![Enter Code](https://github.com/user-attachments/assets/2b4fcc20-8ba7-4acb-afc4-5d6cf5ef88c4)

5.  **Введите облачный пароль (если есть):** Если у вас установлен облачный пароль, введите его. Если ошибок нет, можно остановить выполнение скрипта.

    В результате выполнения данного скрипта будет создан файл сессии.

    ![Session File](https://github.com/user-attachments/assets/1742883a-3bd1-4cdc-a796-a0036d9d1945)

---

## 🎉 Запускаем код и наслаждаемся!

1.  **Откройте терминал/командную строку:** Если вы закрыли терминал, откройте его снова и перейдите в папку с проектом.

2.  **Запустите основной скрипт:** Выполните одну из следующих команд для запуска основного скрипта:
    ```bash
    python3 main.py
    ```
    или
    ```bash
    python main.py
    ```
    или
    ```bash
    py main.py
    ```

3.  **Готово!** Теперь вы можете наслаждаться работой кок-бота на вашем аккаунте! 🎉

---
**Наслаждайтесь и помните:**  Кок-бот это всего лишь развлечение! 😉
