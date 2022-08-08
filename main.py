import os
import time
import requests
import json


class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    # Возвращает информацию о пользователе Вконтакте
    def get_user_info(self):
        URL = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(URL, params={**self.params, **params})
        if response.status_code == 200:
            response_json = response.json()
            return response_json['response'][0]['first_name'] + ' ' + response_json['response'][0]['last_name']
        else:
            return 'Error'

    # Возвращает информацию о фотографиях профиля пользователя
    def get_profile_photo_data(self, count=5):
        URL = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile', 'count': count, 'extended': 1}
        response = requests.get(URL, params={**self.params, **params})
        if response.status_code == 200:
            return response.json()
        else:
            return 'Error'


class YaUploader:
    def __init__(self, token, photo_owner):
        self.URL = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Authorization': f'OAuth {token}'}
        self.backup_directory_name = f"/{photo_owner}_vk_profile_photos/"
        self.replace = True
        response = requests.put(f"{self.URL}?path={self.backup_directory_name}&overwrite="
                                f"{self.replace}", headers=self.headers)

    # Загружает на Яндекс-диск фотографию из переменной content
    def upload(self, content, file_name):
        response = requests.get(f"{self.URL}/upload?path={self.backup_directory_name}{file_name}&overwrite="
                                f"{self.replace}",
                                headers=self.headers)
        if response.status_code == 200:
            try:
                response_json = response.json()
                requests.put(response_json.get("href"), files={'file': content})
                return 'Ok'
            except KeyError:
                return 'Error'
        else:
            return 'Error'


def main():
    if __name__ == '__main__':
        directory = os.getcwd()
        vk_token_file = 'vk.token'
        vk_token_path = os.path.join(directory, vk_token_file)
        with open(vk_token_path) as file:
            vk_token = file.read().strip()
        vk_user_id = input("Введите id пользователя вконтакте: ")
        yandex_token = input("Введите токен для полигона Яндекс-диск: ")
        vk = VK(vk_token, vk_user_id)
        photo_owner = vk.get_user_info()
        if photo_owner == 'Error':
            print("VK user error!")
            return
        uploader = YaUploader(yandex_token, photo_owner)
        photo_data = vk.get_profile_photo_data()
        if photo_data == 'Error':
            print("Photo data error!")
            return
        photo_names_list = []
        photo_info_list = []
        print('Backup started...')
        for item in photo_data['response']['items']:
            likes = item['likes']['count']
            photo_upload_date = item['date']
            photo_name = str(likes)
            if photo_name in photo_names_list:
                photo_name += '_' + str(photo_upload_date)
            photo_names_list.append(photo_name)
            photo_name += '.jpg'
            target_photo = max(item['sizes'], key=lambda s: s['height'])
            photo_url = target_photo['url']
            photo_size = target_photo['type']
            response = requests.get(photo_url)
            result = uploader.upload(response.content, photo_name)
            if result == 'Ok':
                print(f"photo from url {photo_url} ok")
                photo_info_list.append({'file_name': photo_name, 'size': photo_size})
            else:
                print(f"photo from url {photo_url} don't backup!")
            time.sleep(0.3)
        print("\nDone!")
        photo_info_file_path = os.path.join(directory, 'photo_info.json')
        with open(photo_info_file_path, 'w') as file:
            json.dump(photo_info_list, file)


main()
