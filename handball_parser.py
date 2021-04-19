from selenium import webdriver
from time import sleep
import T_bot as telega
import datetime

def get_liga(driver):
    # Получаем все гантбольные события из меню, исключая женские.
    # Возвращаем словарь {название: ссылка}
    events = {}
    sleep(5)
    sports = driver.find_elements_by_class_name('link--labled')
    for sport in sports:
        event = sport.text.split('\n')[0]
        if 'Женщины' in event:
            continue
        link = sport.get_attribute('href')
        events[event] = link
    return events


def close_all(driver):
    driver.close()
    driver.quit()
    return None


class Bot:
    def __init__(self):
        self.totals = {}
        self.matches = {}
        self.live = {}
        self.live_matches = []
        self.line_matches = []
        self.old_matches = []

    def navigate(self, url):
        if url == 'https://1xstavka.ru/line/Handball/':
            mode = 'line'
        else:
            mode = 'live'
        live_matches = line_matches = []
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x935')
        options.add_argument("--kiosk")
        #options.add_argument("--log-path=tennis.log")
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=options)
        # получаем словарь событий с url
        try:
            driver.get(url)
            driver.implicitly_wait(30)
        except Exception:
            print('Ошибка при потыке перейти на сайт букмекера')
            return None
        try:
            headers = get_liga(driver)
        except:
            print(f' Header = False')
            close_all(driver)
            return None
        if not headers:
            print('Ошибка при потыке перейти на сайт букмекера')
            close_all(driver)
            return

        for header in headers:
            # перебираем каждое событие
            try:
                driver.get(headers[header])
                driver.implicitly_wait(50)
            except:
                continue
            # выводим на экран название события
            event = header
            print('\n', event, '\n', '_' * 30)
            totals = self.get_total(driver, mode)

            if mode == 'line':
                line_matches += list(totals)
                self.totals.update(totals)
            else:
                live_matches += list(totals)
                self.live_checking(totals, event)

        self.itog(mode, line_matches, live_matches)
        driver.close()
        driver.quit()

    def live_checking(self, totals_dic, event):
        #print(f'Все матчи с коэфф-ами {totals_dic}')
        for total in totals_dic:
            # print(f'\n {total}')
            if self.bet_start(total, totals_dic[total][1]):
                if self.check(totals_dic, total):
                    self.old_matches.append(total)
                    event_msg = f'{event}\n{total} \n Коэффициент перед матчем {self.totals[total]}\n ' \
                                f'Текущий коэффициент {totals_dic[total]}'
                    telega.telegram_bot_send_text(event_msg)
                    self.totals.pop(total)

    def check(self, totals, total):
        print(f'Текущий максимальный коэф-ент {totals[total]}, записанный {self.totals[total]}')
        if totals[total][0] >= self.totals[total][0] + 6:
            return True
        else:
            return None

    def itog(self, mode, line_matches, live_matches):
        if mode == 'line':
            self.line_matches = line_matches
            print(line_matches)
            print(f'Количество ожидаемых матчей {len(line_matches)}')
        else:
            self.live_matches = live_matches
            # self.save_matches()
            print(f'Количество рассматриваемых матчей {len(live_matches)}')
            print(f'self.totals= {self.totals}')

    def bet_start(self, teams, koeff):
        # Проверяем есть ли команда в предматчевом списке и коэффициент > 1.3
        if teams in self.totals:
            if koeff >= 1.3:
                # print('Коэффициент > 1,3')
                return True
            else:
                # print('Коэффициент < 1,3')
                return None

    def save_matches(self):
        # Проверяем на ненужные матчи список. Если матч не в листе ожидания и не в текущих матчах,
        # добавляем его в список, затем удаляем все матчи из списка
        actual_matches = self.live_matches + self.line_matches
        old_matches = []
        for i in self.totals:
            if i not in actual_matches:
                old_matches.append(i)
        for i in old_matches:
            self.totals.pop(i)
            print(f'Удален из хранилища {i}')
        print(f'\nЭти матчи уже прошли {old_matches}')
        print(f'количество матчей {len(self.totals)}\n self.matches = {self.totals}')

    def get_total(self, driver, mode):
        # Со страницы события получаем название матча
        # А также значение Тотал М. Возвращаем словарь {матч: [тотал, значение]}
        totals = {}
        games = driver.find_elements_by_class_name('c-events__item_game')

        # перебираем все игры в событии
        for game in games:
            if not self.check_time(game, mode):
                continue
            total = None
            try:
                head = game.find_element_by_class_name('c-events__teams')
            except:
                continue
            # teams = название матча
            teams = head.get_attribute('title')
            if 'Хозяева' in teams or 'Bears' in teams:
                continue
            # Если мы проверяем LIVE то необходимо выбрать подходящее значение тотал
            if mode == 'live':
                # проверяем есть ли этот матч в списке матчей с тоталами для сравнения
                # если мы не нашли матч, то пропускаем его
                if teams not in self.totals:
                    print(f'Комманды нет в списке {teams}')
                    continue
                total = self.find_bet(teams, game)
                target_total = self.totals[teams][0] + 6
                try:
                    if total and total < target_total:
                        #print(f' {teams}\n предматчевый {total}, необходимый {target_total} \n')
                        game_total = {teams: [total, self.totals[teams][1]]}
                        totals.update(game_total)
                        continue
                except:
                    continue
            bets = game.find_element_by_class_name('c-bets').text.split()
            if not total:
                print(f'Нужный тотал не найден или рассматривается LINE')
                total = bets[7]
            if total != '-':
                print(f'Тотал есть и не равен -')
                try:
                    total = float(total)
                except ValueError:
                    print(f'Не могу получить значение {total}')
                try:
                    koeff = float(bets[8])
                except ValueError:
                    print(f'Не могу получить значение {bets[8]}')
                    continue
                print(f'{total}  =  {koeff}')
                game_total = {teams: [total, koeff]}
                totals.update(game_total)
        return totals


    def check_time(self, game, mode):
        # Отбираем только те матчи, которые пройдут в ближайшие 24 часа
        time_raw = game.find_element_by_class_name('c-events__time').get_attribute('title')
        if ' дн' in time_raw:
            return None
        else:
            if mode == 'line':
                print(f' Время до начала матча {time_raw}')
            else:
                print(f'матч идет в настоящее время')
        return True


    def find_bet(self, teams, game):
        # Нажимаем на кнопку со значением тотала и выбираем тот, который на 6 больше предматчевого
        total_name = self.totals[teams][0]
        try:
            buttons = game.find_elements_by_class_name('c-bets__bet')
            button = buttons[7]
            button.click()
            total_list = button.find_element_by_class_name('b-markets-dropdown')
            total_items = total_list.find_elements_by_class_name('b-markets-dropdown__item')
        except:
            print("Ошибка нажатия")
            return
        for item in total_items:
            try:
                text = float(item.text)
                total_item = item
            except:
                print('У элемента нет текста')
                continue
            if text >= total_name + 6:
                print('Найден нужный коэффициент')
                item.click()
                return text
        try:
            # print(f'максимальный тотал на текущий момент {total_item.text}')
            text = total_item.text
            total_item.click()
        except:
            text = None
        if text:
            return float(text)
        else:
            return total_name


def main():
    counter = 1
    x_bot = Bot()
    main_url = 'https://1xstavka.ru/line/Handball/'
    live_url = 'https://1xstavka.ru/live/Handball/'
    t = 3600
    while True:
        now = datetime.datetime.now()
        print(f'counter = {counter}, {str(now)}')
        if t % 3600 == 0:
            print('LINE')
            x_bot.navigate(main_url)
        print('LIVE')
        x_bot.navigate(live_url)
        print('#####################################')
        counter += 1
        sleep(300)
        t += 300


if __name__ == '__main__':
    main()

# https://1xstavka.ru/line/Handball

