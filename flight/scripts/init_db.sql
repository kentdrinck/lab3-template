CREATE TABLE IF NOT EXISTS airport (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(255),
    city    VARCHAR(255),
    country VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS flight (
    id              SERIAL PRIMARY KEY,
    flight_number   VARCHAR(20)              NOT NULL,
    datetime        TIMESTAMP WITH TIME ZONE NOT NULL,
    from_airport_id INT REFERENCES airport (id),
    to_airport_id   INT REFERENCES airport (id),
    price           INT                      NOT NULL
);

-- Тестовые данные
INSERT INTO airport (id, name, city, country) VALUES (1, 'Шереметьево', 'Москва', 'Россия') ON CONFLICT DO NOTHING;
INSERT INTO airport (id, name, city, country) VALUES (2, 'Пулково', 'Санкт-Петербург', 'Россия') ON CONFLICT DO NOTHING;

INSERT INTO flight (flight_number, datetime, from_airport_id, to_airport_id, price) 
VALUES ('AFL031', '2021-10-08 20:00:00+03', 2, 1, 1500) ON CONFLICT DO NOTHING;