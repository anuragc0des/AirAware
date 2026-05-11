import db from "../db.js";

export const findLatestAqiByStation = async (stationId) => {
  const result = await db.query(
    `SELECT id, date, pm25, pm10, o3, no2, so2, co, station_id
     FROM aqi_data
     WHERE station_id = $1
     ORDER BY date DESC NULLS LAST
     LIMIT 100`,
    [stationId],
  );

  const rows = result.rows;
  if (rows.length === 0) {
    return null;
  }

  // Create an object with the most recent non-null value for each field
  const pollutantFields = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co'];
  const latestAqi = {
    id: rows[0].id,
    station_id: rows[0].station_id,
    date: rows[0].date,
  };

  // For each pollutant, find the most recent non-null value across all rows
  pollutantFields.forEach(field => {
    latestAqi[field] = null;
    for (const row of rows) {
      if (row[field] != null) {
        latestAqi[field] = row[field];
        break;
      }
    }
  });

  return latestAqi;
};

export const findAqiHistory = async (stationId) => {
  const result = await db.query(
    `SELECT id, date, pm25, pm10, o3, no2, so2, co
     FROM aqi_data
     WHERE station_id = $1
     ORDER BY date ASC`,
    [stationId],
  );
  return result.rows;
};

export const findAllAqiRecords = async (stationId) => {
  const result = await db.query(
    `SELECT id, date, pm25, pm10, o3, no2, so2, co, station_id
     FROM aqi_data
     WHERE station_id = $1
     ORDER BY date DESC`,
    [stationId],
  );
  return result.rows;
};

export const findTrendsByStation = async (stationId) => {
  const result = await db.query(
    `SELECT date, pm25, pm10, o3, no2, so2, co
     FROM aqi_data
     WHERE station_id = $1
     ORDER BY date ASC`,
    [stationId],
  );
  return result.rows;
};

export const findOverallPm25Summary = async () => {
  const result = await db.query(
    "SELECT AVG(pm25) AS average_pm25 FROM aqi_data",
  );
  return result.rows[0];
};

export const findLatestPm25ByStation = async () => {
  const result = await db.query(
    `SELECT s.id AS station_id, s.station_name, a.pm25, a.date
     FROM stations s
     JOIN LATERAL (
       SELECT pm25, date
       FROM aqi_data
       WHERE station_id = s.id
       ORDER BY date DESC
       LIMIT 1
     ) a ON true`,
  );
  return result.rows;
};
