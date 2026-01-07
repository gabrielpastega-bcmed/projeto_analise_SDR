"""
Script para testar o cálculo de semana útil.
"""

from datetime import datetime, timedelta
from typing import Optional


def get_week_range(week_start_str: Optional[str] = None) -> tuple[datetime, datetime]:
    """
    Calcula o intervalo da semana ÚTIL a analisar (segunda a sexta).
    """
    if week_start_str:
        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
        week_end = week_start + timedelta(days=4)
    else:
        today = datetime.now()
        days_since_monday = today.weekday()

        if days_since_monday >= 5:
            days_to_last_friday = days_since_monday - 4
        else:
            days_to_last_friday = days_since_monday + 3

        last_friday = today - timedelta(days=days_to_last_friday)
        last_friday = last_friday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        week_start = last_friday - timedelta(days=4)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = last_friday

    return week_start, week_end


def test_week_calculation():
    """Testa o cálculo em diferentes dias da semana."""

    print("=" * 70)
    print("TESTE: Cálculo de Semana Útil (Segunda a Sexta)")
    print("=" * 70 + "\n")

    # Simula diferentes dias
    test_dates = [
        ("2026-01-05", "Domingo"),  # Hoje
        ("2026-01-03", "Sexta"),
        ("2026-01-02", "Quinta"),
        ("2026-01-01", "Quarta"),
        ("2025-12-30", "Terça"),
        ("2025-12-29", "Segunda"),
        ("2025-12-28", "Domingo"),
        ("2025-12-27", "Sábado"),
    ]

    for date_str, day_name in test_dates:
        # Simula "today" sendo essa data
        test_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Calcula manualmente
        days_since_monday = test_date.weekday()

        if days_since_monday >= 5:
            days_to_last_friday = days_since_monday - 4
        else:
            days_to_last_friday = days_since_monday + 3

        last_friday = test_date - timedelta(days=days_to_last_friday)
        week_start = last_friday - timedelta(days=4)
        week_end = last_friday

        print(f"Se hoje fosse: {date_str} ({day_name})")
        print(
            f"  → Semana útil passada: {week_start.strftime('%d/%m/%Y')} (seg) a {week_end.strftime('%d/%m/%Y')} (sex)"
        )
        print()

    print("=" * 70)
    print("RESULTADO ESPERADO PARA HOJE (05/01/2026 - Domingo):")
    print("=" * 70)

    week_start, week_end = get_week_range()
    print(
        f"Semana útil: {week_start.strftime('%d/%m/%Y')} a {week_end.strftime('%d/%m/%Y')}"
    )
    print("\nDias incluídos:")

    current = week_start
    while current <= week_end:
        day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        print(f"  - {current.strftime('%d/%m/%Y')} ({day_names[current.weekday()]})")
        current += timedelta(days=1)


if __name__ == "__main__":
    test_week_calculation()
