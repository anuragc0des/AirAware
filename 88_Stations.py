import subprocess
import sys
import os
import re
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────────

MODEL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Model-XGBoost.py"
)

START_STATION = 1
END_STATION = 88

RESULTS_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "88_station_results.csv"
)

BEST_OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "best_station_output.txt"
)


# ── RUN ONE STATION ───────────────────────────────────────────────────────────

def run_station(station_id):

    print("\n" + "=" * 80)
    print(f"RUNNING STATION {station_id}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, MODEL_FILE, str(station_id)],
        capture_output=True,
        text=True
    )

    output = result.stdout
    error = result.stderr

    if result.returncode != 0:
        print(f"Station {station_id} FAILED")

        if error:
            print(error)

        return None, output, error

    print(f"Station {station_id} completed successfully.")

    return parse_metrics(
        station_id,
        output
    ), output, error


# ── PARSE CLI METRICS ─────────────────────────────────────────────────────────

def parse_metrics(station_id, output):

    results = []

    lines = output.splitlines()

    for line in lines:

        # Example:
        # PM2.5        Full                12.345       5.678        0.901               15.234             2.889

        match = re.match(
            r"^\s*(PM2\.5|PM10|NO2|NH3|SO2|CO|Ozone)"
            r"\s+(\S+)"
            r"\s+([-+]?\d*\.?\d+)"
            r"\s+([-+]?\d*\.?\d+)"
            r"\s+([-+]?\d*\.?\d+)"
            r"\s+([-+]?\d*\.?\d+)"
            r"\s+([-+]?\d*\.?\d+)"
            r"\s*$",
            line
        )

        if match:

            target = match.group(1)
            window = match.group(2)

            rmse = float(match.group(3))
            mae = float(match.group(4))
            r2 = float(match.group(5))
            persistence_rmse = float(match.group(6))
            rmse_difference = float(match.group(7))

            results.append({
                "Station": station_id,
                "Parameter": target,
                "Window": window,
                "RMSE": rmse,
                "MAE": mae,
                "R2": r2,
                "Persistence_RMSE": persistence_rmse,
                "RMSE_Difference": rmse_difference
            })

    return results


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    all_results = []
    station_outputs = {}

    total_stations = END_STATION - START_STATION + 1

    print("\n" + "=" * 80)
    print("AIR AWARE - 88 STATION MODEL RUNNER")
    print("=" * 80)
    print(f"Model: {MODEL_FILE}")
    print(f"Stations: {START_STATION} to {END_STATION}")
    print(f"Total: {total_stations}")
    print("=" * 80)

    # ── RUN ALL 88 STATIONS ───────────────────────────────────────────────────

    for station_id in range(
        START_STATION,
        END_STATION + 1
    ):

        metrics, output, error = run_station(
            station_id
        )

        station_outputs[station_id] = {
            "output": output,
            "error": error
        }

        if metrics:

            all_results.extend(metrics)

            print(
                f"Metrics collected: "
                f"{len(metrics)} parameters"
            )

        else:

            print(
                f"No metrics collected for "
                f"station {station_id}"
            )

    # ── CHECK RESULTS ─────────────────────────────────────────────────────────

    if not all_results:

        print("\nNo successful station results found.")
        sys.exit(1)

    results_df = pd.DataFrame(
        all_results
    )

    # ── SAVE ALL RESULTS ──────────────────────────────────────────────────────

    results_df.to_csv(
        RESULTS_CSV,
        index=False
    )

    print("\n" + "=" * 80)
    print("ALL RESULTS SAVED")
    print("=" * 80)
    print(RESULTS_CSV)

    # ── CALCULATE STATION-LEVEL PERFORMANCE ────────────────────────────────────
    #
    # Best station = lowest average RMSE across its available parameters.

    station_summary = (
        results_df
        .groupby("Station")
        .agg(
            Average_RMSE=("RMSE", "mean"),
            Average_MAE=("MAE", "mean"),
            Average_R2=("R2", "mean"),
            Average_Persistence_RMSE=(
                "Persistence_RMSE",
                "mean"
            ),
            Average_RMSE_Difference=(
                "RMSE_Difference",
                "mean"
            ),
            Parameters=("Parameter", "count")
        )
        .reset_index()
        .sort_values(
            "Average_RMSE",
            ascending=True
        )
    )

    # ── BEST STATION ──────────────────────────────────────────────────────────

    best = station_summary.iloc[0]

    best_station = int(
        best["Station"]
    )

    # ── PRINT RANKING ─────────────────────────────────────────────────────────

    print("\n" + "=" * 80)
    print("STATION RANKING")
    print("=" * 80)

    print(
        station_summary.to_string(
            index=False
        )
    )

    print("\n" + "=" * 80)
    print("BEST STATION")
    print("=" * 80)

    print(
        f"Station: {best_station}"
    )

    print(
        f"Average RMSE: "
        f"{best['Average_RMSE']:.3f}"
    )

    print(
        f"Average MAE: "
        f"{best['Average_MAE']:.3f}"
    )

    print(
        f"Average R²: "
        f"{best['Average_R2']:.3f}"
    )

    print(
        f"Average Persistence RMSE: "
        f"{best['Average_Persistence_RMSE']:.3f}"
    )

    print(
        f"Average RMSE Difference: "
        f"{best['Average_RMSE_Difference']:.3f}"
    )

    print(
        f"Parameters: "
        f"{int(best['Parameters'])}"
    )

    # ── SAVE BEST STATION COMPLETE OUTPUT ─────────────────────────────────────

    with open(
        BEST_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("=" * 80 + "\n")
        f.write("BEST STATION OUTPUT\n")
        f.write("=" * 80 + "\n\n")

        f.write(
            f"Best Station: {best_station}\n"
        )

        f.write(
            f"Average RMSE: "
            f"{best['Average_RMSE']:.3f}\n"
        )

        f.write(
            f"Average MAE: "
            f"{best['Average_MAE']:.3f}\n"
        )

        f.write(
            f"Average R2: "
            f"{best['Average_R2']:.3f}\n"
        )

        f.write(
            f"Average Persistence RMSE: "
            f"{best['Average_Persistence_RMSE']:.3f}\n"
        )

        f.write(
            f"Average RMSE Difference: "
            f"{best['Average_RMSE_Difference']:.3f}\n"
        )

        f.write("\n" + "=" * 80 + "\n")
        f.write("PARAMETER METRICS\n")
        f.write("=" * 80 + "\n\n")

        best_rows = results_df[
            results_df["Station"] == best_station
        ]

        f.write(
            best_rows.to_string(
                index=False
            )
        )

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("COMPLETE MODEL OUTPUT\n")
        f.write("=" * 80 + "\n\n")

        f.write(
            station_outputs[best_station]["output"]
        )

    # ── SAVE STATION SUMMARY ──────────────────────────────────────────────────

    summary_csv = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "station_ranking.csv"
    )

    station_summary.to_csv(
        summary_csv,
        index=False
    )

    print("\n" + "=" * 80)
    print("FINISHED")
    print("=" * 80)

    print(
        f"All parameter results: {RESULTS_CSV}"
    )

    print(
        f"Station ranking: {summary_csv}"
    )

    print(
        f"Best station output: {BEST_OUTPUT}"
    )

    print(
        f"\nBEST STATION = {best_station}"
    )

    print(
        f"BEST AVERAGE RMSE = "
        f"{best['Average_RMSE']:.3f}"
    )