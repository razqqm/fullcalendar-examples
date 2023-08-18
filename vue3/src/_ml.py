import simpy
import math
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

def time_to_minutes(time_value):
    if isinstance(time_value, str):
        h, m = map(int, time_value.split(':'))
        return h * 60 + m
    elif isinstance(time_value, time):
        return time_value.hour * 60 + time_value.minute
    else:
        raise ValueError(f"Unsupported type for time_to_minutes: {type(time_value)}")



def crosses_workhour_boundary(start_time, work_hours):
    next_boundary = None

    # Получим только время из start_time в минутах после полуночи
    current_minutes = start_time.hour * 60 + start_time.minute

    for interval in work_hours:
        work_start, work_end = interval

        # Преобразуем время в минуты после полуночи
        work_start_minutes = time_to_minutes(work_start)
        work_end_minutes = time_to_minutes(work_end)

        # Если текущее время находится между началом и концом интервала, то следующая граница - это конец этого интервала
        if work_start_minutes <= current_minutes < work_end_minutes:
            next_boundary = datetime.combine(start_time.date(), datetime.time(work_end_minutes // 60, work_end_minutes % 60))
            break

    # Если не находим рабочий интервал, который содержит текущее время, это означает, что мы находимся вне рабочего времени (например, ночью)
    if not next_boundary:
        return True

    # Если начало следующего слота будет за пределами текущего рабочего интервала
    if start_time + timedelta(minutes=SLOT_DURATION) > next_boundary:
        return True

    return False



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

        total_required_slots = duration // SLOT_DURATION + (1 if duration % SLOT_DURATION else 0)
        remaining_slots = total_required_slots
        part_number = 1

        while remaining_slots > 0:
            task_start_slot = current_slot_index

            # Если задача начинается на границе рабочего времени, переходим к следующему слоту
            while crosses_workhour_boundary(slots[task_start_slot][0], WORK_HOURS):
                task_start_slot += 1

            task_end_slot = task_start_slot

            # Проверяем, сколько слотов можно использовать перед следующим перерывом
            while task_end_slot - task_start_slot < remaining_slots and not crosses_workhour_boundary(slots[task_end_slot][0], WORK_HOURS):
                task_end_slot += 1

            # Если текущее доступное рабочее время меньше оставшегося времени задачи, то используем все доступное время
            slots_for_this_part = min(remaining_slots, task_end_slot - task_start_slot)
            if slots_for_this_part == 0:
                print(Fore.RED + f"Ошибка: задача '{task['title']}' не может быть распределена из-за ограничений времени. Пропускаем её.")
                break

            task_start_time = slots[task_start_slot][0]
            task_end_time = slots[task_start_slot + slots_for_this_part - 1][0] + timedelta(minutes=SLOT_DURATION)

            task_title = f"{task['title']} {part_number}/{math.ceil(total_required_slots / slots_for_this_part)}"

            print(Fore.YELLOW + f"Задача '{task_title}' началась в {task_start_time.strftime('%H:%M, %A, %Y-%m-%d')} (длительность: {slots_for_this_part} слота/слотов)")
            print(Fore.GREEN + f"Задача '{task_title}' завершилась в {task_end_time.strftime('%H:%M, %A, %Y-%m-%d')}")

            updated_task = task.copy()
            updated_task['title'] = task_title
            updated_task['start'] = task_start_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            updated_task['end'] = task_end_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            updated_tasks.append(updated_task)

            current_slot_index = task_start_slot + slots_for_this_part
            remaining_slots -= slots_for_this_part
            part_number += 1

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




def save_slots_to_json(slots):
    """Сохраняет слоты в файл events.json в виде задач."""
    tasks = []
    for idx, (start_time, _) in enumerate(slots):
        end_time = start_time + timedelta(minutes=SLOT_DURATION)
        task = {
            "id": str(idx),
            "title": "SLOT " + str(idx+1),
            "start": start_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "end": end_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "allDay": False
        }
        tasks.append(task)
    
    with open('events.json', 'a') as file:
        for task in tasks:
            file.write(json.dumps(task) + '\n')


def remove_slot_events_from_file():
    with open('events.json', 'r') as file:
        events = [json.loads(line.strip()) for line in file if line.strip()]

    # Фильтрация событий, исключая события со словом "SLOT" в начале title
    non_slot_events = [event for event in events if not event['title'].startswith("SLOT")]

    with open('events.json', 'w') as file:
        for event in non_slot_events:
            file.write(json.dumps(event) + '\n')
    print(Fore.GREEN + "События-слоты удалены из events.json!")



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
        print("2 - Сохранить сетку слотов")
        print("3 - Удалить события-слоты из файла")
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

        elif choice == "2":
            save_slots_to_json(slots_grid)
            print(Fore.GREEN + "Сетка слотов сохранена в events.json!")

        elif choice == "3":
            remove_slot_events_from_file()

        elif choice == "0":
            print(Fore.GREEN + "Работа скрипта завершена!")
            break
        else:
            print(Fore.RED + "Неизвестная команда. Пожалуйста, попробуйте снова.")