DROP VIEW IF EXISTS traffic_timeseries;
DROP TABLE IF EXISTS top_ips;
DROP TABLE IF EXISTS status_by_day;
DROP TABLE IF EXISTS top_urls_by_day;
DROP TABLE IF EXISTS traffic_by_hour;

CREATE TABLE IF NOT EXISTS top_ips (
  day date NOT NULL,
  ip text NOT NULL,
  hits bigint NOT NULL,
  PRIMARY KEY (day, ip)
);

CREATE TABLE IF NOT EXISTS status_by_day (
  day date NOT NULL,
  status integer NOT NULL,
  hits bigint NOT NULL,
  PRIMARY KEY (day, status)
);

CREATE TABLE IF NOT EXISTS top_urls_by_day (
  day date NOT NULL,
  url text NOT NULL,
  hits bigint NOT NULL,
  PRIMARY KEY (day, url)
);

CREATE TABLE IF NOT EXISTS traffic_by_hour (
  day date NOT NULL,
  hour integer NOT NULL CHECK (hour >= 0 AND hour <= 23),
  hits bigint NOT NULL,
  PRIMARY KEY (day, hour)
);

CREATE OR REPLACE VIEW traffic_timeseries AS
SELECT
  day + (hour || ' hours')::interval AS time,
  day,
  hour,
  hits
FROM traffic_by_hour;
