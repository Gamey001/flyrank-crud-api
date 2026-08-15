CREATE TABLE IF NOT EXISTS tasks (
    id    SERIAL  PRIMARY KEY,
    title TEXT    NOT NULL,
    done  BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tasks (title, done)
SELECT seed.title, seed.done
FROM (
    VALUES
        ('Learn FastAPI', TRUE),
        ('Build a CRUD API', FALSE),
        ('Write a README', FALSE)
) AS seed(title, done)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
