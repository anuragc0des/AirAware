import db from "../db.js";
import { findUserById } from "../repositories/userRepository.js";

export const getUserDashboardData = async (userId) => {
  const user = await findUserById(userId);
  
  if (!user) {
    const error = new Error("User not found");
    error.status = 404;
    throw error;
  }

  // Find station by user's location
  const stationResult = await db.query(
    "SELECT id, station_name, source_url FROM stations WHERE LOWER(station_name) LIKE LOWER($1) LIMIT 1",
    [`%${user.location}%`]
  );

  if (stationResult.rows.length === 0) {
    const error = new Error(`No station found for location: ${user.location}`);
    error.status = 404;
    throw error;
  }

  const station = stationResult.rows[0];

  // Get latest AQI data with fallback to previous non-null values
  const aqiResult = await db.query(
    `SELECT id, date, pm25, pm10, o3, no2, so2, co, station_id
     FROM aqi_data
     WHERE station_id = $1
     ORDER BY date DESC NULLS LAST
     LIMIT 100`,
    [station.id]
  );

  const rows = aqiResult.rows;
  let latestAqi = null;

  if (rows.length > 0) {
    // Create an object with the most recent non-null value for each field
    const pollutantFields = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co'];
    latestAqi = {
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
  }

  return {
    user: {
      firstName: user.first_name,
      lastName: user.last_name,
      location: user.location,
    },
    station,
    latestAqi,
  };
};

export const getUserTrends = async (userId) => {
  const user = await findUserById(userId);
  
  if (!user) {
    const error = new Error("User not found");
    error.status = 404;
    throw error;
  }

  // Find station by user's location
  const stationResult = await db.query(
    "SELECT id, station_name FROM stations WHERE LOWER(station_name) LIKE LOWER($1) LIMIT 1",
    [`%${user.location}%`]
  );

  if (stationResult.rows.length === 0) {
    const error = new Error(`No station found for location: ${user.location}`);
    error.status = 404;
    throw error;
  }

  const station = stationResult.rows[0];

  // Get historical AQI data (last 30 days)
  const trendsResult = await db.query(
    `SELECT date, pm25, pm10, o3, no2, so2, co
     FROM aqi_data
     WHERE station_id = $1
     AND date >= CURRENT_DATE - INTERVAL '30 days'
     ORDER BY date ASC`,
    [station.id]
  );

  return {
    station,
    data: trendsResult.rows,
  };
};
