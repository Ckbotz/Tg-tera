import requests
import aria2p
from datetime import datetime
from status import format_progress_bar
import asyncio
import os, time
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)
options = {
    "max-tries": "50",
    "retry-wait": "3",
    "continue": "true"
}

aria2.set_global_options(options)


async def download_video(url, reply_msg, user_mention, user_id):
    encoded_url = requests.utils.quote(url, safe='')
    api_url = f"http://terabox.silentxbotz.tech/api/download?url={encoded_url}&token=TERAXBOTZ"

    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        await reply_msg.edit_text("Failed to fetch video info from API.")
        return None, None, None

    video_info = data["data"][0]
    hd_download_link = video_info["link"]
    thumbnail_url = video_info["thumb"]
    video_title = video_info["filename"]

    try:
        download = aria2.add_uris([hd_download_link])
        start_time = datetime.now()

        while not download.is_complete:
            download.update()
            percentage = download.progress
            done = download.completed_length
            total_size = download.total_length
            speed = download.download_speed
            eta = download.eta
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()
            progress_text = format_progress_bar(
                filename=video_title,
                percentage=percentage,
                done=done,
                total_size=total_size,
                status="Downloading",
                eta=eta,
                speed=speed,
                elapsed=elapsed_time_seconds,
                user_mention=user_mention,
                user_id=user_id,
                aria2p_gid=download.gid
            )
            await reply_msg.edit_text(progress_text)
            await asyncio.sleep(2)

        if download.is_complete:
            file_path = download.files[0].path

            thumbnail_path = "thumbnail.jpg"
            thumbnail_response = requests.get(thumbnail_url)
            with open(thumbnail_path, "wb") as thumb_file:
                thumb_file.write(thumbnail_response.content)

            await reply_msg.edit_text("ᴜᴘʟᴏᴀᴅɪɴɢ...")

            return file_path, thumbnail_path, video_title

    except Exception as e:
        logging.error(f"Error handling download: {e}")
        buttons = [
            [InlineKeyboardButton("🚀 Download", url=hd_download_link)],
            [InlineKeyboardButton('ᴍᴏʀᴇ ᴠɪᴅᴇᴏꜱ', switch_inline_query_current_chat='')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await reply_msg.reply_text(
            "Download failed. You can download manually using the button below.",
            reply_markup=reply_markup
        )
        return None, None, None

# async def download_video(url, reply_msg, user_mention, user_id):
#     response = requests.get(f"https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}")
#     response.raise_for_status()
#     data = response.json()

#     resolutions = data["response"][0]["resolutions"]
#     fast_download_link = resolutions["Fast Download"]
#     hd_download_link = resolutions["HD Video"]
#     thumbnail_url = data["response"][0]["thumbnail"]
#     video_title = data["response"][0]["title"]

#     download = aria2.add_uris([fast_download_link])
#     start_time = datetime.now()

#     while not download.is_complete:
#         download.update()
#         percentage = download.progress
#         done = download.completed_length
#         total_size = download.total_length
#         speed = download.download_speed
#         eta = download.eta
#         elapsed_time_seconds = (datetime.now() - start_time).total_seconds()
#         progress_text = format_progress_bar(
#             filename=video_title,
#             percentage=percentage,
#             done=done,
#             total_size=total_size,
#             status="Downloading",
#             eta=eta,
#             speed=speed,
#             elapsed=elapsed_time_seconds,
#             user_mention=user_mention,
#             user_id=user_id,
#             aria2p_gid=download.gid
#         )
#         await reply_msg.edit_text(progress_text)
#         await asyncio.sleep(2)

#     if download.is_complete:
#         file_path = download.files[0].path

#         thumbnail_path = "thumbnail.jpg"
#         thumbnail_response = requests.get(thumbnail_url)
#         with open(thumbnail_path, "wb") as thumb_file:
#             thumb_file.write(thumbnail_response.content)

#         await reply_msg.edit_text("ᴜᴘʟᴏᴀᴅɪɴɢ...")

#         return file_path, thumbnail_path, video_title
#     else:
#         return markup


async def upload_video(client, file_path, thumbnail_path, video_title, reply_msg, collection_channel_id, user_mention, user_id, message):
    file_size = os.path.getsize(file_path)
    uploaded = 0
    start_time = datetime.now()
    last_update_time = time.time()

    async def progress(current, total):
        nonlocal uploaded, last_update_time
        uploaded = current
        percentage = (current / total) * 100
        elapsed_time_seconds = (datetime.now() - start_time).total_seconds()
        
        if time.time() - last_update_time > 2:
            progress_text = format_progress_bar(
                filename=video_title,
                percentage=percentage,
                done=current,
                total_size=total,
                status="Uploading",
                eta=(total - current) / (current / elapsed_time_seconds) if current > 0 else 0,
                speed=current / elapsed_time_seconds if current > 0 else 0,
                elapsed=elapsed_time_seconds,
                user_mention=user_mention,
                user_id=user_id,
                aria2p_gid=""
            )
            try:
                await reply_msg.edit_text(progress_text)
                last_update_time = time.time()
            except Exception as e:
                logging.warning(f"Error updating progress message: {e}")

    with open(file_path, 'rb') as file:
        collection_message = await client.send_video(
    chat_id=collection_channel_id,
    video=file,
    caption=f"✨ {video_title}\n👤 ʟᴇᴇᴄʜᴇᴅ ʙʏ : {user_mention}\n📥 ᴜsᴇʀ ʟɪɴᴋ: tg://user?id={user_id}",
    thumb=thumbnail_path,
    progress=progress,
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴍᴏʀᴇ ᴠɪᴅᴇᴏꜱ", switch_inline_query_current_chat="text")]
    ])
        )
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=collection_channel_id,
            message_id=collection_message.id
        )
        await asyncio.sleep(1)
        await message.delete()

    await reply_msg.delete()
    sticker_message = await message.reply_sticker("CAACAgUAAxkBAAEM-DFnDocHxzzdxA3pGXrVH98mvH-u7QAClxMAAj3xcVS7F_0jw0cQTjYE")
    os.remove(file_path)
    os.remove(thumbnail_path)
    await asyncio.sleep(5)
    await sticker_message.delete()
    return collection_message.id
