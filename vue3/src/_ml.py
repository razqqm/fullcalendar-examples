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
START_DATE = datetime(2023, 8, 10)
TIMEZONE = pytz.timezone("Europe/Moscow")
SLOT_DURATION = 15  # Длительность каждого слота в минутах

def create_slots_grid():
    slots = []
    for day in range(WORK_DAYS):
        for start_hour, end_hour in WORK_HOURS:
            current_time = START_DATE + timedelta(days=day, hours=start_hour)
            while current_time.hour != end_hour:
                slots.append(current_time)
                current_time += timedelta(minutes=SLOT_DURATION)
    return slots

def distribute_tasks_on_slots(slots, tasks):
    current_slot_index = 0
    updated_tasks = []
    tasks_per_day = len(tasks) // WORK_DAYS
    current_day_task_count = 0
    current_day = slots[0].day

    for task in tasks:
        start_time = parse(task['start'])
        end_time = parse(task['end'])
        duration = (end_time - start_time).seconds // 60
        num_slots = duration // SLOT_DURATION
        
        # Если текущий день уже заполнен задачами, переходим к следующему дню
        if current_day_task_count >= tasks_per_day and current_day != slots[current_slot_index].day:
            current_day_task_count = 0
            current_day = slots[current_slot_index].day

        task_start_time = slots[current_slot_index]
        task_end_time = slots[current_slot_index + num_slots - 1] + timedelta(minutes=SLOT_DURATION)
        
        print(Fore.YELLOW + f"Слот {task['title']} начался в {task_start_time.strftime('%H:%M, %A, %Y-%m-%d')} (длительность: {num_slots} слота/слотов)")
        print(Fore.GREEN + f"Слот {task['title']} завершился в {task_end_time.strftime('%H:%M, %A, %Y-%m-%d')}")
        
        # Обновляем временные метки задачи
        task['start'] = task_start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        task['end'] = task_end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        updated_tasks.append(task)
        
        current_slot_index += num_slots
        current_day_task_count += 1

    return updated_tasks



with open('events.json', 'r') as file:
    events = [json.loads(line.strip()) for line in file if line.strip()]

total_slots = sum([(end - start) * 4 for start, end in WORK_HOURS]) * WORK_DAYS

print(Fore.CYAN + f"Рассчитанное количество слотов: {total_slots}")

if len(events) > total_slots:
    print(Fore.RED + "Слишком много событий для размещения в течение недели!")
    exit()

print(Fore.BLUE + "Начало моделирования процесса распределения слотов...")

slots_grid = create_slots_grid()
distribute_tasks_on_slots(slots_grid, events)

print(Fore.BLUE + "Моделирование завершено!")

save_choice = input(Fore.MAGENTA + "Хотите ли вы сохранить оптимизированные события? (y/n): ").lower()
if save_choice == 'y':
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
