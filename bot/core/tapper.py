import asyncio
import random
from datetime import datetime
from random import randint
from time import time
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

from bot.config import settings
from bot.exceptions import InvalidSession
from bot.utils import logger
from .headers import headers


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            bot = await self.tg_client.resolve_peer('theYescoin_bot')
            app = InputBotAppShortName(bot_id=bot, short_name="Yescoin")
            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=bot,
                app=app,
                platform='android',
                write_allowed=True,
                start_param=settings.REF_ID
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str) -> tuple[dict[str], str]:
        try:
            response = await http_client.post(url='https://api-backend.yescoin.gold/user/login',
                                              json={"code": tg_web_data})
            response.raise_for_status()

            response_json = await response.json()
            access_token = response_json['data']['token']

            return access_token
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/account/getAccountInfo')
            response.raise_for_status()

            response_json = await response.json()
            profile_data = response_json['data']

            return profile_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def get_game_data(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/game/getGameInfo')
            response.raise_for_status()

            response_json = await response.json()
            game_data = response_json['data']

            return game_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Game Data: {error}")
            await asyncio.sleep(delay=3)

    async def get_boosts_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/build/getAccountBuildInfo')
            response.raise_for_status()

            response_json = await response.json()
            boosts_info = response_json['data']

            return boosts_info
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Boosts Info: {error}")
            await asyncio.sleep(delay=3)

    async def get_special_box_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/game/getSpecialBoxInfo')
            response.raise_for_status()

            response_json = await response.json()
            special_box_info = response_json['data']

            return special_box_info
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Special Box Info: {error}")
            await asyncio.sleep(delay=3)

    async def level_up(self, http_client: aiohttp.ClientSession, boost_id: int) -> bool:
        try:
            response = await http_client.post(url='https://api-backend.yescoin.gold/build/levelUp', json=boost_id)
            response.raise_for_status()

            response_json = await response.json()

            return response_json['data']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply {boost_id} Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_turbo_boost(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://api-backend.yescoin.gold/game/recoverSpecialBox')
            response.raise_for_status()

            response_json = await response.json()

            return response_json['data']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Turbo Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_energy_boost(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://api-backend.yescoin.gold/game/recoverCoinPool')
            response.raise_for_status()

            response_json = await response.json()

            return response_json['data']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Energy Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def send_taps(self, http_client: aiohttp.ClientSession, taps: int) -> bool:
        try:
            response = await http_client.post(url='https://api-backend.yescoin.gold/game/collectCoin', json=taps)
            response.raise_for_status()

            response_json = await response.json()

            if not response_json['data']:
                return False

            status = response_json['data']['collectStatus']

            return status
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def send_taps_with_turbo(self, http_client: aiohttp.ClientSession) -> bool:
        try:
            special_box_info = await self.get_special_box_info(http_client=http_client)
            box_type = special_box_info['recoveryBox']['boxType']
            taps = special_box_info['recoveryBox']['specialBoxTotalCount']

            await asyncio.sleep(delay=10)

            response = await http_client.post(url='https://api-backend.yescoin.gold/game/collectSpecialBoxCoin',
                                              json={'boxType': box_type, 'coinCount': taps})
            response.raise_for_status()

            response_json = await response.json()

            if not response_json['data']:
                return False

            status = response_json['data']['collectStatus']

            return status
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def main_page(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/task/mainPage')
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success':
                if response_json['data']['dailyTaskTodoCount'] > 0:
                    await self.daily_task(http_client=http_client)
                    #每日任务完成之后点击领取奖励
                    await self.claimBonus(http_client=http_client)
                else:
                    logger.info(f"{self.session_name} | Daily Task Success")
        except Exception as error:
            logger.error(f"{self.session_name} | Main Page Error: {error}")

    async def daily_task(self, http_client: aiohttp.ClientSession):
        try:
            await asyncio.sleep(delay=5)
            response = await http_client.get(url='https://api-backend.yescoin.gold/mission/getDailyMission')
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success':
                data = response_json['data']
                for task in data:
                    if task['name'] == u'Claim Offline reward 1 time' or task['name'] == u'Daily Check-in':
                        continue
                    if task['link'] == u'CheckIn':
                        await self.daily_check_in(http_client=http_client, task=task)
                    if task['missionStatus'] == 0 and task['checkStatus'] == 0:
                        await self.click_daily_mission(http_client=http_client, task=task)
                    if task['checkStatus'] == 2 and task['missionStatus'] == 0:
                        await self.check_daily_mission(http_client=http_client, task=task)
                    if task['checkStatus'] == 1 and task['missionStatus'] == 0:
                        await self.claim_reward(http_client=http_client, task=task)
        except Exception as error:
            logger.error(f"{self.session_name} | Daily Task Error: {error}")

    async def claimBonus(self, http_client):
        try:
            response = await http_client.get(url=f'https://api-backend.yescoin.gold/task/getFinishTaskBonusInfo')
            response.raise_for_status()
            response_json = await response.json()
            dailyTaskFinishCount = response_json.get('data')['dailyTaskTotalCount']
            dailyTaskTotalCount = response_json.get('data')['dailyTaskFinishCount']
            if dailyTaskTotalCount == dailyTaskFinishCount:
                # 开始点击奖励
                await http_client.post(url=f'https://api-backend.yescoin.gold/task/claimBonus')
        except Exception as error:
            logger.error(f"{self.session_name} | claimBonus Error: {error}")

    async def daily_check_in(self, http_client: aiohttp.ClientSession, task: dict):
        try:
            if task['checkStatus'] == 2:
                await asyncio.sleep(delay=5)
                response = await http_client.get(url='https://api-backend.yescoin.gold/signIn/list')
                response.raise_for_status()
                response_json = await response.json()
                if response_json['message'] == u'Success':
                    data = response_json['data']
                    for task in data:
                        if task['status'] == 1 and task['checkIn'] == 0:
                            json_data = {}
                            tm = int(time())
                            if self.friendly_address is not None:
                                json_data = {"id": task['id'], "createAt": tm, "signInType": 1,
                                             "destination": self.friendly_address}
                            else:
                                logger.warning(f"{self.session_name} | 请绑定钱包地址")
                                json_data = {"id": task['id'], "createAt": tm, "signInType": 1, "destination": ""}
                            await asyncio.sleep(delay=5)
                            http_client.headers['tm'] = tm
                            http_client.headers['sign'] = '0cd8d99e09fc6d1e423eff26ab414070'
                            response = await http_client.post(url='https://api-backend.yescoin.gold/signIn/claim',
                                                              json=json_data)
                            response.raise_for_status()
                            response_json = await response.json()
                            if response_json['message'] == u'Success':
                                logger.success(
                                    f"{self.session_name} | Daily Check-In: {response_json['data']['reward']}")
                            else:
                                logger.error(f"{self.session_name} | Daily Check-In Error: {response_json['message']}")
        except Exception as error:
            logger.error(f"{self.session_name} | Daily Check In Error: {error}")

    async def click_daily_mission(self, http_client: aiohttp.ClientSession, task: dict):
        try:
            await asyncio.sleep(delay=5)
            response = await http_client.post(url='https://api-backend.yescoin.gold/mission/clickDailyMission',
                                              json=task['missionId'])
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success':
                logger.success(f"{self.session_name} | Click Daily Mission Success: {task['des']}")
                # await self.check_daily_mission(http_client=http_client, task=task)
        except Exception as error:
            logger.error(f"{self.session_name} | Click Daily Mission Error: {error}")

    async def check_daily_mission(self, http_client: aiohttp.ClientSession, task: dict):
        try:
            await asyncio.sleep(delay=5)
            response = await http_client.post(url='https://api-backend.yescoin.gold/mission/checkDailyMission',
                                              json=task['missionId'])
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success':
                # await self.claim_reward(http_client=http_client, task=task)
                logger.success(f"{self.session_name} | Check Daily Success: {task['des']}")
            else:
                logger.warning(f"{self.session_name} | {response_json['message']}")
        except Exception as error:
            logger.error(f"{self.session_name} | Check Daily Mission Error: {error}")

    async def claim_reward(self, http_client: aiohttp.ClientSession, task: dict):
        try:
            await asyncio.sleep(delay=5)
            response = await http_client.post(url='https://api-backend.yescoin.gold/mission/claimReward',
                                              json=task['missionId'])
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success':
                logger.success(
                    f"{self.session_name} | Claim Reward Success: {task['des']} | reward: {response_json['data']['reward']}")
        except Exception as error:
            logger.error(f"{self.session_name} | Check Daily Mission Error: {error}")

    async def get_wallet(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/wallet/getWallet')
            response.raise_for_status()
            response_json = await response.json()
            if response_json['message'] == u'Success' and len(response_json['data']):
                logger.info(f"{self.session_name}  | 钱包地址：{response_json['data'][0]['friendlyAddress']}")
                return response_json['data'][0]['friendlyAddress']
        except Exception as error:
            logger.error(f"{self.session_name} | Get Wallet Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        active_turbo = False

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                try:
                    if time() - access_token_created_time >= 3600:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        access_token = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                        http_client.headers["Token"] = access_token
                        headers["Token"] = access_token

                        access_token_created_time = time()

                        profile_data = await self.get_profile_data(http_client=http_client)
                        balance = profile_data['currentAmount']
                        rank = profile_data['rank']
                        level = profile_data['userLevel']
                        invite_amount = profile_data['inviteAmount']

                        logger.info(f"{self.session_name} | Rank: <m>{rank}</m> | Level: <r>{level}</r> | "
                                    f"Invite amount: <y>{invite_amount}</y>")

                        self.friendly_address = await self.get_wallet(http_client=http_client)
                    await self.main_page(http_client=http_client)
                    try:
                        # 做任务1
                        # await self.doTask(http_client=http_client)
                        # 做任务2
                        await self.doNewTask(http_client=http_client)
                        # 做任务3
                        await self.doNewTask1(http_client=http_client)
                        # 签到
                        # await self.sign(http_client=http_client)
                    except InvalidSession as error:
                        logger.info(f"{self.session_name} | 做任务出现异常!")
                    taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                    game_data = await self.get_game_data(http_client=http_client)

                    available_energy = game_data['coinPoolLeftCount']
                    coins_by_tap = game_data['singleCoinValue']

                    if active_turbo:
                        # taps += settings.ADD_TAPS_ON_TURBO
                        status = await self.send_taps_with_turbo(http_client=http_client)
                    else:
                        if taps * coins_by_tap >= available_energy:
                            taps = abs(available_energy // 10 - 1)

                        status = await self.send_taps(http_client=http_client, taps=taps)

                    profile_data = await self.get_profile_data(http_client=http_client)

                    if not profile_data or not status:
                        continue

                    new_balance = profile_data['currentAmount']
                    calc_taps = new_balance - balance
                    balance = new_balance
                    total = profile_data['totalAmount']

                    logger.success(f"{self.session_name} | Successful tapped! | "
                                   f"Balance: <c>{balance}</c> (<g>+{calc_taps}</g>) | Total: <e>{total}</e>")

                    boosts_info = await self.get_boosts_info(http_client=http_client)

                    turbo_boost_count = boosts_info['specialBoxLeftRecoveryCount']
                    energy_boost_count = boosts_info['coinPoolLeftRecoveryCount']

                    next_tap_level = boosts_info['singleCoinLevel'] + 1
                    next_energy_level = boosts_info['coinPoolTotalLevel'] + 1
                    next_charge_level = boosts_info['coinPoolRecoveryLevel'] + 1

                    next_tap_price = boosts_info['singleCoinUpgradeCost']
                    next_energy_price = boosts_info['coinPoolTotalUpgradeCost']
                    next_charge_price = boosts_info['coinPoolRecoveryUpgradeCost']

                    if active_turbo is False:
                        if (energy_boost_count > 0
                                and available_energy < settings.MIN_AVAILABLE_ENERGY
                                and settings.APPLY_DAILY_ENERGY is True):
                            logger.info(f"{self.session_name} | Sleep 5s before activating the daily energy boost")
                            await asyncio.sleep(delay=5)

                            status = await self.apply_energy_boost(http_client=http_client)
                            if status is True:
                                logger.success(f"{self.session_name} | Energy boost applied")

                                await asyncio.sleep(delay=1)

                            continue

                        if turbo_boost_count > 0 and settings.APPLY_DAILY_TURBO is True:
                            logger.info(f"{self.session_name} | Sleep 5s before activating the daily turbo boost")
                            await asyncio.sleep(delay=5)

                            status = await self.apply_turbo_boost(http_client=http_client)
                            if status is True:
                                logger.success(f"{self.session_name} | Turbo boost applied")

                                await asyncio.sleep(delay=1)

                                active_turbo = True
                                turbo_time = time()

                            continue

                        if (settings.AUTO_UPGRADE_TAP is True
                                and balance > next_tap_price
                                and next_tap_level <= settings.MAX_TAP_LEVEL):
                            logger.info(f"{self.session_name} | Sleep 5s before upgrade tap to {next_tap_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.level_up(http_client=http_client, boost_id=1)
                            if status is True:
                                logger.success(f"{self.session_name} | Tap upgraded to {next_tap_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue

                        if (settings.AUTO_UPGRADE_ENERGY is True
                                and balance > next_energy_price
                                and next_energy_level <= settings.MAX_ENERGY_LEVEL):
                            logger.info(
                                f"{self.session_name} | Sleep 5s before upgrade energy to {next_energy_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.level_up(http_client=http_client, boost_id=3)
                            if status is True:
                                logger.success(f"{self.session_name} | Energy upgraded to {next_energy_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue
                        if (settings.AUTO_UPGRADE_CHARGE is True
                                and balance > next_charge_price
                                and next_charge_level <= settings.MAX_CHARGE_LEVEL):
                            logger.info(
                                f"{self.session_name} | Sleep 5s before upgrade charge to {next_charge_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.level_up(http_client=http_client, boost_id=2)
                            if status is True:
                                logger.success(f"{self.session_name} | Charge upgraded to {next_charge_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue
                        if available_energy < settings.MIN_AVAILABLE_ENERGY:
                            logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                            logger.info(f"{self.session_name} | Sleep {settings.SLEEP_BY_MIN_ENERGY}s")

                            await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)

                            continue
                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    if active_turbo is True:
                        active_turbo = False

                    logger.info(f"Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)

    async def doTask(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-backend.yescoin.gold/mission/getDailyMission')
            response.raise_for_status()
            response_json = await response.json()
            taskList = response_json['data']
            for ts in taskList:
                if ts['missionStatus'] == 0 and ts['checkStatus'] == 0:
                    # start
                    response = await http_client.post(
                        url='https://api-backend.yescoin.gold/mission/clickDailyMission',
                        json=ts['missionId'])
                    response.raise_for_status()
                    response_json = await response.json()
                    if response_json['data'] is True:
                        response = await http_client.post(
                            url='https://api-backend.yescoin.gold/mission/checkDailyMission',
                            json=ts['missionId'])
                        response.raise_for_status()
                        response_json = await response.json()
                        if response_json['data'] is True:
                            try:
                                response = await http_client.post(
                                    url='https://api-backend.yescoin.gold/mission/claimReward',
                                    json=ts['missionId'])
                                response.raise_for_status()
                                response_json = await response.json()
                                if response_json['data'] is True:
                                    logger.info(f"{ts['name']}任务完成!")
                            except Exception as error:
                                await asyncio.sleep(delay=3)
                elif ts['missionStatus'] == 0 and ts['checkStatus'] == 1:
                    try:
                        response = await http_client.post(
                            url='https://api-backend.yescoin.gold/mission/claimReward',
                            json=ts['missionId'])
                        response.raise_for_status()
                        response_json = await response.json()
                        if response_json['data'] is True:
                            logger.info(f"{ts['name']}任务完成!")
                    except Exception as error:
                        await asyncio.sleep(delay=3)
        except Exception as error:
            await asyncio.sleep(delay=3)

            return False

    async def sign(self, http_client):
        response = await http_client.get(url='https://api-backend.yescoin.gold/mission/getDailyMission')
        response.raise_for_status()
        response_json = await response.json()
        taskList = response_json['data']
        for ts in taskList:
            if ts['link'] == 'CheckIn' and ts['missionStatus'] == 0:
                response = await http_client.get(url='https://api-backend.yescoin.gold/signIn/list')
                response.raise_for_status()
                response_json = await response.json()
                signList = response_json['data']
                for sl in signList:
                    if sl['checkIn'] == 0:
                        signParam = {
                            "id": f"{sl['id']}",
                            "createAt": int(time()),
                            "signInType":1,
                            "destination": ""
                        }
                        response = await http_client.post(
                            url='https://api-backend.yescoin.gold/signIn/claim',
                            json=signParam)
                        response.raise_for_status()
                        response_json = await response.json()
                        if response_json['data']['status'] is True:
                            logger.info(f"{self.session_name} | 签到成功!")

    async def doNewTask(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(url='https://api-backend.yescoin.gold/task/getTaskList')
        response.raise_for_status()
        response_json = await response.json()
        taskList = response_json['data']['taskList']
        for ts in taskList:
            if ts['taskStatus'] == 0:
                random_delay = random.randint(1, 3)
                logger.info(
                    f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                await asyncio.sleep(delay=random_delay)
                # start
                response = await http_client.post(
                    url='https://api-backend.yescoin.gold/task/clickTask',
                    json=ts['taskId'])
                response.raise_for_status()
                response_json = await response.json()
                if response_json['data'] is True:
                    random_delay = random.randint(1, 3)
                    logger.info(
                        f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                    await asyncio.sleep(delay=random_delay)
                    response = await http_client.post(
                        url='https://api-backend.yescoin.gold/task/checkTask',
                        json=ts['taskId'])
                    response.raise_for_status()
                    response_json = await response.json()
                    if response_json['data'] is True:
                        random_delay = random.randint(1, 3)
                        logger.info(
                            f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                        await asyncio.sleep(delay=random_delay)
                        try:
                            response = await http_client.post(
                                url='https://api-backend.yescoin.gold/task/claimTaskReward',
                                json=ts['taskId'])
                            response.raise_for_status()
                            response_json = await response.json()
                            if response_json['code'] == 0:
                                logger.info(f"{ts['taskDescription']}任务完成!")
                        except Exception as error:
                            await asyncio.sleep(delay=3)

    async def doNewTask1(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(url='https://api-backend.yescoin.gold/task/getTaskList')
        response.raise_for_status()
        response_json = await response.json()
        taskList = response_json['data']['specialTaskList']
        for ts in taskList:
            if ts['taskStatus'] == 0:
                random_delay = random.randint(1, 3)
                logger.info(
                    f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                await asyncio.sleep(delay=random_delay)
                # start
                response = await http_client.post(
                    url='https://api-backend.yescoin.gold/task/clickTask',
                    json=ts['taskId'])
                response.raise_for_status()
                response_json = await response.json()
                if response_json['data'] is True:
                    random_delay = random.randint(1, 3)
                    logger.info(
                        f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                    await asyncio.sleep(delay=random_delay)
                    response = await http_client.post(
                        url='https://api-backend.yescoin.gold/task/checkTask',
                        json=ts['taskId'])
                    response.raise_for_status()
                    response_json = await response.json()
                    if response_json['data'] is True:
                        random_delay = random.randint(1, 3)
                        logger.info(
                            f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
                        await asyncio.sleep(delay=random_delay)
                        try:
                            response = await http_client.post(
                                url='https://api-backend.yescoin.gold/task/claimTaskReward',
                                json=ts['taskId'])
                            response.raise_for_status()
                            response_json = await response.json()
                            if response_json['code'] == 0:
                                logger.info(f"{ts['taskDescription']}任务完成!")
                        except Exception as error:
                            await asyncio.sleep(delay=3)

    async def yaoqing(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(
            url=f'https://api-backend.yescoin.gold/invite/getInviteGiftBoxInfoWithCode?inviteCode={settings.REF_ID}')
        response.raise_for_status()
        response_json = await response.json()
        if response_json['code'] == 0:
            ivResponse = await http_client.post(
                url=f'https://api-backend.yescoin.gold/invite/claimGiftBox?packId={settings.REF_ID}')
            ivResponse.raise_for_status()
            ivResponse_json = await ivResponse.json()
            logger.info(f"邀请完成!{ivResponse_json['data']['claimAmount']}")


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
