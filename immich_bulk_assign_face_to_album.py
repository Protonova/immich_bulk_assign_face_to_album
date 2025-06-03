import argparse
import json
import logging
from sys import exit
from time import sleep
from typing import List

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util import Retry

logger = logging.getLogger(__name__)

# TODO: Detangle logic, improve efficiency.
# TODO: Refactor constructor, overly complicated.
# TODO: Breakup logic into testable functions

class BulkAssignFaceToAlbum:
    def __init__(self, server_base_url, api_key, requested_person, requested_album):
        self.album_list = []
        self.person_list = []
        self.found_album = False
        self.found_person = False
        self.base_url = server_base_url
        self.album_id = requested_album
        self.album_name = None
        self.person_id = requested_person
        self.person_name = None
        self.default_headers = {"Accept": "application/json", "Content-Type": "application/json", "x-api-key": api_key}
        self.session = requests.Session()

        # Session Configuration
        retry_strategy = Retry(total=5, backoff_factor=0.2)
        self.session.mount('https://', HTTPAdapter(max_retries=retry_strategy))

        self.validate_person_and_album()
        temp_asset_list = []
        filtered_asset_list = []

        if self.found_album:
            logger.info(f'Validated {self.album_id} as {self.album_name}')

            # Generate list of pictures in album:
            try:
                album_response = self.session.get(url=f"{self.base_url}/api/albums/{self.album_id}", headers=self.default_headers)
                album_response.raise_for_status()
                album_json = album_response.json()

                for asset in tqdm(album_json['assets'][:110], desc="Reviewing Entire Album", position=0, leave=True): # TODO: Remove hard limit on release
                    try:
                        asset_info_response = self.session.get(url=f"{self.base_url}/api/assets/{asset['id']}", headers=self.default_headers)
                        asset_info_response.raise_for_status()
                        asset_json = asset_info_response.json()
                        temp_asset_list.append({'id': asset['id'], 'originalPath': asset['originalPath'], 'deviceAssetId': asset['deviceAssetId'], 'ownerId': asset['ownerId'], 'people': asset_json.get('people', [])})
                        sleep(0.1)  # TODO test if this is necessary
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Failed to fetch asset {asset['id']}: {e}")
                        continue  # Skip this asset and continue
            except requests.exceptions.RequestException as e:
                logger.exception(f"Failed to fetch assets for \"{self.base_url}/api/albums/{self.album_id}\": {e}")

        if self.found_person:
            logger.info(f'Validated {self.person_id} as {self.person_name}')

            # Create new list containing only what needs to be changed
            if self.found_album and self.found_person:
                for asset in temp_asset_list:
                    people_ids = [person['id'] for person in asset.get('people', [])]
                    if self.person_id in people_ids:
                        logger.debug(f"Asset: {asset['id']} already has the target person: {self.person_id}")
                    else:
                        logger.debug(f'Adding Asset: {asset['id']} to the list of actionable assets')
                        filtered_asset_list.append(asset)

                # Load dummy face tagging parameters and post them to immich
                if filtered_asset_list:
                    for asset_image in tqdm(filtered_asset_list, desc="Processing Faces Additions"):
                        payload = json.dumps({
                            "assetId": asset_image['id'],
                            "height": 0,
                            "imageHeight": 0,
                            "imageWidth": 0,
                            "personId": str(self.person_id),
                            "width": 0,
                            "x": 0,
                            "y": 0
                        })
                        try:
                            actionable_assets_response = self.session.post(f"{self.base_url}/api/faces", headers=self.default_headers, timeout=10, data=payload)
                            actionable_assets_response.raise_for_status()
                            logger.debug(f'Added: \"{self.person_id}\" to asset: \"{asset_image['id']}\"')
                            sleep(0.1)  # TODO test if this is necessary
                        except requests.exceptions.RequestException as err:
                            logger.error(f"Failed to modify asset {asset_image['id']}: {err}")
                            continue  # Skip this asset and continue
                else:
                    logger.debug(f"No assets needed modifying, \"{self.person_name}\" was already tagged in all assets")

                logger.info(f'Summary: \"{self.person_name}\" was added to {len(filtered_asset_list)} assets within \"{self.album_name}\"')

    def get_endpoint_data(self, endpoint: str) -> List[dict] | None:
        """
        Go grab either a list of available albums or people.
        :param endpoint: the complete url to query.
        :return: the list (contents) of the requested api.
        """
        results_list = []

        try:
            queried_response = self.session.get(url=endpoint, headers=self.default_headers)
            queried_response.raise_for_status()
            json_data = queried_response.json()

            if '/api/albums' in endpoint: # https://immich.app/docs/api/get-all-albums
                for album in json_data:
                    temp_dict = {}
                    for key in ("albumName", "id"):
                        temp_dict[key] = album[key]
                    results_list.append(temp_dict)
            elif '/api/people' in endpoint: # https://immich.app/docs/api/get-all-people
                for person in json_data['people']:
                    results_list.append({'name': person['name'], 'id': person['id']})
            logger.debug(f'Retrieved data from \"{endpoint}\"')

            return results_list
        except requests.exceptions.RequestException as e:
            logger.exception(f"Failed to fetch assets for \"{endpoint}\": {e}")
            return None

    def validate_person_and_album(self) -> None:
        try:
            # Validate that we have an immich server that is actually working...
            valid_immich_response = self.session.get(url=f'{self.base_url}/api/server/about', headers=self.default_headers)
            valid_immich_response.raise_for_status()

            if valid_immich_response.status_code == 200:
                logger.info(f'Successfully authenticated with {self.base_url}')

                # Retrieve available albums and people
                self.album_list = self.get_endpoint_data(f'{self.base_url}/api/albums')
                self.person_list = self.get_endpoint_data(f'{self.base_url}/api/people')

                # Validate album ID
                for album_entry in self.album_list:
                    if album_entry.get('id') == self.album_id:
                        self.album_name = album_entry['albumName']
                        self.album_id = album_entry['id']
                        self.found_album = True
                        logger.info(f'Found an album with id: \"{self.album_id}\", otherwise known as \"{self.album_name}\"')

                # Validate person ID
                for person_entry in self.person_list:
                    if person_entry.get('id') == self.person_id:
                        self.person_name = person_entry['name']
                        self.person_id = person_entry['id']
                        self.found_person = True
                        logger.info(f'Found a person with id: \"{self.person_id}\", otherwise known as \"{self.person_name}\"')
        except requests.exceptions.HTTPError as err:
            if valid_immich_response.status_code == 401:
                logger.exception(f'Unauthorized connection. Please check your credentials')
            else:
                logger.exception(f'Failed to connect to {self.base_url} and got error: {err}. ({valid_immich_response.status_code})')

def main() -> None:
    parser = argparse.ArgumentParser(prog='Bulk Assign Faces to Albums', usage='%(prog)s [options]')
    parser.add_argument('-u', '--url', '--server', type=str, required=True, help='Your Immich server URL (ie https://immich.domain.com)')
    parser.add_argument('-k', '--key', type=str, required=True, help='Your Immich API Key')
    parser.add_argument('-p', '--person', type=str, required=True, help='ID of the person you want to add')
    parser.add_argument('-a', '--album', type=str, required=True, help='ID of the album you want to add the person to')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s %(levelname)-8s L:%(lineno)-3s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.FileHandler("BulkAssignFaceToAlbum_debug.log"), logging.StreamHandler()]
    )

    logger.info('BAFTA Script Started')
    query_immich = BulkAssignFaceToAlbum(args.url, args.key, args.person, args.album)
    logger.info('BAFTA Script Exiting')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
        logger.info(f'Exiting with return code 1')
        exit(1)