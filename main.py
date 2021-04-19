from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep

import T_bot as telega


class Bot:
    def __init__(self):

        self.totals = {}
        self.matches = {}
        self.live = {}
        self.live_matches = []
        self.line_matches = []

    def close_all(self, driver):
        driver.close()
        driver.quit()
        return None

    def navigate(self, url):
        difference = 0.1
        live_matches = line_matches = []
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x935')
        options.add_argument("--kiosk")
        driver = webdriver.Chrome(chrome_options=options)
        temp_matches = {}
        try:
            driver.get(url)
            driver.implicitly_wait(30)
        except Exception:
            print('Error in line 34')
            return None
        try:
            headers = self.get_liga(driver)
        except:
            print(f' Header = False')
            return None
        if not headers:
            return self.close_all(driver)
        # print(f'self.mathes = {self.matches.keys()}')
        for header in headers:
            driver.get(headers[header])
            driver.implicitly_wait(50)
            event = header
            print('\n', event, '\n', '_' * 15)
            '''
            teams = driver.find_elements_by_class_name('c-events__teams')
            links = driver.find_elements_by_class_name('c-events__name')
            titles = [team.get_attribute('title') for team in teams]
            links = [link.get_attribute('href') for link in links][1:]
            matches = dict(zip(titles, links))
            '''
            totals = self.get_total(driver, None)
            if url == 'https://1xstavka.ru/line/Handball/':
                line_matches += list(totals)
                self.totals.update(totals)
            else:
                live_matches += list(totals)
                for total in totals:
                    if self.bet_start(total, totals[total], difference):
                        event_msg = f'\n{total} \n Коэффициент перед матчем {self.totals[total]}\n ' \
                                    f'Текущий коэффициент {totals[total]}'
                        print(f'Предварительное сообщение {event_msg}')
                        telega.telegram_bot_send_text(event_msg)
                        self.totals.pop(total)

        self.itog(url, line_matches, live_matches)
        driver.close()
        driver.quit()
        '''
            if url == 'https://1xstavka.ru/line/Handball/':
                line_matches.update(matches)
                temp_matches = line_matches
            else:
                live_matches.update(matches)
                temp_matches = live_matches
            #print('Матчи события:')
            #for title in titles:
            #    if 'Хозяева' in title:
            #        continue
            #    print(title)
            for match in matches:
                print(match)
                total = []
                # Защита от сбоев для гандбола в url
                if 'Handball' not in matches[match]:
                    continue
                if url == 'https://1xstavka.ru/line/Handball/':
                    if match not in self.matches:
                        total = self.get_total(matches[match], driver, None)
                    else:
                        continue
                else:
                    #print(match)
                    # Если этот матч уже отработан то пропускаем
                    if match not in self.matches.keys() or 'Хозяева' in match:
                        continue
                    # Этот параметр указывает на имя предварительного Тотала
                    if self.totals[match]:
                        name = self.totals[match][0]
                        print(total[match])
                        print(f'name = {name}')
                    else:
                        name = None
                    # Коэффициент полученный перед началом
                    line_koeff = self.totals[match][1]
                    total = self.get_total(matches[match], driver, name)
                    try:
                        live_koeff = total[1]
                    except TypeError:
                        print(f'Проблема с получением Тотала {total}')
                        continue
                    event_msg = f'\n{match} \n {total[0]}\n Коэффициент перед матчем {line_koeff}\n ' \
                                f'Текущий коэффициент {live_koeff}'
                    print(f'Предварительное сообщение {event_msg}')
                    if live_koeff >= line_koeff + difference and live_koeff > 1.3:
                        print('ALLAY')
                        self.clean(match)
                        event_msg = f'{match} \n {total[0]}\n Коэффициент перед матчем{line_koeff}\n ' \
                                    f'Текущий коэффициент {live_koeff}'
                        print(event_msg)
                        telega.telegram_bot_send_text(event_msg)
        self.save_matches(url, temp_matches)
        '''

    def itog(self, url, line_matches, live_matches):
        if url == 'https://1xstavka.ru/line/Handball/':
            self.line_matches = line_matches
            print(f' self.line = {self.live_matches}')
            print(f'Количество ожидаемых матчей {len(line_matches)}')
        else:
            self.live_matches = live_matches
            self.save_matches()
            print(f'Количество идущих матчей {len(live_matches)}')
        print(self.totals)


    def bet_start(self, teams, koeff, diff):
        if teams in self.totals:
            pre_bet = self.totals[teams]
            print(f'Ставка до игры = {pre_bet} ставка сейчас {koeff}')
            if pre_bet + diff <= koeff or pre_bet - diff >= koeff:
                return True
            else:
                return None

    def save_matches(self):
        old_matches = []
        print(self.line_matches, '\n', self.line_matches)
        for match in self.totals:
            print(match)
            if match in self.live_matches or match in self.live_matches:
                continue
            else:
                old_matches += match
        print(f'\nЭти матчи уже прошли {old_matches}')
        for match in old_matches:
            print(f'Удален из хранилища {self.totals.pop(match)}')
        print(f'количество матчей {len(self.totals)}\n self.matches = {self.totals}')

    def clean(self, match):
        self.matches.pop(match)
        self.totals.pop(match)

    def get_total(self, driver, name):
        totals = {}
        games = driver.find_elements_by_class_name('c-events__item_game')  # c-bets__bet_sm static-event num
        for game in games:
            head = game.find_element_by_class_name('c-events__teams')
            teams = head.get_attribute('title')
            bets = game.find_element_by_class_name('c-bets').text.split()
            total = bets[7]
            if total != '-':
                try:
                    koeff = float(bets[8].strip())
                except ValueError:
                    print(f'Не могу получить значение {bets[8]}')
                    continue
                print(f'{teams}')
                print(f'{total}  =  {koeff}')
                total = {teams: koeff}
                totals.update(total)
        return totals

    '''
    def get_total(self, url, driver, name):
        total = []
        driver.get(url)
        all_groups = driver.find_elements_by_class_name('bet_group')
        # Перебираем все группы ставок
        for group in all_groups:
            try:
                # Находим группу Тотал
                target_area = group.find_element_by_class_name('bet-title')
                bet = target_area.text
                if bet == "Тотал":
                    total_group = group
                    break
            except:
                continue
        try:
            bet_types = total_group.find_elements_by_class_name('bet_type')
            bet_koeffs = total_group.find_elements_by_class_name('koeff')
            types = [bet_type.text for bet_type in bet_types]
            koefs = [float(bet_koeff.text) for bet_koeff in bet_koeffs]
            if not name:
                index = self.find_bet(koefs)
                print(f'Total = {types[index]}  koeff = {koefs[index]}')
            else:
                print(url)
                print(f'types = {types}\n koefs = {koefs}')
                try:
                    index = types.index(name)
                except:
                    # Если не нашли такого же тотала, то ищем снова наиболее ровный
                    index = self.find_bet(koefs)
                print(f'Index = {index}\n Total = {types[index]}  koeff = {koefs[index]}')
            total = [types[index], koefs[index]]
        except:

            return None

        return total
    '''

    def find_bet(self, koefs):
        index = 0
        min_difference = abs(koefs[0] - koefs[1])
        for i in range(2, len(koefs), 2):
            difference = abs(koefs[i] - koefs[i + 1])
            if difference <= min_difference:
                min_difference = difference
                index = i
        return index + 1

    def get_liga(self, driver):
        events = {}
        sleep(5)
        sports = driver.find_elements_by_class_name('link--labled')
        for sport in sports:
            event = sport.text.split('\n')[0]
            if 'Женщины' in event:
                continue
            link = sport.get_attribute('href')
            events[event] = link
            # print(event, link)
        return events


def main():
    counter = 1
    x_bot = Bot()
    main_url = 'https://1xstavka.ru/line/Handball/'
    live_url = 'https://1xstavka.ru/live/Handball/'
    t = 3600
    while True:
        print(f'counter = {counter}')
        if t % 3600 == 0:
            print('LINE')
            x_bot.navigate(main_url)
        print('LIVE')
        x_bot.navigate(live_url)
        counter += 1
        sleep(300)
        print('#####################################')
        t += 60


if __name__ == '__main__':
    main()

# https://1xstavka.ru/line/Handball
