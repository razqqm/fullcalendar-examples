import simpy
import json
import os
import shutil
from colorama import init, Fore, Style

# Инициализация colorama для корректной работы в Windows
init(autoreset=True)

# Глобальные переменные
WORK_HOURS = [(9, 13), (14, 18)]
WORK_DAYS = 5

def slot_process(env, slot, resource):
    """Процесс для каждого слота"""
    with resource.request() as req:
        yield req
        print(Fore.YELLOW + f"Слот {slot['title']} начался в {env.now}")
        yield env.timeout(15)  # каждый слот занимает 15 минут
        print(Fore.GREEN + f"Слот {slot['title']} завершился в {env.now + 15}")

def schedule(env, slots, resource):
    """Генератор слотов"""
    for slot in slots:
        env.process(slot_process(env, slot, resource))
        yield env.timeout(15)  # переход к следующему слоту через 15 минут

# Загрузка событий из файла
with open('events.json', 'r') as file:
    events = [json.loads(line.strip()) for line in file]

# Расчет общего количества доступных слотов в неделю
total_slots = sum([(end - start) * 4 for start, end in WORK_HOURS]) * WORK_DAYS

print(Fore.CYAN + f"Рассчитанное количество слотов: {total_slots}")

if len(events) > total_slots:
    print(Fore.RED + "Слишком много событий для размещения в течение недели!")
    exit()

print(Fore.BLUE + "Начало моделирования процесса распределения слотов...")

# Создание среды моделирования
env = simpy.Environment()

# Ресурс, представляющий доступность слота
resource = simpy.Resource(env, capacity=1)  # в одно время может быть только один слот

# Запуск генератора слотов
env.process(schedule(env, events, resource))

# Запуск моделирования
env.run(until=len(events)*15)  # моделирование продолжается до завершения всех слотов

print(Fore.BLUE + "Моделирование завершено!")

# Интерактивный режим для сохранения
save_choice = input(Fore.MAGENTA + "Хотите ли вы сохранить оптимизированные события? (y/n): ").lower()
if save_choice == 'y':
    # Создаем резервную копию текущего файла
    backup_file = 'events_back.json'
    counter = 1
    while os.path.exists(backup_file):
        backup_file = f'events_back{counter}.json'
        counter += 1
    shutil.copy('events.json', backup_file)
    
    # Сохраняем оптимизированные события
    with open('events.json', 'w') as file:
        for event in events:
            file.write(json.dumps(event) + '\n')
    print(Fore.GREEN + f"События сохранены! Резервная копия создана как {backup_file}")
else:
    print(Fore.RED + "События не сохранены.")
