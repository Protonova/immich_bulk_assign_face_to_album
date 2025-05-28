from pprint import pprint
from datetime import date, datetime
from time import sleep
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import requests
import json
import click

# TODO: Cleanup code/comments
# TODO: Fix variable names
# TODO: Properly initialize used variables
# TODO: Add more/proper error handling
# TODO: Add proper logging and print messages (remove click echos and json outputs)
# TODO: Implement sessions across all requests
# TODO: breakup logic into more functions (if needed)
# TODO: Improve logic for efficiency. Like list comprehension and removing duplicate logic

def serialize_json_dates(obj) -> object:
    if isinstance(obj, (date, datetime)):
        return "{}-{}-{}".format(obj.year, obj.strftime('%m'), obj.strftime('%d'))

def add_person_to_album():
    return None

def get_endpoint_data(endpoint, headers):
    results_list = []
    # Retrieve all albums and then people asset lists
    response = requests.get(url=endpoint,headers=headers)
    # pprint(r.text)
    json_data = json.loads(response.text)
    if '/api/albums' in endpoint:
        for album in json_data:
            temp_dict = {}
            for key in ("albumName", "id"):
                temp_dict[key] = album[key]
            results_list.append(temp_dict)
    elif '/api/people' in endpoint:
        for person in json_data['people']:
            results_list.append({'name': person['name'], 'id': person['id']})

    # pprint(album_list)
    return results_list

@click.command()
@click.option("--server", help="Your Immich server URL (ie https://immich.domain.com)", required=True)
@click.option("--key", help="Your Immich API Key", required=True)
@click.option("--person", help="ID of the person you want to add", required=True)
@click.option("--album", help="ID of the album you want to add the person to", required=True)
@click.option("--debug", is_flag=True, help="Enable verbose debug output")
def immich_bulk_assign_face_to_album(server, key, person, album, debug=False):
    # https://immich.app/docs/api/get-all-albums
    headers = {"Accept": "application/json", "Content-Type": "application/json", "x-api-key": key}
    # payload = {}
    # endpoint = f'{server}/api/albums/{album}/assets'
    # /api/albums
    album_list = []
    person_list = []
    asset_list_to_modify = []
    found_album = False
    found_person = False

    try:
        response = requests.get(url=f'{server}/api/server/about',headers=headers)
        response.raise_for_status()
        pprint(response.text)
        if response.status_code == 200:
            click.echo(f'Success | Authenticated with {server}.')

        # Retrieve available albums and people
        album_list = get_endpoint_data(f'{server}/api/albums', headers)
        # pprint(album_list)
        person_list = get_endpoint_data(f'{server}/api/people', headers)
        # pprint(person_list)

        # Validate that your request is valid
        # any(d.get('albumName') == album_name for d in list_of_dicts)
        # exists = any(d.get('albumName') == album for d in album_list)
        # pprint(album)
        # Validate album
        for album_entry in album_list:
            # print(album_entry)
            if album_entry.get('id') == album:
                # print(album_entry)
                album_name = album_entry['albumName']
                album_id = album_entry['id']
                found_album = True
                click.echo(f'Debug | Found an album with id: \"{album}\", it is associated with: \"{album_name}\".')
                # pprint([album_name,album_id])
        # Validate person
        for person_entry in person_list:
            if person_entry.get('id') == person:
                person_name = person_entry['name']
                person_id = person_entry['id']
                found_person = True
                click.echo(f'Debug | Found a person with id: \"{person}\", it is associated with: \"{person_name}\".')

        # Generate list of pictures in album:
        response = requests.request("GET", f"{server}/api/albums/{album}", headers=headers)
        json_data = json.loads(response.text)

        # with open('album_data.json', 'w') as f:
        #     json.dump(json_data, f, indent=2)
        # pprint(json_data)
        count = 0
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.2)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        for i,asset in enumerate(json_data['assets']):
            if i >= 50:
                break
            # count = count + 1
            # asset_list.append({'id': asset['id'], 'originalPath': asset['originalPath']})

            # response2 = requests.request("GET", f"{server}/api/assets/{asset['id']}", headers=headers)
            try:
                response2 = session.get(f"{server}/api/assets/{asset['id']}", headers=headers, timeout=10)
                response2.raise_for_status()
                json_data2 = json.loads(response2.text)
                # print(asset['id'], len(asset.get('people', [])))  # See which assets have people
                # pprint(json_data2.get('people', []))
                # asset_list.append({'id': asset['id'], 'originalPath': asset['originalPath'], 'deviceAssetId': asset['deviceAssetId'], 'ownerId': asset['ownerId'], 'people': json_data2.get('people', [])})
                # pprint({'id': asset['id'], 'originalPath': asset['originalPath'], 'deviceAssetId': asset['deviceAssetId'], 'ownerId': asset['ownerId'], 'people': json_data2.get('people', [])})
                asset_list_to_modify.append({'id': asset['id'], 'originalPath': asset['originalPath'], 'deviceAssetId': asset['deviceAssetId'], 'ownerId': asset['ownerId'], 'people': json_data2.get('people', [])})
                sleep(0.1)
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch asset {asset['id']}: {e}")
                continue  # Skip this asset and continue



            # if count == 3:
            #     with open('./test.json', encoding='utf-8', mode='w') as f:
            #         f.write(json.dumps(asset_list, default=serialize_json_dates))
            #     exit(0)

        # with open('test.json', 'w') as f:
        #     json.dump(asset_list_to_modify, f, indent=2)

        # New logic
        # personId == people['id']
        # curl -L 'https://photos.local.noveria.uk/api/faces' \
        # -H 'Content-Type: application/json' \
        # -H 'x-api-key: xxxxxxxxx' \
        # -d '{
        #   "assetId": "xxxxxxxxxxxxxx",
        #   "height": 0,
        #   "imageHeight": 0,
        #   "imageWidth": 0,
        #   "personId": "xxxxxxxxxxxxxx",
        #   "width": 0,
        #   "x": 0,
        #   "y": 0
        # }'
        filtered_assets = []
        if found_album and found_person == True:
            # for asset in asset_list_to_modify:
            #     has_target_person = any(person['id'] == person for person in asset.get('people', [])) # This part didn't work as expected...
            #
            #     # Add to filtered list if target person is NOT found
            #     if not has_target_person:
            #         filtered_assets.append(asset)

            # Create new list containing only what needs to be changed
            for asset in asset_list_to_modify:
                people_ids = [person['id'] for person in asset.get('people', [])]
                # click.echo(f"Debug | Asset people IDs: {people_ids}")

                has_target_person = person in people_ids
                # click.echo(f"Debug | Has target person: {has_target_person}")

                if not has_target_person:
                    filtered_assets.append(asset)
                    # click.echo(f"Debug | Added to filtered list")
                else:
                    click.echo(f"Debug | Skipped {asset['id']} - contains target person")

            for asset_image in filtered_assets:
                payload = json.dumps({
                    "assetId": asset_image['id'],
                    "height": 0,
                    "imageHeight": 0,
                    "imageWidth": 0,
                    "personId": str(person),
                    "width": 0,
                    "x": 0,
                    "y": 0
                })
                try:
                    r = session.post(f"{server}/api/faces", headers=headers, timeout=10, data=payload)
                    r.raise_for_status()
                    click.echo(f'Debug | Added person: \"{person}\" to asset: \"{asset_image['id']}\"')
                    sleep(0.1)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to modify asset {asset_image['id']}: {e}")
                    continue  # Skip this asset and continue

        with open('filtered_assets.json', 'w') as f:
            json.dump(filtered_assets, f, indent=2)

        # with open('./test.json', encoding='utf-8', mode='w') as f:
        #     f.write(json.dumps(asset_list, default=serialize_json_dates))
    except requests.exceptions.HTTPError as err:
        if response.status_code == 401:
            click.echo(f'Error | Unauthorized connection. Please check your credentials.')
        else:
            click.echo(f'Error | Failed to connect to {server} and got error: {err}. (Status code: {response.status_code})')



# Connect to API in try catch
# Check if key is valid
# Check if album is valid (get all albums)
# Check if person is valid (get all persons)
# Determine unique assets in the list and ones without the person you want to add
# Get all assets in the album and Loop through all assets then add person to asset

if __name__ == '__main__':
    immich_bulk_assign_face_to_album()