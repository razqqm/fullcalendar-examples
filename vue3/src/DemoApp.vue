<template>
  <div class='demo-app'>
    <div class='demo-app-sidebar'>
      <div class='demo-app-sidebar-section'>
        <h2>Instructions</h2>
        <ul>
          <li>Select dates and you will be prompted to create a new event</li>
          <li>Drag, drop, and resize events</li>
          <li>Click an event to delete it</li>
        </ul>
      </div>
      <div class='demo-app-sidebar-section'>
        <label>
          <input
            type='checkbox'
            :checked='calendarOptions.weekends'
            @change='handleWeekendsToggle'
          />
          toggle weekends
        </label>
      </div>
      <div class='demo-app-sidebar-section'>
        <h2>All Events ({{ currentEvents.length }})</h2>
        <ul>
          <li v-for='event in currentEvents' :key='event.id'>
            <b>{{ event.startStr }}</b>
            <i>{{ event.title }}</i>
          </li>
        </ul>
      </div>
      <div class='demo-app-sidebar-section'>
        <button @click="saveEventsToServer">Сохранить события</button>
        <button @click="loadEventsFromServer">Загрузить события</button>
      </div>
    </div>
    <div class='demo-app-main'>
      <FullCalendar
        ref="fullCalendar"
        class='demo-app-calendar'
        :options='calendarOptions'
      >
        <template v-slot:eventContent='arg'>
          <b>{{ arg.timeText }}</b>
          <i>{{ arg.event.title }}</i>
        </template>
      </FullCalendar>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import allLocales from '@fullcalendar/core/locales-all';
import { INITIAL_EVENTS, createEventId } from './event-utils'

export default defineComponent({
  components: {
    FullCalendar,
  },
  data() {
    return {
      selectableTimeRanges: [
        {
            daysOfWeek: [1, 2, 3, 4, 5], // Понедельник - Пятница
            startTime: '09:00',
            endTime: '13:00'
        },
        {
            daysOfWeek: [1, 2, 3, 4, 5], // Понедельник - Пятница
            startTime: '14:00',
            endTime: '18:00'
        }
      ],
      calendarOptions: {
        selectConstraint: this.selectableTimeRanges,
        locales: allLocales,             // Все доступные локализации
        locale: 'ru',                   // Текущая локализация (русский язык)
        firstDay: 1,                    // Первый день недели (1 - понедельник)
        slotDuration: '00:15:00',       // Продолжительность каждого временного слота (15 минут)
        slotMinTime: '09:00:00',        // Начальное время для представления дня/недели (9 утра)
        slotMaxTime: '18:00:00',        // Конечное время для представления дня/недели (6 вечера)
        nowIndicator: true,             // Отображает индикатор текущего времени
        eventOverlap: true,             // Разрешает перекрытие событий
        eventDurationEditable: true,    // Позволяет изменять продолжительность события путем перетаскивания
        eventStartEditable: true,       // Позволяет изменять начало события путем перетаскивания
        plugins: [                      // Плагины, используемые в календаре
            dayGridPlugin,              // Плагин для месячного представления
            timeGridPlugin,             // Плагин для представления дня/недели с временными слотами
            interactionPlugin          // Плагин для взаимодействия (перетаскивание, выбор и т. д.)
        ],
        headerToolbar: {                // Панель инструментов в верхней части календаря
            left: 'prev,next today',    // Кнопки в левой части
            center: 'title',            // Заголовок (текущий месяц/неделя/день) в центре
            right: 'dayGridMonth,timeGridWeek,timeGridDay' // Кнопки смены представления в правой части
        },
        initialView: 'dayGridMonth',    // Начальное представление календаря (месяц)
        initialEvents: INITIAL_EVENTS,  // Начальные события
        editable: true,                 // Позволяет редактировать события (перетаскивание, изменение размера)
        selectable: true,               // Позволяет выбирать даты и временные интервалы
        selectMirror: true,             // Отображает временное событие при перетаскивании
        dayMaxEvents: true,             // Максимальное количество событий на день в месячном представлении
        weekends: false,                 // Отображать выходные дни
        select: this.handleDateSelect,  // Обработчик выбора даты или временного интервала
        eventClick: this.handleEventClick, // Обработчик клика по событию
        eventsSet: this.handleEvents,   // Обработчик установки событий
        businessHours: [
            // рабочие часы с 9 утра до 1 дня
            {
                daysOfWeek: [1, 2, 3, 4, 5], // Понедельник - Пятница
                startTime: '09:00',
                endTime: '13:00'
            },
            // рабочие часы с 2 дня до 6 вечера (исключая обеденное время с 1 до 2)
            {
                daysOfWeek: [1, 2, 3, 4, 5], // Понедельник - Пятница
                startTime: '14:00',
                endTime: '18:00'
            }
        ],
     },
      currentEvents: [],
    }
  },
  methods: {
    handleWeekendsToggle() {
      this.calendarOptions.weekends = !this.calendarOptions.weekends
    },
    handleDateSelect(selectInfo) {
      const selectedStart = selectInfo.start;
      const lunchStart = new Date(selectedStart);
      lunchStart.setHours(13, 0, 0);
      const lunchEnd = new Date(selectedStart);
      lunchEnd.setHours(14, 0, 0);

      if (selectedStart >= lunchStart && selectedStart < lunchEnd) {
        alert('В это время обеденный перерыв. Пожалуйста, выберите другое время.');
        return;
      }

      let title = prompt('Please enter a new title for your event');
      let calendarApi = selectInfo.view.calendar;

      calendarApi.unselect();

      if (title) {
        calendarApi.addEvent({
          id: createEventId(),
          title,
          start: selectInfo.startStr,
          end: selectInfo.endStr,
          allDay: selectInfo.allDay
        });
      }
    },
   
    
    handleEventClick(clickInfo) {
      if (confirm(`Are you sure you want to delete the event '${clickInfo.event.title}'`)) {
        clickInfo.event.remove()
      }
    },
    handleEvents(events) {
      this.currentEvents = events
    },
    async loadEventsFromServer() {
        try {
            const response = await fetch('http://localhost:3000/events');
            const events = await response.json();
            const calendarApi = this.$refs.fullCalendar.getApi();
            calendarApi.removeAllEvents();
            events.forEach(event => {
                calendarApi.addEvent(event);
            });
        } catch (error) {
            console.error("Error loading events:", error);
        }
    },
    async saveEventsToServer() {
        try {
            const events = this.currentEvents.map(event => {
                return {
                    id: event.id,
                    title: event.title,
                    start: event.start.toISOString(),
                    end: event.end ? event.end.toISOString() : null,
                    allDay: event.allDay
                };
            });
            await fetch('http://localhost:3000/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(events)
            });
        } catch (error) {
            console.error("Error saving events:", error);
        }
    }
  }
})
</script>

<style lang='css'>
h2 {
  margin: 0;
  font-size: 16px;
}

ul {
  margin: 0;
  padding: 0 0 0 1.5em;
}

li {
  margin: 1.5em 0;
  padding: 0;
}

b {
  margin-right: 3px;
}

.demo-app {
  display: flex;
  min-height: 100%;
  font-family: Arial, Helvetica Neue, Helvetica, sans-serif;
  font-size: 14px;
}

.demo-app-sidebar {
  width: 300px;
  line-height: 1.5;
  background: #eaf9ff;
  border-right: 1px solid #d3e2e8;
}

.demo-app-sidebar-section {
  padding: 2em;
}

.demo-app-main {
  flex-grow: 1;
  padding: 3em;
}

.fc {
  max-width: 1100px;
  margin: 0 auto;
}
</style>
