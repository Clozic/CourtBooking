CREATE TABLE court_slots (
  course_id     INT,
  session_date  DATE,
  field         TEXT        NOT NULL,
  start_time    TIME,
  end_time      TIME,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  notified_at   TIMESTAMPTZ,
  booked_by_me  BOOLEAN     NOT NULL DEFAULT false,
  PRIMARY KEY (course_id, session_date)
);