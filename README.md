# todofse

## UI Prototyp
https://www.figma.com/design/MzwpbR6DFNJvDRwkuvOCxV/To-do-Liste?node-id=1-2&t=SizUd1L2nwv1Hl1U-0

## Backend-Repository
https://github.com/LLf13/todofse-backend

## Architektur
```mermaid
---
title: Datenstruktur (MongoDB)
---
erDiagram
    Todo{
        int _id
        int user_id
        datetime created_at
        datetime updated_at
        String title
        String description
        datetime due_date
        String status
        String priority
    }
    
    Termin{
        int _id
        int user_id
        datetime created_at
        datetime updated_at
        String title
        datetime timestamp
        String location
        boolean repeated
        String repeat_intervall
    }
    
    User{
        int user_id
        String username
        String password
    }
```

```mermaid
---
title: Anmeldeprozess
---
flowchart LR
    Start
    Stop
    seite[Nutzer sieht Login-seite]
    daten[Nutzerdaten eingeben]
    click_login[Login button drücken]
    Dashboard[Nutzer sieht das Dashboard]
    
    Start --> seite
    seite --> daten
    daten --> click_login
    click_login -->|fehlerhaft| daten
    click_login -->|erfolgreich| Dashboard
    Dashboard --> Stop
```

```mermaid
---
title: Todo anlegen
---
flowchart TD
    Start
    Stop
    dashboard[Nutzer sieht Dashboard]
    widget[Nutzer klickt Todo-Widget]
    menu[Nutzer öffnet Menü]
    todo-menu[Klick auf 'Todos'-Tab]
    todo-list[Nutzer sieht große Todo-Liste]
    add[Klick auf 'Hinzufügen']
    form[Alle Felder ausfüllen]
    add-todo[Klick auf 'Todo hinzufügen']
    
    Start --> dashboard
    dashboard --> widget
    dashboard --> menu
    menu --> todo-menu
    widget --> todo-list
    todo-menu --> todo-list
    todo-list --> add
    add --> form
    form --> add-todo
    add-todo -->|erfolgreich| Stop
    add-todo --> |fehlerhaft| form
```




