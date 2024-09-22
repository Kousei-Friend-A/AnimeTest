from json import loads as jloads
from aiohttp import ClientSession
from bot import Var, bot, ffQueue
from bot.core.text_utils import TextEditor
from bot.core.reporter import rep

async def upcoming_animes():
    if Var.SEND_SCHEDULE:
        try:
            async with ClientSession() as ses:
                res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
                aniContent = jloads(await res.text())["schedule"]
            
            text = "<b>📆 Today's Anime Releases Schedule</b>\n\n"
            for i in aniContent:
                aname = TextEditor(i["title"])
                await aname.load_anilist()
                text += f''' <a href="https://subsplease.org/shows/{i['page']}">{aname.adata.get('title', {}).get('english') or i['title']}</a>\n    • <b>Time</b> : {i["time"]} hrs\n\n'''
            
            sch_list = text + "<b>⏰ Current TimeZone :</b> <code>IST (UTC +5:30)</code>"
            TD_SCHR = await bot.send_message(Var.MAIN_CHANNEL, sch_list)
            await (await TD_SCHR.delete())
        except Exception as e:
            # Handle the exception (e.g., log it)
            print(f"An error occurred: {e}")
