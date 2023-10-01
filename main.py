import nextcord
import requests
from nextcord.ext import commands, application_checks
from nextcord import Colour
import os
from dotenv import load_dotenv
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
channel = os.getenv('CHANNEL')
telegram_token = os.getenv('TELEGRAM_TOKEN')
print(discord_token)
admins_str = os.getenv("ADMINS")
admins = tuple(admins_str.split(','))
print(admins)
print(admins_str)

bot = commands.Bot()

notifications_enabled = False

selected_channel_ids = []


def is_allowed():
    def predicate(interaction: nextcord.Interaction):
        if str(interaction.user.id) in admins:
            return True
        else:
            raise nextcord.errors.ApplicationCheckFailure("Доступ запрещен")
    return application_checks.check(predicate)


def send_info_to_telegram(message):
    url = "https://api.telegram.org/bot"
    url += telegram_token
    method = url + "/sendMessage"

    requests.post(method, data={
        "chat_id": channel,
        "text": {message},
        "parse_mode": 'html',
        "disable_web_page_preview": True
    })

    logger.info(message)


@bot.event
async def on_ready():
    logger.info('I am running...')


@bot.event
async def on_voice_state_update(member, before, after):
    if notifications_enabled:
        if after.channel and after.channel != before.channel:
            if str(after.channel.id) in selected_channel_ids:
                message = (
                    f'Пользователь {member.name} подключился к голосовому каналу <a href="https://discord.com/channels/'
                    f'{member.guild.id}/{after.channel.id}">{after.channel.name}</a>'
                )
                send_info_to_telegram(message)


@bot.slash_command(description="Включение отслеживания подключений")
@is_allowed()
@application_checks.guild_only()
async def on(interaction: nextcord.Interaction):
    global notifications_enabled
    if not notifications_enabled:
        notifications_enabled = True
        await interaction.response.send_message(':white_check_mark: Уведомления о подключении включены',
                                                ephemeral=True)
    else:
        await interaction.response.send_message(':warning: Уведомления о подключении уже включены', ephemeral=True)


@bot.slash_command(description="Выключение отслеживания подключений")
@is_allowed()
@application_checks.guild_only()
async def off(interaction: nextcord.Interaction):
    global notifications_enabled
    if notifications_enabled:
        notifications_enabled = False
        await interaction.response.send_message(':white_check_mark: Уведомления о подключении выключены',
                                                ephemeral=True)
    else:
        await interaction.response.send_message(':warning: Уведомления о подключении уже выключены', ephemeral=True)


@bot.slash_command(description="Статус отслеживания подключений")
@is_allowed()
@application_checks.guild_only()
async def status(interaction: nextcord.Interaction):
    global notifications_enabled
    if notifications_enabled:
        await interaction.response.send_message(':white_check_mark: Отслеживание включено', ephemeral=True)
    else:
        await interaction.response.send_message(':x: Отслеживание выключено', ephemeral=True)


@bot.slash_command(description="Список отслеживаемых каналов")
@is_allowed()
@application_checks.guild_only()
async def list(interaction: nextcord.Interaction):
    global selected_channel_ids
    guild = interaction.guild

    channel_info = []

    if not selected_channel_ids:
        await interaction.response.send_message(':wastebasket: Список отслеживаемых каналов пуст', ephemeral=True)
    else:
        for channel_id in selected_channel_ids:
            channel_name = guild.get_channel(int(channel_id))
            if channel_name:
                channel_info.append(f"{channel_name.name} (id: {channel_id})")

        message = "\n".join(channel_info)
        await interaction.response.send_message(f'Список отслеживаемых каналов:\n{message}', ephemeral=True)


@bot.slash_command(description="Добавление канала в список отслеживания")
@is_allowed()
@application_checks.guild_only()
async def add(interaction: nextcord.Interaction, channel_id):
    global selected_channel_ids
    guild = interaction.guild
    channel_ids = [channel_info.id for channel_info in guild.channels]
    if int(channel_id) in channel_ids:
        if channel_id not in selected_channel_ids:
            selected_channel_ids.append(channel_id)
            await interaction.response.send_message(f':white_check_mark: Канал с id {channel_id}'
                                                    f' успешно добавлен в список отслеживания', ephemeral=True)
        else:
            await interaction.response.send_message(f':warning: Канал c id {channel_id}'
                                                    f' уже добавлен в список отслеживания', ephemeral=True)
    else:
        await interaction.response.send_message(f':no_entry_sign: Канал id {channel_id} отсутствует на сервере',
                                                ephemeral=True)


@bot.slash_command(description="Удаление канала из списка отслеживания")
@is_allowed()
@application_checks.guild_only()
async def remove(interaction: nextcord.Interaction, channel_id):
    global selected_channel_ids
    if channel_id in selected_channel_ids:
        selected_channel_ids.remove(channel_id)
        await interaction.response.send_message(f':white_check_mark: Канал с id {channel_id}'
                                                f' успешно удален из списка отслеживания', ephemeral=True)
    else:
        await interaction.response.send_message(f':no_entry_sign: Канал с id {channel_id}'
                                                f' отсутствует в списке отслеживания', ephemeral=True)


@bot.slash_command(description="Удаление всех каналов из списка отслеживания")
@is_allowed()
@application_checks.guild_only()
async def clear(interaction: nextcord.Interaction):
    global selected_channel_ids
    if not selected_channel_ids:
        await interaction.response.send_message(':warning: Список отслеживаемых каналов пуст', ephemeral=True)
    else:
        selected_channel_ids = []
        await interaction.response.send_message(':white_check_mark: Список отслеживаемых каналов успешно очищен',
                                                ephemeral=True)


@bot.slash_command(description="Список доступных команд")
@is_allowed()
@application_checks.guild_only()
async def info(interaction: nextcord.Interaction):
    try:
        embed = nextcord.Embed(title="Список доступных команд", colour=Colour.blue())
        embed.set_author(name="Scout Service",
                         icon_url="https://pin.ski/3rBbkJR")
        embed.set_thumbnail(url="https://pin.ski/3rBbkJR")
        embed.add_field(name="Включение отслеживания подключений:",
                        value="/on\n", inline=False)
        embed.add_field(name="Выключение отслеживания подключений:",
                        value="/off\n", inline=False)
        embed.add_field(name="Статус отслеживания подключений:",
                        value="/status\n", inline=False)
        embed.add_field(name="Список отслеживаемых каналов:",
                        value="/list\n", inline=False)
        embed.add_field(name="Добавление канала в список отслеживания указанием его id:",
                        value="/add [channel_id], например: /add 123456\n", inline=False)
        embed.add_field(name="Удаление канала из списка отслеживания с указанием его id:",
                        value="/remove [channel_id], например: /add 123456\n", inline=False)
        embed.add_field(name="Удаление всех каналов из списка отслеживания:",
                        value="/clear\n", inline=False)
        embed.add_field(name="Список доступных команд:",
                        value="/info\n", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(e)


@on.error
@off.error
@status.error
@list.error
@add.error
@remove.error
@clear.error
@info.error
async def command_error(interaction: nextcord.Interaction, error):
    if isinstance(error, nextcord.errors.ApplicationCheckFailure) and "Доступ запрещен" in str(error):
        await interaction.response.send_message(":no_entry_sign: Доступ запрещен", ephemeral=True)
        user_name = interaction.user.name
        command_used = interaction.data.get('name')
        message = f'Пользователь {user_name} пытался использовать команду /{command_used}'
        send_info_to_telegram(message)
    elif isinstance(error, nextcord.ext.application_checks.errors.ApplicationNoPrivateMessage):
        await interaction.response.send_message(":no_entry_sign: Выполнение команд запрещено в личных сообщениях",
                                                ephemeral=True)
    else:
        logger.info(error)
        await interaction.response.send_message(":no_entry_sign: Неизвестная ошибка", ephemeral=True)


def main():
    bot.run(discord_token)


if __name__ == '__main__':
    main()
