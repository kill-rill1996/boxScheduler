-- EVENTS
INSERT INTO events (type, title, date, places, min_user_count, active, level, price)
VALUES
    -- День 1 (две записи)
    ('workshop', 'Мастер-класс по SQL', CURRENT_DATE + INTERVAL '1 day' + TIME '10:00:00', 20, 5, true, null, 2000),
    ('lecture', 'Введение в базы данных', CURRENT_DATE + INTERVAL '1 day' + TIME '18:00:00', 30, 3, true, null, 1500),

    -- День 2 (одна запись)
    ('meeting', 'Встреча разработчиков', CURRENT_DATE + INTERVAL '2 days' + TIME '19:00:00', 15, 2, true, null, 1000),

    -- День 3 (две записи)
    ('workshop', 'Продвинутый SQL', CURRENT_DATE + INTERVAL '3 days' + TIME '11:00:00', 15, 5, true, null, 3000),
    ('seminar', 'Оптимизация запросов', CURRENT_DATE + INTERVAL '3 days' + TIME '16:00:00', 25, 4, true, null, 2500),

    -- День 4 (одна запись)
    ('conference', 'IT-конференция', CURRENT_DATE + INTERVAL '4 days' + TIME '09:00:00', 10, 2, false, NULL, 5000),

    -- День 5 (две записи)
    ('training', 'Обучение Python', CURRENT_DATE + INTERVAL '5 days' + TIME '10:00:00', 12, 6, true, null, 4000),
    ('meeting', 'Брейншторм', CURRENT_DATE + INTERVAL '5 days' + TIME '14:00:00', 10, 4, true, NULL, 1000),

    -- День 6 (одна запись)
    ('lecture', 'Архитектура приложений', CURRENT_DATE + INTERVAL '6 days' + TIME '17:00:00', 13, 4, false, null, 1800),

    -- День 7 (одна запись)
    ('workshop', 'Проектирование БД', CURRENT_DATE + INTERVAL '7 days' + TIME '13:00:00', 18, 6, true, null, 3500);