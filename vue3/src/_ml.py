import simpy
import json
import os
import shutil
import pytz
from colorama import init, Fore, Style
from datetime import datetime, timedelta
import locale
from dateutil.parser import parse

# Устанавливаем русскую локаль для корректного вывода даты
locale.setlocale(locale.LC_TIME, 'ru_RU')

# Инициализация colorama для корректной работы в Windows
init(autoreset=True)

# Глобальные переменные
WORK_HOURS = [(9, 13), (14, 18)]
WORK_DAYS = 5
START_DATE = datetime(2023, 8, 10)  # Изменил дату начала для демонстрации
TIMEZONE = pytz.timezone("Asia/Almaty")
SLOT_DURATION = 15  # Длительность каждого слота в минутах
WEEKEND_DAYS = [5, 6]  # список выходных дней (например, суббота и воскресенье)

def create_slots_grid(base_date):
    slots = []
    slot_number = 1
    current_date = base_date
    total_days_added = 0
    
    while total_days_added < WORK_DAYS:
        for start_hour, end_hour in WORK_HOURS:
            current_time = current_date.replace(hour=start_hour, minute=0)
            while current_time.hour < end_hour:
                # Проверка, чтобы слоты не попадали на выходные дни
                if current_time.weekday() not in WEEKEND_DAYS:
                    slot_end_time = current_time + timedelta(minutes=SLOT_DURATION)
                    slot_interval = f"{current_time.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')}"
                    slots.append((current_time, slot_interval))
                    print(Fore.CYAN + f"Слот {slot_number}: {slot_interval}, {current_time.strftime('%A, %Y-%m-%d')}")
                    slot_number += 1
                current_time += timedelta(minutes=SLOT_DURATION)
        
        current_date = next_workday(current_date)
        total_days_added += 1
                
    return slots




def distribute_tasks_on_slots(slots, tasks):
    current_slot_index = 0
    updated_tasks = []

    for task in tasks:
        if not task.get('start') or not task.get('end'):
            print(Fore.RED + f"Ошибка: в задаче '{task['title']}' отсутствует дата начала или окончания.")
            continue

        start_time = parse(task['start'])
        end_time = parse(task['end'])
        duration = (end_time - start_time).seconds // 60
        num_slots = duration // SLOT_DURATION

        # Проверка наличия достаточного количества свободных слотов
        if current_slot_index + num_slots > len(slots):
            print(Fore.RED + f"Ошибка: не хватает слотов для задачи '{task['title']}' с {task['start']} до {task['end']}. Пропускаем её.")
            continue

        task_start_time = slots[current_slot_index][0]
        task_end_time = slots[current_slot_index + num_slots - 1][0] + timedelta(minutes=SLOT_DURATION)

        print(Fore.YELLOW + f"Задача '{task['title']}' началась в {task_start_time.strftime('%H:%M, %A, %Y-%m-%d')} (длительность: {num_slots} слота/слотов)")
        print(Fore.GREEN + f"Задача '{task['title']}' завершилась в {task_end_time.strftime('%H:%M, %A, %Y-%m-%d')}")

        # Обновляем временные метки задачи и конвертируем их в UTC
        task['start'] = task_start_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        task['end'] = task_end_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        updated_tasks.append(task)

        current_slot_index += num_slots

    return updated_tasks



def next_workday(date):
    next_day = date + timedelta(days=1)
    while next_day.weekday() in WEEKEND_DAYS:
        next_day += timedelta(days=1)
    return next_day


def workdays_difference(start, end):
    """Вычисляет разницу в рабочих днях между start и end."""
    if start > end:
        start, end = end, start
    total_days = (end - start).days
    workdays = 0
    for day in range(total_days):
        if (start + timedelta(days=day)).weekday() not in WEEKEND_DAYS:
            workdays += 1
    return workdays



def add_workdays(base, num_days):
    current_date = base
    added_days = 0
    while added_days < num_days:
        current_date += timedelta(days=1)
        if current_date.weekday() not in WEEKEND_DAYS:
            added_days += 1
    return current_date - timedelta(days=1)



if __name__ == "__main__":
    current_datetime = datetime.now(TIMEZONE)
    
    if START_DATE.replace(tzinfo=TIMEZONE) > current_datetime:
        print(Fore.YELLOW + "START_DATE больше текущей даты. Рассчитываем с учетом START_DATE.")
        base_date = START_DATE
    else:
        diff_days = workdays_difference(current_datetime, START_DATE.replace(tzinfo=TIMEZONE))
        print(Fore.YELLOW + f"START_DATE ({START_DATE.strftime('%Y-%m-%d')}) меньше текущей даты на {diff_days} рабочих дней. Рассчитываем с учетом текущей даты.")
        base_date = current_datetime

    # Вычисляем дату через 5 рабочих дней от base_date
    end_date = add_workdays(base_date, 5)
    
    
    print(Fore.GREEN + f"Дата начала: {base_date.strftime('%Y-%m-%d')}")
    print(Fore.RED + f"Дата окончания: {end_date.strftime('%Y-%m-%d')}")


    slots_grid = create_slots_grid(base_date)  # Создаем сетку слотов

    
    while True:
        print(Fore.CYAN + "Выберите команду:")
        print("1 - Провести симуляцию")
        print("0 - Завершить работу")
        choice = input(Fore.MAGENTA + "Ваш выбор: ")

        if choice == "1":
            with open('events.json', 'r') as file:
                events = [json.loads(line.strip()) for line in file if line.strip()]

            total_slots = sum([(end - start) * 4 for start, end in WORK_HOURS]) * WORK_DAYS
            print(Fore.CYAN + f"Рассчитанное количество слотов: {total_slots}")

            if len(events) > total_slots:
                print(Fore.RED + "Слишком много событий для размещения в течение недели!")
                continue

            print(Fore.BLUE + "Начало моделирования процесса распределения слотов...")
            distribute_tasks_on_slots(slots_grid, events)
            print(Fore.BLUE + "Моделирование завершено!")

            save_choice = input(Fore.MAGENTA + "Хотите ли вы сохранить оптимизированные события? (3 - сохранить, любая другая клавиша - вернуться): ")
            if save_choice == '3':
                if not os.path.exists('back'):
                    os.makedirs('back')

                backup_file = 'back/events_back.json'
                counter = 1
                while os.path.exists(backup_file):
                    backup_file = f'back/events_back{counter}.json'
                    counter += 1
                shutil.copy('events.json', backup_file)
                
                with open('events.json', 'w') as file:
                    for event in events:
                        file.write(json.dumps(event) + '\n')
                print(Fore.GREEN + f"События сохранены! Резервная копия создана как {backup_file}")
            else:
                print(Fore.RED + "События не сохранены.")

        elif choice == "0":
            print(Fore.GREEN + "Работа скрипта завершена!")
            break
        else:
            print(Fore.RED + "Неизвестная команда. Пожалуйста, попробуйте снова.")
