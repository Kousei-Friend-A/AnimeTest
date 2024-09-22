from re import findall 
from math import floor
from time import time
from os import path as ospath
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, rename as aiorename
from shlex import split as ssplit
from asyncio import sleep as asleep, gather, create_subprocess_shell, create_task
from asyncio.subprocess import PIPE

from bot import Var, bot_loop, ffpids_cache, LOGS
from .func_utils import mediainfo, convertBytes, convertTime, sendMessage, editMessage
from .reporter import rep

ffargs = {
    '1080': Var.FFCODE_1080,
    '720': Var.FFCODE_720,
    '480': Var.FFCODE_480,
    '360': Var.FFCODE_360,
}

class FFEncoder:
    def __init__(self, name, total_time, qual, dl_path, out_path):
        self.__name = name
        self.__total_time = total_time
        self.__qual = qual
        self.dl_path = dl_path
        self.out_path = out_path
        self.__proc = None
        self.is_cancelled = False
        self.__prog_file = "progress.txt"
    
    async def progress(self):
        while not self.is_cancelled:
            # Assume time_done, ensize, speed, diff are defined somewhere
            percent = round((time_done / self.__total_time) * 100, 2)
            tsize = ensize / max(percent / 100, 0.01)
            eta = (tsize - ensize) / max(speed, 0.01)

            # Create the progress bar
            filled_blocks = floor(percent / 8) * "●"
            empty_blocks = (12 - floor(percent / 8)) * "○"
            bar = filled_blocks + empty_blocks

            progress_str = f"""<blockquote>📌 <b>Anime Name :</b> <b><i>{self.__name}</i></b></blockquote>
<blockquote>🔄 <b>Status :</b> <i>Encoding</i>
    <code>[{bar}]</code> {percent}%</blockquote> 
<blockquote>📚 <b>Size :</b> {convertBytes(ensize)} out of ~ {convertBytes(tsize)}
   🚀 <b>Speed :</b> {convertBytes(speed)}/s
   ⏱ <b>Time Took :</b> {convertTime(diff)}
   ⏳ <b>Time Left :</b> {convertTime(eta)}</blockquote>
<blockquote>📂 <b>File(s) Encoded:</b> <code>{Var.QUALS.index(self.__qual)} / {len(Var.QUALS)}</code></blockquote>"""

            await editMessage(self.message, progress_str)

            # Check for progress end condition
            if (prog := findall(r"progress=(\w+)", text)) and prog[-1] == 'end':
                break

            await asleep(8)

    async def start_encode(self):
        if ospath.exists(self.__prog_file):
            await aioremove(self.__prog_file)

        async with aiopen(self.__prog_file, 'w+'):
            LOGS.info("Progress Temp Generated!")

        dl_npath = ospath.join("encode", "ffanimeadvin.mkv")
        out_npath = ospath.join("encode", "ffanimeadvout.mkv")
        await aiorename(self.dl_path, dl_npath)

        ffcode = ffargs[self.__qual].format(dl_npath, self.__prog_file, out_npath)
        LOGS.info(f'FFCode: {ffcode}')
        
        self.__proc = await create_subprocess_shell(ffcode, stdout=PIPE, stderr=PIPE)
        proc_pid = self.__proc.pid
        ffpids_cache.append(proc_pid)

        # Run progress tracking and wait for process to finish
        _, return_code = await gather(create_task(self.progress()), self.__proc.wait())
        ffpids_cache.remove(proc_pid)

        await aiorename(dl_npath, self.dl_path)

        if self.is_cancelled:
            return

        if return_code == 0:
            if ospath.exists(out_npath):
                await aiorename(out_npath, self.out_path)
            return self.out_path
        else:
            error_message = (await self.__proc.stderr.read()).decode().strip()
            await rep.report(error_message, "error")

    async def cancel_encode(self):
        self.is_cancelled = True
        if self.__proc is not None:
            try:
                self.__proc.kill()
            except Exception as e:
                LOGS.error(f"Error while trying to kill process: {e}")
