
from pathlib import Path
import pandas as pd

from oecd_data_lab.config import (
    COUNTRIES,
    START_PERIOD,
    END_PERIOD,
)


def find_project_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory

    raise FileNotFoundError("Raiz não encontrada.")


def main():
    root = find_project_root()

    file_path = (
        root / "data" / "coverage"
        / "coverage_response.csv"
    )

    df = pd.read_csv(file_path, low_memory=False)

    expected = pd.period_range(
        START_PERIOD,
        END_PERIOD,
        freq="M",
    )

    print("=== DIAGNÓSTICO DE LACUNAS ===")

    for code, name in COUNTRIES.items():
        subset = df[df["REF_AREA"] == code]

        observed = pd.PeriodIndex(
            subset["TIME_PERIOD"],
            freq="M",
        )

        missing = expected.difference(observed)

        print(f"\n{code} - {name}")
        print(f"Disponíveis: {len(observed.unique())}")
        print(f"Ausentes: {len(missing)}")

        if len(missing):
            # Agrupa meses consecutivos ausentes
            groups = []
            start = previous = missing[0]

            for period in missing[1:]:
                if period.ordinal != previous.ordinal + 1:
                    groups.append((start, previous))
                    start = period
                previous = period

            groups.append((start, previous))

            print("Intervalos ausentes:")

            for first, last in groups:
                if first == last:
                    print(f"  {first}")
                else:
                    print(f"  {first} até {last}")


if __name__ == "__main__":
    main()
