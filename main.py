import requests
from bs4 import BeautifulSoup
import pandas as pd


BASE_URL = "https://w-stom.ru"
CATEGORY_URL = "https://w-stom.ru/catalog/salfetki_triloks/"

import os
import requests

IMAGE_DIR = r"C:\mylife\Git_project\parser_w-stom.ru\product_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

import re

def download_image(url, article, index):
    """Скачивает изображение и сохраняет с уникальным именем."""
    try:
        # Убираем недопустимые символы из имени файла
        article = re.sub(r'[\\/:"*?<>|]', '_', article)
        
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            ext = url.split(".")[-1].split("?")[0]  # Убираем параметры после "?"
            filename = f"{article}_{index}.{ext}"
            filepath = os.path.join(IMAGE_DIR, filename)

            with open(filepath, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            print(f"✅ Сохранено: {filepath}")  # Проверка
            return filepath  # Возвращаем путь
        else:
            print(f"❌ Ошибка загрузки {url} (код {response.status_code})")
    except Exception as e:
        print(f"⚠ Ошибка скачивания {url}: {e}")

    return ""


def parser_photo(photo_paths, url, article):

    while len(photo_paths) < 7:
        photo_paths.append("")

    return [url, article, *photo_paths]






def get_soup(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, stream=True)
    return BeautifulSoup(response.text, "html.parser")

def get_product_links():
    soup = get_soup(CATEGORY_URL)
    product_links = []
    for div in soup.select("div.items.productList div.item.product .productColImage a.picture"):
        link = div.get("href")
        if link:
            if link.startswith("/"):
                link = f"{BASE_URL}{link}"
            product_links.append(link)
    
    return product_links


def parse_product(url):
    soup = get_soup(url)

    # Инициализация переменных
    breadcrumbs = [li.text.strip() for li in soup.select("li[itemprop='itemListElement'] span[itemprop='name']")][1:]
    category = breadcrumbs[0] if len(breadcrumbs) > 0 else ""
    subcategories = breadcrumbs[1:] if len(breadcrumbs) > 1 else []

    article = ""
    manufacturer = ""

    # Извлечение свойств из propertyList
    property_tables = soup.select("div.propertyList div.propertyTable")
    for prop in property_tables:
        property_name = prop.select_one("div.propertyName").text.strip()
        property_value = prop.select_one("div.propertyValue").text.strip()

        if property_name == "Артикул":
            article = property_value  # Артикул
        elif property_name == "Производитель":
            manufacturer_link = prop.select_one("div.propertyValue a")
            manufacturer = manufacturer_link.text.strip() if manufacturer_link else property_value  # Производитель

    name = soup.select_one("h1.changeName")
    name = name.text.strip() if name else ""

    short_description = soup.select_one(".changeShortDescription")
    short_description = short_description.text.strip() if short_description else ""

    # Полное описание
    full_description = get_full_description(soup)

    # Работа с изображениями
    photo_tags = soup.select(".item a.zoom")
    photo_paths = []

    for i, tag in enumerate(photo_tags[:7]):
        img_url = BASE_URL + tag["href"]
        print(f"🔗 Загружаем: {img_url}")
        img_path = download_image(img_url, article, i + 1)  # Скачиваем изображение
        photo_paths.append(img_path)  # Добавляем только путь к файлу

    # Если есть только одно изображение, остальные колонки остаются пустыми
    max_photos = 7
    while len(photo_paths) < max_photos:
        photo_paths.append("")  # Заполняем пустые пути

    # Извлечение цены и единицы измерения
    price = soup.select_one(".priceVal")
    price = price.text.strip() if price else ""

    unit = soup.select_one(".measure")
    unit = unit.text.strip() if unit else ""

    print(f"Артикул: {article}, Производитель: {manufacturer}, Изображения: {photo_paths}")

    # Возвращаем данные в строгом порядке
    return [
        url, category, *subcategories[:2], article, name,
        short_description, full_description, price, unit,
        *photo_paths, manufacturer
    ]










def get_full_description(soup):
    # Получаем все элементы с классом changeDescription
    description_blocks = soup.find_all("div", class_="changeDescription")

    for block in description_blocks:
        # Проверяем, есть ли атрибут data-first-value (значит, это нужный блок)
        if block.has_attr("data-first-value"):
            full_description_html = block.decode_contents()

            # Заменяем <br> на переносы строк, &nbsp; на пробел
            full_description_html = full_description_html.replace("<br>", "\n").replace("&nbsp;", " ")

            # Преобразуем в читаемый текст, но сохраняя форматирование
            full_description = BeautifulSoup(full_description_html, "html.parser").get_text("\n", strip=True)
            
            return full_description  # Выходим, как только нашли нужный блок

    return ""  # Если не нашли, возвращаем пустую строку



def main():
    product_links = get_product_links()
    data = []
    for link in product_links:
        data.append(parse_product(link))
    
    columns = [
        "URL", "Категория", "Подкатегория 1", "Подкатегория 2", "Артикул", "Наименование",
        "Описание краткое", "Описание полное", "Цена", "Единицы (шт/упак)",
        "Изображение 1", "Изображение 2", "Изображение 3", "Изображение 4", "Изображение 5", "Изображение 6", "Изображение 7",
        "Производитель"
    ]

    
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(r"C:\mylife\Git_project\parser_w-stom.ru\excel\products.xlsx", index=False)
    print("Парсинг завершен. Данные сохранены в products.xlsx")

if __name__ == "__main__":
    main()
