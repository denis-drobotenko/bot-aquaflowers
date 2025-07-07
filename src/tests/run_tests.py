#!/usr/bin/env python3
"""
Скрипт для запуска тестов с различными опциями
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(command, description):
    """Запуск команды с выводом результата"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Команда: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"Код возврата: {result.returncode}")
    print(f"{'='*60}")
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов для сервисов")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "coverage", "fast"],
        default="all",
        help="Тип тестов для запуска"
    )
    parser.add_argument(
        "--service",
        help="Конкретный сервис для тестирования (например: ai_service)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Генерировать HTML отчет о покрытии"
    )
    
    args = parser.parse_args()
    
    # Базовые опции pytest
    base_opts = ["python3", "-m", "pytest"]
    
    if args.verbose:
        base_opts.append("-v")
    
    # Определяем путь к тестам
    tests_path = Path(__file__).parent
    
    if args.type == "all":
        # Все тесты
        command = base_opts + [str(tests_path)]
        success = run_command(" ".join(command), "Запуск всех тестов")
        
    elif args.type == "unit":
        # Только модульные тесты
        unit_path = tests_path / "unit"
        command = base_opts + [str(unit_path)]
        success = run_command(" ".join(command), "Запуск модульных тестов")
        
    elif args.type == "integration":
        # Только интеграционные тесты
        integration_path = tests_path / "integration"
        command = base_opts + [str(integration_path)]
        success = run_command(" ".join(command), "Запуск интеграционных тестов")
        
    elif args.type == "coverage":
        # Тесты с покрытием
        coverage_opts = base_opts + [
            "--cov=src/services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov" if args.html_report else "",
            str(tests_path)
        ]
        command = " ".join([opt for opt in coverage_opts if opt])
        success = run_command(command, "Запуск тестов с покрытием кода")
        
    elif args.type == "fast":
        # Быстрые тесты (без медленных)
        command = base_opts + ["-m", "not slow", str(tests_path)]
        success = run_command(" ".join(command), "Запуск быстрых тестов")
    
    # Если указан конкретный сервис
    if args.service:
        service_test_path = tests_path / "unit" / f"test_{args.service}.py"
        if service_test_path.exists():
            command = base_opts + [str(service_test_path)]
            success = run_command(" ".join(command), f"Тестирование сервиса {args.service}")
        else:
            print(f"❌ Тесты для сервиса {args.service} не найдены")
            print(f"Ожидаемый путь: {service_test_path}")
            success = False
    
    # Итоговый результат
    if success:
        print("\n✅ Все тесты прошли успешно!")
        return 0
    else:
        print("\n❌ Некоторые тесты не прошли")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 