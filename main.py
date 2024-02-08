from bs4 import BeautifulSoup
import fake_headers
import json
from pprint import pprint
import requests
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
import time
from webdriver_manager.chrome import ChromeDriverManager


def choice_vacancy_count() -> int | None:
    '''Функция для ввода количество вакансий, о которых хотелось бы получить данные
    '''

    number = input('''Введите количество вакансий, которые хотели бы сохранить в файл.\n\
Если вы введете число не более 20, для запроса будет использоваться библиотека requests\n\
Если вы введете число более 20, для запроса будет использоваться библиотека selenium.\n\
При использовании библитеки selenium время выполнения программы может существенно увеличится\n''')
    try:
        number = int(number)
        return number
    except:
        print("Введенное значение не является числом")
        return None


def get_headers() -> dict:
    '''Функция для генерации headers для http запросов
    '''

    headers_gen = fake_headers.Headers(os="win", browser="chrome")
    return headers_gen.generate()


def get_start_page_html(area: int | list[int], text: str = '', currency_code: str = '') -> str | None:
    '''Функция формирует поисковый запрос.
       Параметры:
                area - цифровое обозначение регионов, в которых будет вестись поиск вакансий
                text - текст, по которому будет вестись поиск
    '''

    def create_area_substring(area_numbers):
        '''Функция формирует подстроку с номерами регионов, в которых будет вестись поиск вакансий
        '''

        if isinstance(area_numbers, int):
            return str(area_numbers)
        elif isinstance(area_numbers, list):
            return "&".join([f"area={number}" for number in area_numbers])
        else:
            return ''

    base_url = "https://spb.hh.ru"

    try:
        url = f"/search/vacancy?text={text}&salary=&currency_code={currency_code}&ored_clusters=true&order_by=publication_time&{create_area_substring(area)}&hhtmFrom=vacancy_search_list&hhtmFromLabel=vacancy_search_line"
        url = base_url + url
        return url
    except:
        return None


def get_vacancy_from_page(data: str, data_json: list[dict], number: int = 20) -> tuple:
    '''Функция извлекает данные о вакансиях со страницы
       Параметры:
                data - код страницы
                data_json - список, в который будут добавляться словари с данными о вакансиях
                number - количество вакансий, о которых необходимо получить данные

       Функция возвращает кортеж из двух элементов:
               первый элемент - список словарей с данными по вакансиям,
               второй элемент - ссылка на следующую страницу, если она существует и количество элементов в data_json меньше number,
                                либо None в противном случае 
    '''

    base_url = "https://spb.hh.ru"

    soup = BeautifulSoup(data, 'lxml')
    vacancy_list = soup.find("div", id="a11y-main-content")
    vacancies = vacancy_list.find_all("div", class_="vacancy-serp-item-body")

    for vacancy in vacancies:
        a_html = vacancy.find("a", class_="bloko-link")
        href = a_html['href']
        vacancy_title = a_html.find("span", class_="serp-item__title").text
        salary = vacancy.find("span", class_="bloko-header-section-2")
        company = vacancy.find(
            "a", class_="bloko-link bloko-link_kind-tertiary").text
        city = vacancy.find(
            "div", {"data-qa": "vacancy-serp__vacancy-address"}).text
        data_json.append({
            "vacancy": vacancy_title,
            "linc": href,
            "salary": " ".join(salary.text.split()) if salary else "Не указана",
            "company": " ".join(company.split()),
            "city": " ".join(city.split())
        })
    if len(data_json) < number:
        next_page = soup.find(
            "a", {"class": "bloko-button", "rel": "nofollow", "data-qa": "pager-next"})
        if next_page:
            return data_json, base_url + next_page['href']
        else:
            return data_json, None
    else:
        return data_json, None


def export_data_in_file(data_json: list[dict], file_name: str = "result.json") -> None:
    '''Фунция для записи данных в файл
       Параметры:
                data_json - список, содержащий словари с данными о вакансиях
                file_name - имя файла для записи
    '''
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data_json, file)
    except Exception as err:
        print(err)


def print_data_from_file(file_name: str = "result.json"):
    '''Функция для вывода на печать данных из файла .json
    Параметры:
            file_name - имя файла
    '''
    try:
        with open(file_name, "r", encoding='utf-8') as file:
            data = json.load(file)
            print(f"Общее количество вакансий в файле: {len(data)}\n")
            pprint(data)
    except Exception as err:
        print(err)


def main() -> tuple:
    '''Функция для парсинга данных о вакансиях с сайта https://spb.hh.ru/
       Функция возращает кортеж, первым элементом которого явлется список со словарями с данными по вакансиям,
                                 вторым элементом является число вакансий, о которых необходимо получить данные  
    '''

    number = choice_vacancy_count()
    if not number:
        return None, None

    data_json = []
    next_page = get_start_page_html([1, 2], "python+django+flask")
    if not next_page:
        return None, None

    if number > 20:
        path = ChromeDriverManager().install()
        service = Service(executable_path=path)
        browser = Chrome(service=service)
        while next_page:
            browser.get(next_page)
            time.sleep(1)
            data = browser.page_source
            data_json, next_page = get_vacancy_from_page(
                data, data_json, number)
        return data_json, number
    else:
        response = requests.get(next_page, headers=get_headers())
        if not response or response.status_code != 200:
            return data_json, number
        else:
            data_json, _ = get_vacancy_from_page(response.text, data_json)
            return data_json, number


if __name__ == "__main__":
    data, number = main()

    if data:
        export_data_in_file(data[:number])
        print_data_from_file()
