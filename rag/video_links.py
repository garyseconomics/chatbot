from pathlib import Path

from config import settings


# Get the list of youtube videos from the context
def get_video_link(context):
    if not context:
        return []
    videos_list = []
    for doc in context:
        file_source = doc.metadata["source"]
        # Takes the video id from the name of the file
        video_id = Path(file_source).stem.split(settings.video_ids_separator)[0]
        video_url = "https://www.youtube.com/watch?v=" + video_id
        if video_url not in videos_list:
            videos_list.append(video_url)
    return videos_list


# Get the list of videos and returns a text for the chatbots
def videos_text_for_chat(video_links):
    if not video_links:
        return ""
    if len(video_links) == 1:
        videos_text = f"More information on this video: {video_links[0]}"
    else:
        videos_text = "More information on this videos:\n"
        for video in video_links:
            videos_text += video + "\n"
    return videos_text
