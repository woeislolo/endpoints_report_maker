import argparse
import json
from collections import defaultdict
import logging
from datetime import datetime
import sys

from tabulate import tabulate


logger = logging.getLogger(__name__)


def parse_arguments():
    """ Парсит аргументы из команды в консоли """

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', required=True, nargs='+')
    parser.add_argument('--report', default='average')
    parser.add_argument('--date', type=validate_date, help='Дата в формате YYYY-MM-DD')

    args = parser.parse_args()
    files = args.file
    output_name = args.report
    filter_date = args.date

    return files, filter_date, output_name


def validate_date(filter_date):
    """ Валидирует полученную дату.
    Допустимый вариант состоит из 10 цифр, 
    например: 2025-06-22 """

    if len(filter_date) == 10:
        try:
            datetime.strptime(filter_date, "%Y-%m-%d")
            return filter_date
        except ValueError:
            sys.exit('Дата должна быть в формате YYYY-MM-DD')
    else:
        sys.exit('Дата должна быть в формате YYYY-MM-DD')


def create_counter_with_and_without_filter_date(files, filter_date=None):
    """ Создает счетчик вида {'url': ['total_requests', 'total_time', 'average_time']}
    Есть возможность фильтрации по дате """

    counter = defaultdict(lambda: [0, 0.0, 0])

    for file in files:
        try:
            with open(file, mode='r', encoding='utf8') as f:
                for line in f:
                    try:
                        data = json.loads(line)

                        if filter_date:
                            timestamp = data.get('@timestamp', '')
                            if not timestamp.startswith(filter_date):
                                continue

                        url = data.get('url')
                        response_time = data.get('response_time', None)

                        if url and response_time is not None:
                            counter[url][0] += 1
                            counter[url][1] += response_time
                        else:
                            logger.warning('Пропущены некорректные параметры: url=%s, response_time=%s', 
                                           url, response_time)

                    except json.JSONDecodeError:
                        logger.error('JSONDecodeError: %s', line.strip(), exc_info=False)

        except FileNotFoundError:
            logger.error('Файл не найден: %s', file)
            print(f'Файл не найден: {file}')
    
    if not counter:
        sys.exit('Данные для отчета отсутствуют')

    return counter


def calculate_avg_response_time(counter):
    """ Рассчитывает среднее время ответа для каждого url """

    new_counter = []

    for url, (count, total_time, average_time) in counter.items():
        average_time = total_time / count
        new_counter.append([url, count, average_time])

    return new_counter


def create_table(new_counter):
    """ Выводит в консоль красиво оформленную табличку с результатами,
    заголовки: handler, total, avg_response_time """

    return tabulate(tabular_data=new_counter,
                headers=['handler', 'total', 'avg_response_time'],
                floatfmt=".3f")


def main():
    files, filter_date, output_name = parse_arguments()
    counter = create_counter_with_and_without_filter_date(files, filter_date)
    new_counter = calculate_avg_response_time(counter)
    print(create_table(new_counter))


if __name__ == "__main__":

    logging.basicConfig(filename='log.log',
                        filemode='a',
                        level=logging.WARNING,
                        format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                        datefmt='%H:%M:%S',
                        encoding='utf-8')
    main()
